"""Strict schema transform tests: reproduce the live 502, then prove the fix.

The provider rejected our schemas with HTTP 400:
"'required' is required to be supplied and to be an array including every
key in properties." These tests audit the RAW Pydantic schemas (must
fail) and the transformed ones (must pass) for both live call shapes
(observe + propose). No network, no key.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from veytac.providers.strict import audit_strict, to_strict_schema  # noqa: E402
from veytac.schemas import Observation, ObservationInference, Question  # noqa: E402


def test_raw_observation_schema_violates_strict_shape():
    problems = audit_strict(Observation.model_json_schema())
    assert any("required must list every property key" in p for p in problems)
    assert any("unresolved $ref/$defs" in p for p in problems)


def test_raw_question_schema_violates_strict_shape():
    problems = audit_strict(Question.model_json_schema())
    assert problems, "expected the raw Question schema to violate strict shape"


def test_transformed_observation_schema_is_strict_compliant():
    strict = to_strict_schema(Observation.model_json_schema())
    assert audit_strict(strict) == []
    assert strict["type"] == "object"
    assert set(strict["required"]) == set(strict["properties"].keys())
    # every nested object complies too, e.g. evidence locator
    assert strict["additionalProperties"] is False


def test_transformed_question_schema_is_strict_compliant():
    strict = to_strict_schema(Question.model_json_schema())
    assert audit_strict(strict) == []


def test_optional_fields_become_required_nullable_not_dropped():
    strict = to_strict_schema(ObservationInference.model_json_schema())
    assert "candidate_action" in strict["required"]
    cand = strict["properties"]["candidate_action"]
    assert cand.get("anyOf") or cand.get("type") is not None


def test_live_observation_schema_contains_only_provider_claims():
    strict = to_strict_schema(ObservationInference.model_json_schema())
    assert audit_strict(strict) == []
    assert set(strict["properties"]) == {
        "description", "objects", "candidate_action", "uncertainty", "unavailable_cues"
    }
    assert "id" not in strict["properties"]
    assert "evidence_refs" not in strict["properties"]


def test_meta_request_serializes_the_strict_inference_contract(monkeypatch):
    """Exercise the real client serializer with an in-process HTTP transport."""
    import json

    import httpx

    from veytac.providers.meta import (
        LiveMetaClient, MetaConfig, OBSERVATION_OUTPUT_TOKENS,
        QUESTION_OUTPUT_TOKENS,
    )

    monkeypatch.setenv("VEYTAC_META_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("VEYTAC_ALLOW_PAID_CALLS", "true")
    config = MetaConfig()
    seen = []
    request_options = []

    def answer(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        shape = body["response_format"]["json_schema"]["schema"]
        seen.append(shape)
        request_options.append((body["reasoning_effort"], body["max_tokens"]))
        return httpx.Response(200, json={
            "choices": [{"message": {"content": json.dumps({
                "description": "A visible wrench is held.", "objects": ["wrench"],
                "candidate_action": None, "uncertainty": "Tool choice reason is unseen.",
                "unavailable_cues": [],
            })}}], "usage": {},
        })

    client = LiveMetaClient(config)
    client._http.close()
    client._http = httpx.Client(base_url=config.base_url, transport=httpx.MockTransport(answer))
    client.observe(window_text="synthetic", task_context="synthetic",
                   schema=ObservationInference.model_json_schema())
    assert len(seen) == 1
    assert audit_strict(seen[0]) == []
    assert "id" not in seen[0]["properties"]
    assert request_options == [("minimal", OBSERVATION_OUTPUT_TOKENS)]

    client.propose(gap_text="synthetic gap", schema={
        "type": "object", "properties": {"no_question": {"type": "boolean"}},
        "required": ["no_question"],
    })
    assert request_options[-1] == ("minimal", QUESTION_OUTPUT_TOKENS)


def test_bad_input_rejected():
    import pytest

    with pytest.raises(ValueError):
        to_strict_schema({"$ref": "https://external.example/s.json"})  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        to_strict_schema([])  # type: ignore[arg-type]
