"""Question gating and ranking (TRD 6.2-6.3). Pure functions, fully testable."""

from __future__ import annotations

from veytac.schemas import Question, rank_score


def delivery_allowed(
    *,
    questions_allowed: bool,
    outstanding: int,
    now_ms: int,
    window_expires_ms: int | None,
    last_delivered_ms: int | None,
    cooldown_s: int = 45,
    delivered_this_session: int = 0,
    max_per_10min: int = 5,
) -> tuple[bool, str]:
    """Safe-pause gate. Returns (allowed, reason). No model involvement."""
    if not questions_allowed:
        return False, "question window not enabled by human"
    if window_expires_ms is not None and now_ms > window_expires_ms:
        return False, "question window expired"
    if outstanding > 0:
        return False, "one outstanding question already"
    if last_delivered_ms is not None and now_ms - last_delivered_ms < cooldown_s * 1000:
        return False, "cooldown active"
    if delivered_this_session >= max_per_10min:
        return False, "session question cap reached"
    return True, "gate passed"


def pick_question(
    candidates: list[Question],
    *,
    task_relevance: dict[str, float],
    divergence: dict[str, float],
    consequence: dict[str, float],
    novelty: dict[str, float],
    burden: dict[str, float],
    asked_gap_ids: set[str],
) -> Question | None:
    """Rank bounded candidates, deduplicate by gap. Returns None = no_question."""
    best: Question | None = None
    best_score = float("-inf")
    for q in candidates:
        if q.gap_id in asked_gap_ids:
            continue
        def get(scores: dict[str, float]) -> float:
            return scores.get(q.id, 0.5)
        score = rank_score(
            get(task_relevance), get(divergence), get(consequence),
            get(novelty), get(burden),
        )
        if score > best_score:
            best, best_score = q, score
    if best is not None:
        best.rank_score = best_score
        best.rank_reason = f"heuristic score {best_score:.3f} (unCalibrated)"
    return best
