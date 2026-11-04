# VEYTAC — Verification plan and claim gates

Version: 0.1.0 • Prepared 2026-10-30  
**Initial status: all application and experimental verification is NOT RUN.**

This document defines what must be demonstrated, how to evaluate it, and which claims the resulting evidence permits. It is not a report that any test passed. Detailed cases are in [Acceptance tests](verification/ACCEPTANCE_TESTS.md); learning experiments are in [Learning/robot evaluation](verification/LEARNING_AND_ROBOT_EVALUATION.md).

## 1. End goal

> A genuine expert supplies consequential context that passive observation did not establish. VEYTAC preserves that context faithfully and with permission, produces a usable reviewed skill package, and tests whether it helps a new learner or policy handle a different case.

A pleasant conversation is insufficient. A dataset-shaped ZIP is insufficient. A training loss curve is insufficient. Every stronger claim requires the corresponding additional evidence.

## 2. Evidence levels

| Level | Evidence | Permitted statement | Not established |
|---|---|---|---|
| E0 | Mock/unit tests | The specified logic behaves correctly on declared fixtures. | Live model or device integration. |
| E1 | Real provider + real device session | This integration captured and processed a real demonstration. | Broad industrial reliability. |
| E2 | Reviewed source-linked episode | An expert's reported context was preserved with stated scope. | Scientific truth or robot-control suitability. |
| E3 | Validated action-aligned export and downstream loader | The declared format and semantics passed these compatibility checks. | Better learning. |
| E4 | Controlled held-out knowledge/policy evaluation | The measured result applies to these conditions and sample sizes. | Generalization to every industry or physical deployment. |
| E5 | Physical robot/field validation | Only the actually tested system/task conditions. | Safety certification or universal autonomy. |

The hackathon targets E1/E2 and a bounded E4 study. E3 is required before a robot-policy claim. E5 is future work unless a genuine separate experiment occurs; do not invent it.

## 3. Release gates

| Gate | Required evidence | Blocking behavior |
|---|---|---|
| G0 — Reproducible foundation | Clean setup, pinned environment, schema tests, capability report, source registry. | No “works from fresh checkout” claim without actual test. |
| G1 — Rights and safety | Consent/auth/publication/deletion tests; permissions for demo material; no live actuation. | Critical failure blocks public release. |
| G2 — Real live acquisition | Phone or approved real screen capture, actual Meta processing, actual question/answer, timestamp trace. | Mock/replay does not pass live gate. |
| G3 — Faithful knowledge | Evidence references, corrections, scope/exceptions, review, supersession and conflict handling. | Fabricated answer/measurement or broken evidence lineage blocks release. |
| G4 — Usable outputs | Canonical export validates; lesson cites approved version; publication remains explicit. | A ZIP download without validation is not a pass. |
| G5 — Knowledge-transfer investigation | Fixed scenarios and baseline/enriched results with sample counts and budgets. | An anecdotal demo does not support a general improvement claim. |
| G6 — Robot-data compatibility | Genuine actions/states, metadata, loader, time checks, and replay where supported. | Phone-only data must fail action-policy export. |
| G7 — Robot-learning experiment | Actual BC baseline and context experiment; declared offline-RL run/status; artifacts and held-out outcomes. | Adapter-only or training-only result cannot be called robot improvement. |
| G8 — Submission readiness | Passing critical cases, claim inventory, budget reconciliation, clean repository, disclosed fallback. | Secrets, restricted material, or fake results block submission. |
| G9 — Optional model adaptation | Eligible SFT/RL job, data rights, checkpoint and independent comparison. | A config file or queued job is not a fine-tuned model. |

Core product release requires G0–G5 and G8. G6/G7 are the required research workstream and must be reported separately. If they are blocked, label the submission `CORE_ONLY; ROBOT_LEARNING_NOT_DEMONSTRATED` and keep that goal incomplete. Do not silently reclassify the work as done. G9 is optional and must not consume protected demo resources.

## 4. Test categories and execution rules

### 4.1 Deterministic tests

Schema/state/budget/auth/rights/export invariants run in CI without paid providers or GPUs. Use small labeled fixtures. A fixture can test logic, not real model understanding.

### 4.2 Provider contract tests

Run a bounded approved request per supported capability, recording exact endpoint/model/mode, payload type, timing, usage, and validated response. Redact keys. Unavailable capability is `BLOCKED` or `NOT_APPLICABLE` with scope adjustment, never a fabricated response.

### 4.3 Real device tests

Test at least the owner's phone/browser and one desktop browser. Verify HTTPS permissions, microphone, recording, background/interruption behavior, playback, original-language corrections, and reconnection. Record device/browser/codec versions. Do not claim support for devices not tested.

### 4.4 Human/expert evaluation

A reviewer checks evidence faithfulness and applicability. The runtime model cannot be its own sole judge. With one reviewer, disclose that limitation. Blind reviewers to condition where possible and preserve disagreements.

### 4.5 Training/evaluation tests

Run in isolated environments with immutable manifests, fixed held-out splits, and actual costs. Tests must verify that added context reaches the learning computation. A paragraph saved beside a trajectory but never used by the learner does not count.

## 5. Nonnegotiable invariants

