"""SAM 3.1 segmentation provider (TRD 7.5) via the Meta Responses API.

Contract (Meta media-segmentation + SAM docs, S-series):
- ``POST {base}/responses`` with ``{"model": "sam-3.1", "input": [...],
  "stream": true}``. Server key only, Bearer header, never the browser.
- Prompt (``input_text``): ONE concept noun phrase per request (a comma
  list matches nothing), or box/point prompts in the token grammar, never
  both. Concept lists are refused client-side to avoid a paid zero-match.
- Media (``input_image``): data URL or hosted URL.
- The stream carries one ``output_text`` lane: one line per frame,
  ``<Nf>id<|box;...|><|mask;...|>,...``. Object ids are stable within a
  response; empty output = zero matches (valid, not an error).
- Mask decode uses the official ``meta_sam_parser`` package when it is
  installed (declared dependency). Without it, mask payloads are stored
  opaque and boxes/ids still work — never a fake decode.

``include_confidence`` / ``metadata.mask_encoding`` follow the docs and
are re-verified on the first live run; a provider rejection is stored,
never hidden.
"""

from __future__ import annotations

import json
import os
import re
import time

import httpx

RESPONSES_PATH = "/responses"
DEFAULT_MODEL = "sam-3.1"
DEFAULT_TIMEOUT_S = 60
RATE_CARD_VERSION = "meta-2026-11-04"  # placeholder; recompute from first bill


class SamError(Exception):
    def __init__(self, message: str, *, transient: bool = False) -> None:
        super().__init__(message)
        self.transient = transient


class SamConfig:
    def __init__(self) -> None:
        self.base_url = os.getenv("VEYTAC_META_BASE_URL", "https://api.meta.ai/v1").rstrip("/")
        self.api_key = os.getenv("VEYTAC_META_API_KEY", "")
        self.model = os.getenv("VEYTAC_MODEL_SEGMENTATION", DEFAULT_MODEL)
        self.paid_calls_allowed = os.getenv("VEYTAC_ALLOW_PAID_CALLS", "false") == "true"

    def require_ready(self) -> None:
        if not self.api_key:
            raise SamError("VEYTAC_META_API_KEY is not set", transient=False)
        if not self.paid_calls_allowed:
            raise SamError("paid calls are disabled (VEYTAC_ALLOW_PAID_CALLS)", transient=False)


def estimate_sam_micro(objects: int) -> int:
    """Conservative placeholder per event-frame call (TRD 13.2 step 2)."""
    return 2000 + objects * 500


_LIST_LIKE = re.compile(r"[,;]|(\band\b)|\n")


def build_concept_text(concept: str) -> str:
    """One short noun phrase. Lists match nothing, so refuse them unpaid."""
    text = " ".join(concept.strip().split())
    if not text:
        raise SamError("empty concept prompt", transient=False)
    if _LIST_LIKE.search(text):
        raise SamError(
            f"concept {text!r} looks like a list; SAM matches one concept "
            "per request, lists return zero matches", transient=False)
    return text


def _int(v: object, what: str) -> int:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or int(v) != v or v < 0:
        raise SamError(f"{what} must be a non-negative integer pixel value", transient=False)
    return int(v)


def build_box_prompt(size: tuple[int, int], objects: list[dict]) -> str:
    """Token grammar for box prompts: ``<0f>id<|box;...|>,...``.

    ``objects``: [{id, x1, y1, x2, y2}] in source pixels, x2/y2 inclusive.
    Mirrors the documented truck example exactly.
    """
    w, h = size
    if not objects:
        raise SamError("at least one prompted object is required", transient=False)
    if w <= 0 or h <= 0:
        raise SamError(f"invalid frame size {size!r}", transient=False)
    seen: set[str] = set()
    parts: list[str] = []
    for o in objects:
        oid = str(o.get("id"))
        if not oid.isdigit():
            raise SamError(f"object id {o.get('id')!r} must be a non-negative integer", transient=False)
        if oid in seen:
            raise SamError(f"duplicate object id {oid}", transient=False)
        seen.add(oid)
        x1, y1, x2, y2 = (_int(o.get(k), f"box.{k}") for k in ("x1", "y1", "x2", "y2"))
        if not (x1 <= x2 < w and y1 <= y2 < h and (x2 > x1 or y2 > y1)):
            raise SamError(f"box [{x1},{y1},{x2},{y2}] outside {w}x{h} or empty", transient=False)
        parts.append(
            f"{oid}<|box;x1={x1};y1={y1};x2={x2};y2={y2};w={w};h={h}|>")
    return f"<0f>{','.join(parts)}"


_HEADER = re.compile(r"^<([0-9]+)f>")
_RECORD = re.compile(r",?([0-9]+)(?=<\|)")
_TOKEN = re.compile(r"<\|([A-Za-z][A-Za-z0-9_.-]*)(?:;([^|]*))?\|>")
_INT_FIELDS = re.compile(r"([a-z0-9]+)=(-?[0-9]+(?:\.[0-9]+)?)")


def _fields(body: str | None) -> dict:
    out: dict = {}
    for m in _INT_FIELDS.finditer(body or ""):
        v = m.group(2)
        out[m.group(1)] = float(v) if "." in v else int(v)
    return out


_MASK_DATA = re.compile(r"([0-9]+),([0-9]+),([!~][^|]+)")


