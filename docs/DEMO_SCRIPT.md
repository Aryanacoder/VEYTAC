# VEYTAC — Demo Storyboard and Claim Checklist

This is a **demo plan**, not proof that every live-provider integration has passed. The default fallback must be labeled as a **recorded or mock-mode replay**, never portrayed as fresh live AI.

## Story in ~150 seconds

**0:00–0:18 — The problem:** Show a skilled person making a choice while working. Say: *“The camera captured the action. It did not capture the reason.”* Avoid dramatic accident claims without evidence.

**0:18–0:40 — Live capture:** Use a phone or screen on an authorized, safe task. Show the real camera feed, capture status, microphone permission, and visible objects or events. Capture, model processing, and training permissions are separate.

**0:40–1:15 — The question that matters:** The apprentice proposes a question based on an actual unknown in the observed task. An expert approves delivery, answers in their own language, and can correct the AI's interpretation. Preserve the exact timestamp and original answer. Never let an AI-generated “expert” reply stand in for a human.

**1:15–1:40 — Knowledge becomes data:** Show the draft decision, its source clip, applicability conditions, alternatives, exceptions, and review status. Explicitly approve it. Distinguish observed fact from expert report and model inference.

**1:40–2:00 — Skill package:** Open the lesson and downloadable observation/decision bundle. Show the actual schema, source references, checksums, rights and missing sensor fields. Do not describe a phone-only ZIP as robot-ready training.

**2:00–2:20 — The transfer test:** Ideally demonstrate a new case that the original passive-video baseline cannot resolve but the reviewed context can. If no verified experiment exists, state the hypothesis and show the harness **without** claiming measured improvement.

**2:20–2:30 — The company vision:** “A smartphone today; synchronized industrial cameras, sensors and robot telemetry tomorrow. The same apprenticeship layer can preserve expert judgment for future workers and machines.”

## Hard acceptance gates before recording a live demo

- [ ] Live phone recording works through trusted HTTPS, with usable mic and speaker.
- [ ] Meta observation and question calls succeed on this exact task; failures are visible.
- [ ] A question is grounded in a real uncertainty, not a canned generic prompt.
- [ ] The expert answers; the complete original-language answer is persisted.
- [ ] A reviewed decision is linked to the correct recording interval.
- [ ] The final episode/lesson and private export can be reopened and validated.
- [ ] Model receipts/cost are checked; no secrets or private raw recordings are accidentally displayed.
- [ ] Unsupported claims about robot training, simulations, safety, market traction, or performance are excluded.

## If one gate fails

Show the last **accurately labeled recorded run**, explain what was observed, and identify the remaining blocker. Do not silently switch a simulated session to “live” or claim model training results that are not backed by runs.

## Useful links

- [Implementation status](IMPLEMENTATION_STATUS.md)
- [Dataset quality checklist](DEMO_DATASET_CHECKLIST.md)
- [Acceptance tests](../ACCEPTANCE_TESTS.md)
- [Learning evaluation](../LEARNING_AND_ROBOT_EVALUATION.md)
