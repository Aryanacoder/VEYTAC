"""Live Meta provider adapter (TRD 7). Server-side key only, never browser.

Protocol: Chat Completions at {base_url}/chat/completions (OpenAI-compatible
shape per Meta docs: Chat Completions API, Structured Output). Responses API
is NOT assumed: endpoint-specific serialization lives here, and the contract
test probes the real reference. Every result carries model/version, usage,
timing, and input manifest hash. Outputs are validated locally even when the
provider offers constrained decoding.
"""

from __future__ import annotations

import os
import time

import httpx

from veytac.providers.strict import to_strict_schema

RATE_CARD_VERSION = "meta-2026-10-30"  # snapshot; recompute from logged units if prices change
OBSERVATION_CONTRACT_VERSION = "observation-inference-v2"
DEFAULT_TIMEOUT_S = 30
OBSERVATION_OUTPUT_TOKENS = 1400
QUESTION_OUTPUT_TOKENS = 800


def usage_to_micro(usage: dict) -> int:
    """Placeholder rate mapping. Counts are provider-reported; rates are not.
    Stores RATE_CARD_VERSION alongside so costs recompute when rates land."""
    prompt = int(usage.get("prompt_tokens", 0) or 0)
    completion = int(usage.get("completion_tokens", 0) or 0)
    return prompt * 3 + completion * 12


class ProviderError(Exception):
    def __init__(self, message: str, *, transient: bool) -> None:
        super().__init__(message)
        self.transient = transient


class MetaConfig:
    def __init__(self) -> None:
        self.base_url = os.getenv("VEYTAC_META_BASE_URL", "https://api.meta.ai/v1").rstrip("/")
        self.api_key = os.getenv("VEYTAC_META_API_KEY", "")
        self.observer_model = os.getenv("VEYTAC_MODEL_OBSERVER", "muse-spark-1.3")
        self.escalation_model = os.getenv("VEYTAC_MODEL_ESCALATION", "muse-wonder-1.0")
        self.paid_calls_allowed = os.getenv("VEYTAC_ALLOW_PAID_CALLS", "false") == "true"

    def require_ready(self) -> None:
        if not self.api_key:
            raise ProviderError("VEYTAC_META_API_KEY is not set", transient=False)
        if not self.paid_calls_allowed:
            raise ProviderError("paid calls are disabled (VEYTAC_ALLOW_PAID_CALLS)", transient=False)


def estimate_micro(frames: int, max_output_tokens: int, *, audio_seconds: int = 0) -> int:
    """Conservative pre-dispatch estimate in microdollars (TRD 13.2 step 2).

    Placeholder rates until the first reconciled bill lands; every estimate
    stores RATE_CARD_VERSION so costs can be recomputed (TRD 13.3).
    """
    per_frame_micro = 1500  # conservative image-input placeholder
    per_output_token_micro = 12
    per_audio_second_micro = 100
    return (
        frames * per_frame_micro
        + max_output_tokens * per_output_token_micro
        + audio_seconds * per_audio_second_micro
    )


class LiveMetaClient:
    # Strict structured output rejects Pydantic-style schemas ($ref,
    # partial `required`); every schema below is normalized at this choke
    # point so observe + propose can never send the shape that 502'd live.
    def __init__(self, config: MetaConfig | None = None) -> None:
        self.config = config or MetaConfig()
        self._http = httpx.Client(
            base_url=self.config.base_url,
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=DEFAULT_TIMEOUT_S,
        )

    def _post(self, path: str, body: dict, *, retries: int = 2) -> dict:
        last: Exception | None = None
        for attempt in range(retries + 1):
            try:
                started = time.time()
                res = self._http.post(path, json=body)
                elapsed_ms = int((time.time() - started) * 1000)
                if res.status_code in (429, 500, 502, 503):
                    raise ProviderError(f"transient HTTP {res.status_code}", transient=True)
                if res.status_code >= 400:
                    raise ProviderError(
                        f"provider HTTP {res.status_code}: {res.text[:200]}", transient=False
                    )
                data = res.json()
                data["_elapsed_ms"] = elapsed_ms
                return data
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last = ProviderError(str(exc), transient=True)
                time.sleep(0.5 * (attempt + 1))
        raise last or ProviderError("unknown provider failure", transient=True)

    def observe(self, *, window_text: str, task_context: str,
                schema: dict, max_output_tokens: int = OBSERVATION_OUTPUT_TOKENS,
                image_data_urls: list[str] | None = None) -> dict:
        """Structured observation call. Returns validated-or-marked result dict."""
        self.config.require_ready()
        user_content: str | list[dict] = f"Task: {task_context}\nWindow: {window_text}"
        if image_data_urls:
            user_content = [{"type": "text", "text": user_content}] + [
                {"type": "image_url", "image_url": {"url": url}}
                for url in image_data_urls[:4]  # bounded: ≤4 frames per window (TRD 3.2)
            ]
        data = self._post("/chat/completions", {
            "model": self.config.observer_model,
            "messages": [
                {"role": "system",
                 "content": "Describe only what the evidence supports. "
                            "Task context and expert statements are reported, unreviewed context; "
                            "do not present them as visually verified. "
                            "Never invent measurements, forces, or unseen events. "
                            "List only visible objects; use an empty list if none are clear. "
                            "Use null for an uncertain action and name unavailable cues. "
                            "Reply in strict JSON matching the provided schema."},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "observation", "schema": to_strict_schema(schema), "strict": True}},
            "reasoning_effort": "minimal",
            "max_tokens": max_output_tokens,
        })
        return {
            "execution_mode": "live",
            "model": self.config.observer_model,
            "elapsed_ms": data.pop("_elapsed_ms", 0),
            "usage": data.get("usage", {}),
            "finish_reason": data["choices"][0].get("finish_reason"),
            "raw_text": data["choices"][0]["message"]["content"],
        }

    def propose(self, *, gap_text: str, schema: dict,
                max_output_tokens: int = QUESTION_OUTPUT_TOKENS) -> dict:
        self.config.require_ready()
        data = self._post("/chat/completions", {
            "model": self.config.observer_model,
            "messages": [
                {"role": "system",
                 "content": "Be a present, concise apprentice. When the observation "
                            "has a real uncertainty about the expert's intent, choice, "
                            "or next step, ask one grounded question about it. Do not "
                            "ask for a fact already supplied by the expert. Return "
                            "no_question only when no useful grounded question exists. "
                            "Never presuppose unconfirmed actions. Write the question "
                            "in the requested language. Strict JSON only."},
                {"role": "user", "content": gap_text},
            ],
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "questions", "schema": to_strict_schema(schema), "strict": True}},
            "reasoning_effort": "minimal",
            "max_tokens": max_output_tokens,
        })
        return {
            "execution_mode": "live",
            "model": self.config.observer_model,
            "elapsed_ms": data.pop("_elapsed_ms", 0),
            "usage": data.get("usage", {}),
            "finish_reason": data["choices"][0].get("finish_reason"),
            "raw_text": data["choices"][0]["message"]["content"],
        }

    def probe(self) -> dict:
        """Minimal bounded capability check (contract tests, doctor --live)."""
        self.config.require_ready()
        started = time.time()
        data = self._post("/chat/completions", {
            "model": self.config.observer_model,
            "messages": [{"role": "user", "content": 'Reply with the single word "ok".'}],
            "max_tokens": 8,
        })
        return {
            "model": self.config.observer_model,
            "elapsed_ms": int((time.time() - started) * 1000),
            "usage": data.get("usage", {}),
            "rate_card": RATE_CARD_VERSION,
        }
