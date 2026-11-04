# VEYTAC — Goals, implementation plan, and agent work allocation

Version: 0.1.0 • Prepared 2026-10-30 • All work below starts as **NOT VERIFIED**

## 1. North-star goal

**Preserve expert judgment in a form that another person or machine can use on a new situation.**

The phone, marketplace, illustrations, and model-training jobs serve that goal. Do not optimize for the number of integrations, amount of generated video, or apparent complexity of the dashboard.

### The complete end state we are pursuing

An expert demonstrates a task; VEYTAC notices a consequential information gap; the expert answers a relevant question; the system preserves a reviewed, scoped decision record linked to evidence; a lesson and valid dataset are produced; a held-out task tests whether the knowledge transfers. Where action-aligned data and compute are available, an actual robot policy is trained and evaluated using the added context.

The aim is a complete chain of evidence, not a promise that every research experiment will show an improvement.

## 2. Goal hierarchy

| Goal | Required outcome | Completion evidence |
|---|---|---|
| G-01 Accessible acquisition | Phone capture and screen/upload alternative with explicit permissions. | Real-device run, timestamps, interruptions, and consent tests. |
| G-02 Active expertise capture | At least one useful, non-scripted question grounded in an actual observed gap. | Recording, selected question, answer, and independent relevance review. |
| G-03 Faithful reusable knowledge | Reviewed conditions, alternatives, exceptions, and outcome checks with source links. | Validated SkillEpisode, correction history, and negative tests. |
| G-04 Immediate transfer | Approved knowledge used appropriately on an unseen case. | Frozen baseline/enriched comparison; failures and abstentions included. |
| G-05 Human learning | Evidence-linked lesson and decision checkpoint, not an unsupported procedure. | Reviewer inspection and source/version validation. |
| G-06 Dataset quality | Loadable, rights-aware exports; no invented physical actions/measurements. | Quality report, round-trip load, rejected-invalid-export evidence. |
| G-07 Robot-learning investigation | Genuine action/state data, BC baseline, bounded RL comparison, fixed evaluation. | Actual run artifacts or explicit blocked status; no exporter-only success claim. |
| G-08 Open, controlled sharing | Public code and contributor-approved dataset release/catalog. | Repository audit, rights manifest, publication and isolation tests. |
| G-09 Production-minded demo | Budget, failure states, recovery, privacy, and audit trail. | Acceptance suite, real-provider smoke, resource cleanup, rehearsal. |

## 3. Owner preparation checklist

Prepare these before asking coding agents to build elaborate integrations.

### A. Expert and task

- Select a consenting expert and a safe demonstration containing a genuine conditional decision.
- Agree on the task objective and identify what the camera can and cannot observe.
- Prepare at least two contrasting cases and a basic outcome check without handing the test answers to the agent.
- Obtain recording, external-processing, training, and publication permissions separately as applicable.
- Do not use Nakakita/client documents without specific authorization. An expert can review a self-authored clean-room example instead.
- Arrange a nonhazardous fallback demonstration or labeled recording. Do not claim factory access until confirmed.

### B. Hardware and capture

- Phone with microphone/camera, charger, stable mount or a separate observer, and tested connectivity.
- Laptop for backend/review, microphone/speaker checks, HTTPS access tested on the actual phone.
- A short synchronization test with an observable audible/visual event.
- Work area without unauthorized people, screens, credentials, or confidential equipment labels in frame.

### C. Accounts and budget

- Confirm Meta credits are actually present; identify which account pays Muse Code usage.
- Store server keys outside Git; Standard mode by default.
- Treat Baseten/Fireworks/Modal approval as unconfirmed until verified in each account.
- Establish a daily manual check of account spend; the app cannot control independent terminal spending.
- Authorize each paid experiment by bounded purpose, data, duration, and maximum spend.

### D. Public source material

- Select small, permitted recordings, diagrams, and robotics trajectories with explicit source/version metadata.
- Validate decoding and annotation relevance before downloading large archives.
- Do not invent an expert explanation for a recording whose demonstrator is unavailable.
- Keep data access/rights blockers visible; do not copy restricted assets into the public repository.

## 4. Seven logical implementation milestones

These milestones are an ordering, not a claim that seven calendar days remain. The official deadline is November 4, 2026, 21:00 Eastern / November 5, 11:00 Japan time [S01]. Inspect current time and compress the plan accordingly. Keep final time for rehearsal and verification.

### M0 — Establish reality before scaffolding