def parse_output_line(line: str) -> list[dict]:
    """Parse one ``<Nf>...`` line into records (documented ABNF)."""
    m = _HEADER.match(line.strip())
    if not m:
        raise SamError(f"not a segmentation line: {line[:80]!r}", transient=False)
    frame = int(m.group(1))
    rest = line.strip()[m.end():]
    records: list[dict] = []
    pos = 0
    while pos < len(rest):
        rm = _RECORD.match(rest, pos)
        if not rm:
            break
        oid = int(rm.group(1))
        pos = rm.end()
        box = mask = None
        while True:
            tm = _TOKEN.match(rest, pos)
            if not tm:
                break
            pos = tm.end()
            name, body = tm.group(1), tm.group(2) or ""
            if name == "box":
                box = _fields(body)
            elif name == "mask":
                f = _fields(body)
                dm = _MASK_DATA.search(body)
                if not dm:
                    raise SamError(f"mask without data payload: {body[:60]!r}", transient=False)
                mask = {"x": 0, "y": 0, "h": int(dm.group(1)), "w": int(dm.group(2)),
                        "enc": dm.group(3)[0], "payload": dm.group(3)[1:],
                        "c": f.get("c")}
        if box is None or mask is None:
            raise SamError(f"record {oid} lacks a box+mask pair", transient=False)
        records.append({"frame": frame, "id": oid, "box": box, "mask": mask,
                        "c": box.get("c")})
    return records


def try_decode_masks(records: list[dict]) -> list[dict]:
    """Attach mask geometry via the official parser when installed.

    Returns records with ``svg``/``rle`` when decodable, else the opaque
    payload with ``decoded: False``. Never invents geometry.
    """
    try:
        from meta_sam_parser import (  # type: ignore
            SegmentationMask, decode_mask_to_rle, decode_mask_to_svg_path)
    except ImportError:
        for r in records:
            r["decoded"] = False
        return records
    for r in records:
        enc = {"~": "lossless", "!": "one_bit"}.get(r["mask"]["enc"])
        if enc is None:
            r["decoded"] = False
            continue
        try:
            mask = SegmentationMask(encoding=enc, payload=r["mask"]["payload"],  # type: ignore[arg-type]
                                    width=r["mask"]["w"], height=r["mask"]["h"])
            rle = decode_mask_to_rle(mask)
            get = (lambda k: rle[k]) if isinstance(rle, dict) else (lambda k: getattr(rle, k))
            r["rle"] = {"size": list(get("size")), "counts": list(get("counts"))}
            r["svg"] = decode_mask_to_svg_path(mask)
            r["decoded"] = True
        except Exception:
            r["decoded"] = False
    return records


class SamClient:
    """Live SAM 3.1 over the Responses SSE stream."""

    def __init__(self, config: SamConfig | None = None) -> None:
        self.config = config or SamConfig()
        self._http = httpx.Client(
            base_url=self.config.base_url,
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=DEFAULT_TIMEOUT_S,
        )

    def segment_image(self, *, image_url: str, prompt_text: str,
                      ) -> dict:
        """One image, one prompt. Returns records with boxes, ids, masks."""
        self.config.require_ready()
        started = time.time()
        body = {
            "model": self.config.model,
            "input": [{"role": "user", "content": [
                {"type": "input_text", "text": prompt_text},
                {"type": "input_image", "image_url": image_url},
            ]}],
            "stream": True,
            "metadata": {"mask_encoding": "one_bit", "include_confidence": "true"},
        }
        try:
            with self._http.stream("POST", RESPONSES_PATH, json=body) as res:
                if res.status_code in (429, 500, 502, 503):
                    raise SamError(f"transient HTTP {res.status_code}", transient=True)
                if res.status_code >= 400:
                    raise SamError(
                        f"provider HTTP {res.status_code}: {res.read().decode()[:200]}",
                        transient=False)
                text_lane: list[str] = []
                for line in res.iter_lines():
                    if not line.startswith("data:"):
                        continue
                    try:
                        evt = json.loads(line[5:].strip())
                    except ValueError:
                        continue
                    etype = str(evt.get("type", ""))
                    if "output_text.delta" in etype:
                        d = evt.get("delta", "")
                        if isinstance(d, str):
                            text_lane.append(d)
                    elif "failed" in etype or etype.endswith(".error"):
                        raise SamError(f"stream failed: {str(evt)[:200]}", transient=False)
                    elif "completed" in etype:
                        break
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            raise SamError(f"sam call failed: {exc}", transient=True) from exc
        full = "".join(text_lane)
        records: list[dict] = []
        for raw in full.splitlines():
            raw = raw.strip()
            if raw:
                records.extend(parse_output_line(raw))
        return {
            "execution_mode": "live",
            "model": self.config.model,
            "elapsed_ms": int((time.time() - started) * 1000),
            "records": try_decode_masks(records),
            "rate_card": RATE_CARD_VERSION,
        }


class MockSamClient:
    """Deterministic canned masks; labeled mock, never billed."""

    execution_mode = "mock"

    def segment_image(self, *, image_url: str, prompt_text: str) -> dict:  # noqa: ARG002
        return {
            "execution_mode": "mock",
            "model": "mock-sam-0",
            "elapsed_ms": 0,
            "records": [
                {"frame": 0, "id": 0,
                 "box": {"x1": 10, "y1": 10, "x2": 50, "y2": 50, "w": 320, "h": 240},
                 "mask": {"x": 0, "y": 0, "h": 8, "w": 8, "enc": "~", "payload": "AAAA"},
                 "c": 0.99, "decoded": False},
            ],
            "rate_card": RATE_CARD_VERSION,
        }
