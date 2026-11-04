"""Verifier layer (owner req. 8, FR-07/16): block hallucinations at critical points.

Pure functions returning findings. `error` findings must block the pipeline
(observation stored as failed, question never delivered, record stays draft).
`warning` findings require reviewer attention but do not block capture.
"""

from __future__ import annotations

from veytac.schemas import DecisionRecord, Observation, Question


class Finding(dict):
    pass


def _err(code: str, message: str) -> Finding:
    return Finding(code=code, severity="error", message=message)


def _warn(code: str, message: str) -> Finding:
    return Finding(code=code, severity="warning", message=message)


def validate_observation(
    obs: Observation,
    *,
    capture_watermark_ms: int,
    known_asset_ids: set[str],
) -> list[Finding]:
    """Observation gate (TRD 3.4, 6.1 step 5)."""
    findings: list[Finding] = []
    if not obs.description.strip():
        findings.append(_err("OBS_EMPTY", "observation has no description"))
    if obs.window_end_ms > capture_watermark_ms:
        findings.append(
            _err(
                "OBS_FUTURE",
                f"window ends at {obs.window_end_ms}ms but capture watermark "
                f"is {capture_watermark_ms}ms: no evidence beyond live capture",
            )
        )
    for ref in obs.evidence_refs:
        if ref.asset_id not in known_asset_ids:
            findings.append(
                _err("OBS_UNKNOWN_ASSET", f"references nonexistent asset {ref.asset_id}")
            )
            continue
        loc = ref.locator
        if loc.start_ms is not None and loc.end_ms is not None:
            if loc.end_ms > capture_watermark_ms:
                findings.append(
                    _err(
                        "OBS_FUTURE_SPAN",
                        f"evidence span ends at {loc.end_ms}ms beyond watermark",
                    )
                )
    if obs.candidate_action and not obs.evidence_refs:
        findings.append(
            _warn("OBS_ACTION_UNGROUNDED", "candidate action has no evidence refs")
        )
    return findings


def validate_question(
    q: Question, *, open_gap_ids: set[str], asked_gap_ids: set[str]
) -> list[Finding]:
    """Question gate: grounded in a real open uncertainty (TRD 6.2)."""
    findings: list[Finding] = []
    if not q.wording.strip():
        findings.append(_err("Q_EMPTY", "question has no wording"))
    if q.gap_id not in open_gap_ids:
        findings.append(
            _err("Q_NO_GAP", f"gap {q.gap_id} is not an open recorded gap")
        )
    if q.gap_id in asked_gap_ids:
        findings.append(_warn("Q_REDUNDANT", f"gap {q.gap_id} was already asked"))
    lowered = q.wording.lower()
    if "why did you" in lowered and "did" not in lowered.replace("why did you", ""):
        findings.append(
            _warn(
                "Q_PRESUPPOSES_ACTION",
                "verify the action happened before asking why (TRD 6.2)",
            )
        )
    return findings


def validate_decision_for_review(
    rec: DecisionRecord, *, known_asset_ids: set[str]
) -> list[Finding]:
    """Pre-review gate: attribution, evidence, and honesty checks."""
    findings: list[Finding] = []
    if not rec.expert_original_statement.strip():
        findings.append(_err("REC_NO_STATEMENT", "original expert statement missing"))
    for cue in rec.cues:
        if cue.origin == "measured":
            if not cue.evidence_refs:
                findings.append(
                    _err("REC_MEASURE_UNGROUNDED", f"measured cue '{cue.description}' lacks evidence")
                )
            if not cue.unit and any(
                ch.isdigit() for ch in (cue.value or "")
            ):
                findings.append(
                    _warn("REC_MEASURE_NO_UNIT", f"numeric cue '{cue.description}' lacks units")
                )
        for ref in cue.evidence_refs:
            if ref.asset_id not in known_asset_ids:
                findings.append(
                    _err("REC_UNKNOWN_ASSET", f"cue references unknown asset {ref.asset_id}")
                )
    if rec.alternatives and not rec.applicability.scope_description.strip():
        findings.append(
            _warn("REC_NO_SCOPE", "alternatives listed but applicability scope is empty")
        )
    return findings


def blocks(findings: list[Finding]) -> bool:
    return any(f["severity"] == "error" for f in findings)