**Goal:** resolve the minimum dependencies that determine whether the demo is possible.

Tasks:
1. Inspect the existing repository; record actual files/branch and preserve new work.
2. Verify the expert/task and permissions or record the fallback requiring owner approval.
3. Decode one real permitted video; inspect its timestamps and content.
4. Make explicitly approved, bounded smoke calls for text/structured output, video or images, and transcription. Test SAM separately if available.
5. Check the actual phone's HTTPS camera/mic access and MIME support.
6. Inspect one public robot trajectory and its license/environment metadata; no training yet.
7. Create a capability matrix: available, denied, unsupported, untested; record actual model names and billing mode.

**Artifacts:** environment report, source registry entries, task brief, account capability report, decision log.

**Exit:** a lawful capture path, a usable Meta inference path, and a non-fictional task exist. A missing partner GPU is not a core blocker. An unavailable model is not an excuse to fabricate output.

### M1 — Contracts, invariants, and mocks

**Goal:** create the deterministic foundation before a polished frontend.

Tasks:
1. Implement canonical schemas, generated types, migrations, and event contracts.
2. Add consent, role, state-machine, revision, source-reference, and publication logic.
3. Implement cost reservations and external coding-spend records.
4. Create mock provider adapters and small permitted/synthetic fixtures with labels.
5. Implement unit tests for invalid references, fabricated robot data, duplicate events, stale approvals, and budget concurrency.

**Artifacts:** schemas, OpenAPI, mock server, passing deterministic tests, initial CLI `doctor`.

**Exit:** no schema or state-machine ambiguity prevents parallel development. Tests cannot be skipped because the UI looks correct.

### M2 — Real capture-to-question vertical slice

**Goal:** phone → evidence → Meta → one relevant question → actual human answer.

Tasks:
1. Implement permissioned camera/audio acquisition, chunk acknowledgments, still-frame observation, and source clocks.
2. Add the backend ASR relay with finalized turns, original-language text, and typed fallback.
3. Implement structured observations and gap/question proposals.
4. Add question-window permission, deferral, stop, cooldown, and one-question-at-a-time handling.
5. Run a real phone session and a network interruption test.

**Artifacts:** recorded session, source manifests, real-provider call logs, latency breakdown, answer linkage.

**Exit:** at least one grounded question is genuinely generated and answered. The system does not merely play a script or label prerecorded data live.

### M3 — Review and persistent expertise

**Goal:** turn dialogue into a faithful reusable skill record.

Tasks:
1. Build evidence cards and decision draft generation.
2. Support corrections, exceptions, conflicts, approval, and supersession.
3. Preserve original speech/transcript, not only a polished summary.
4. Retrieve approved applicable rules on a new case; unknown conditions trigger clarification.
5. Implement deterministic quality checks and canonical private export.

**Artifacts:** approved episode, quality report, source-linked revision history, first held-out decision test.

**Exit:** correcting a rule changes later behavior and invalidates dependent stale artifacts. Expert approval is not presented as physical measurement or universal truth.

### M4 — Human lesson and controlled sharing

**Goal:** make the knowledge usable and shareable without turning the core into a marketplace build.

Tasks:
1. Generate an evidence-linked lesson with a decision checkpoint and a contrasting case where available.
2. Build export preview, dataset card, private catalog draft, and explicit publication flow.
3. Confirm release manifests do not expose private originals or unauthorized assets.
4. Demonstrate a second-domain imported/replayed task using configuration, not a new application.
5. Add an optional approved diagram; defer elaborate 3D if the acquisition loop needs work.

**Artifacts:** lesson, sanitized release, catalog preview, permissions tests.

**Exit:** a reviewer can trace lesson content to approved evidence and a contributor can keep a session private.

### M5 — Learning and evaluation workstream

**Goal:** test the central claims rather than merely showing model activity.

Tasks:
1. Freeze held-out task cases and comparison budgets.
2. Run passive, fixed-question, and active-question conditions.
3. Load genuine robot trajectories in a pinned environment and reproduce an episode.
4. Annotate a small subset of the same task/trajectories with expert context; preserve attribution and missingness.
5. Run compact BC baseline/enriched comparison; run bounded IQL only after reward/termination checks.
6. Produce actual reports with seeds, trajectories, failures, and costs.
7. If supported and funded, run a narrow Glimmer SFT baseline/tuned comparison.

**Artifacts:** manifests, split hashes, reviewed annotations, checkpoints, metrics, report, failure log.