1. Every approved decision has a valid source and attributed statement or explicitly labeled inference.
2. No live observation uses evidence beyond its current capture watermark.
3. Unknown physical quantities remain unknown; zero is not a missing-value placeholder.
4. Expert approval does not convert reported information into sensor measurement.
5. No answer is invented for silence, unavailable expertise, or a missing recording.
6. Consent for recording is not consent for training or public release.
7. A publisher approves the exact payload version; subsequent edits invalidate approval.
8. A stale or corrected rule cannot silently remain active in current lessons and inference.
9. A paid call reserves budget before dispatch; unknown billing stays conservatively accounted for.
10. Model/tool output cannot grant itself privileges, publication rights, or machinery control.
11. Mocks, simulated episodes, and replays are visibly labeled in artifacts and the demo.
12. Missing/failed/skipped evaluation is not a zero-error result.

Any violation is a critical defect regardless of how impressive the frontend looks.

## 6. Metrics and interpretation

### 6.1 Product/quality metrics

- **Evidence validity:** valid references / all exported references; required 100% for an approved release.
- **Unsupported-claim rate:** reviewer-labeled unsupported propositions / evaluated propositions. Report count and uncertainty; critical unsupported measurement/safety claims must be zero in the release sample.
- **Question usefulness:** questions whose answers resolve a relevant unknown / evaluated questions. Predeclare the rubric; expert agreement alone is insufficient.
- **Redundancy:** questions answered by already available evidence / evaluated questions.
- **Correction burden:** expert correction minutes and changed claims per session.
- **Interruption violations:** delivered worker-directed questions while permission was closed; required zero.
- **Latency:** capture-to-observation, eligible-question-to-display, and complete capture-to-question separately; include queue and network delays.
- **Cost:** provider actual/estimated/unknown usage, coding external spend, and training cost separated.

Initial targets from PRD are engineering objectives, not already achieved accuracy. Report latency tails, denominator, devices, and network.

### 6.2 Transfer metrics

Compare task correctness, condition/exception handling, inappropriate rule application, and abstention under matched observation/question/time budgets. Count abstention separately from correct action. A system that abstains on everything has not achieved useful transfer.

For an exploratory pilot, aim for at least three independently recorded/reviewed sessions per condition and twelve held-out decision cases per condition. Smaller evidence can demonstrate workflow but must be labeled case study, not reliable population-level improvement. Do not treat neighboring video frames as independent samples.

### 6.3 Robot metrics

Task success, episode return under a declared reward, recovery success if supported, constraint violations under declared thresholds, rollout length, training time, and expert annotation time. Use paired initial conditions across policies and several training seeds where feasible. Do not infer force safety if the environment does not model/report it.

A positive metric difference with insufficient samples is exploratory, not a guarantee. Negative results must remain in the final report.

## 7. Required evidence bundle

Implementation must produce a report directory such as:

```text
artifacts/verification/<run_id>/
  run_manifest.json
  environment.json
  acceptance_results.json
  provider_capabilities.json
  privacy_and_rights_review.json
  budget_report.json
  episode_quality_reports/
  transfer_results/
  robot_results/                 # Actual report or explicit blocked record
  screenshots_or_recordings/     # Only permitted material
  claim_inventory.json
  SUMMARY.md
```

These are target outputs, not files delivered by this specification pack. The bundle records repository commit, source/data hashes, configuration, seed, model/prompt/schema version, execution mode, and actual timestamps.

Example result structure:

```json
{
  "test_id": "V-KNW-04",
  "status": "NOT_RUN",
  "execution_mode": "mock",
  "requirement_ids": ["FR-13", "FR-15"],
  "started_at": null,
  "finished_at": null,
  "observed_result": null,
  "artifact_refs": [],
  "limitations": ["Specification only; test has not been implemented or executed."]
}
```

Allowed statuses: `NOT_RUN`, `PASS`, `FAIL`, `BLOCKED`, `NOT_APPLICABLE`. A nonapplicable optional feature must be absent from capability claims. A blocked required gate prevents claiming completion of that tier.

## 8. Claims audit

Before release, list each statement used in the pitch, README, UI, and demo script. Assign it a category: vision, implementation fact, measured result, or future work. Attach evidence for facts/results.

Examples:

| Statement | Evidence needed |
|---|---|
| “Asks relevant questions in Japanese.” | Actual Japanese session, reviewed transcript/question, and tested text/TTS behavior. |
| “Creates reviewed decision datasets.” | Export and source-linked human approval. |
| “Robot-compatible export.” | Declared format/version, genuine required fields, successful downstream load. |
| “Improves robot performance.” | Controlled policy comparison and held-out metrics, not only a successful animation. |
| “Learns in real time.” | Specify memory/context update; weight training requires actual training logs/checkpoints. |
| “Creates simulations.” | Actual supported simulator model/run; illustrations and replay alone do not qualify. |
| “Protects proprietary data.” | Actual storage/provider controls and permissions; do not imply an air gap with hosted inference. |

## 9. Independent review and release decision

The implementer runs tests. A second agent reviews code and negative cases where practical. Aryan or an authorized reviewer confirms data permissions and expert attribution. The owner approves spending and public release.

A model may assist with review but cannot authorize its own claims. Do not rewrite a failed criterion after observing results without labeling the subsequent evaluation exploratory and versioning the protocol.

Release decisions are `RELEASE_CORE`, `RELEASE_WITH_RESEARCH_EVIDENCE`, or `DO_NOT_RELEASE`. Both release decisions require critical P0 tests to pass. Research evidence is attached only at its demonstrated scope.