**Exit:** knowledge-transfer evaluation is complete for the core. Robot-learning work has a truthful status and artifacts; “blocked” is not “passed.” A negative result is acceptable evidence but does not support an improvement claim.

**Scope protection:** M5 runs alongside stabilization when possible; it does not justify breaking a working live product to add untested training infrastructure.

### M6 — Release, rehearsal, and submission

**Goal:** a defensible demonstration and a reproducible public repository.

Tasks:
1. Run the acceptance suite and real-provider/device smoke tests.
2. Reconcile spend, disable idle cloud resources, and protect demo reserve.
3. Test a clean checkout and verify no keys, restricted recordings, or fabricated results are committed.
4. Rehearse live and disclosed-replay fallback paths.
5. Freeze the claim inventory and attach evidence links.
6. Record actual limitations, incomplete research goals, and hackathon contributions.

**Artifacts:** release checklist, report index, demo recording, source/license manifest, final commit/tag.

**Exit:** no critical failure, no misleading demonstration, and every public performance claim has a corresponding result.

## 5. Parallel work for Codex and Muse Code

Assign by task ownership, not assumptions about which model is better.

| Work lane | Suggested owner | Boundaries |
|---|---|---|
| Shared contracts, migrations, budget and permissions | Codex | Own `schemas/`, state machines, database, and deterministic tests until M1 freeze. |
| Capture/review frontend, Meta provider integration | Muse Code | Own `apps/web/` and provider adapters; consume frozen contracts, propose changes explicitly. |
| Robot/SFT experiment harness | Whichever agent is free after M2 | Isolated branch/environment; no automatic paid launches. |
| Adversarial review and test expansion | The other agent | Review the implementation against fixed criteria; do not weaken the criteria. |
| Requirements, expert labels, permissions, spend | Aryan | Human approval cannot be delegated to an LLM pretending to be the expert. |

Use separate branches/worktrees. Do not let both agents edit the same schema, lockfile, or migration simultaneously. One integrator merges small reviewed changes. Before switching lanes, write a handoff with changed files, commands run, actual results, unresolved issues, and expected next tests.

A shared `docs/IMPLEMENTATION_STATUS.md` should track milestone state and evidence, but a claimed completion without logs is not sufficient. Agents must not mark tests passed because a previous agent said they were.

## 6. Resource strategy

Core paid calls are selective: bounded frames/clips, approved questions, cached replays, and limited escalation. Mocks serve development and regression tests. Reprocessing an identical artifact with the same prompt/schema/model should reuse cached results when permissions and version scope remain valid.

Partner credit roles, after approval:
- Baseten: compatible open-model serving or a bounded training job.
- Fireworks: eligible Glimmer LoRA SFT plus explicitly budgeted evaluation/inference.
- Modal: short preprocessing or robotics training/evaluation jobs.

Do not deploy the same model on three services merely to use every credit. Actual need and measured cost determine placement.

## 7. Cut order if time runs short

Cut, in order: paid marketplace features; fancy Anatomy/3D visuals; extra languages beyond tested English/Japanese; a third domain; local large-model serving; nonessential source connectors; large training sweeps.

Never cut: provenance, explicit expert review, permission boundaries, honest missing fields, held-out evaluation, or rejection of invented robot data.

A training job can be documented as blocked. The acquisition system cannot be replaced with hand-authored answers while retaining the live-learning claim.

## 8. Decision gates

- **No real task or permission:** owner approves a safe alternative; do not fabricate factory access.
- **Vision insufficient:** improve capture, ask clarifying questions, or reduce the supported visual event class; do not silently supply event ground truth.
- **Expert context adds no value:** retain result and narrow the claim. Do not move test cases into training until success appears.
- **Robot replay fails:** fix compatibility or document a different selected task before training; no animation-only success.
- **Budget unknown:** block nonessential spending until reconciled.
- **Conflicting expert explanations:** preserve both and obtain scoped review; do not invent consensus.

## 9. Final acceptance statement

The goal is not “the app runs.” The goal is:

> A real expert provides information the observation did not establish; VEYTAC preserves it faithfully and with permission; the resulting record is usable for a lesson and a valid dataset; a controlled evaluation reveals whether that information changes later performance.

That result, plus a clear path to richer instrumented and robot-learning deployments, is the hackathon's substantive proof of the startup vision.

<!-- Primary source reference links; design requirements above remain proposed. -->
[S01]: https://dev.meta.ai/events/global-hackathon
