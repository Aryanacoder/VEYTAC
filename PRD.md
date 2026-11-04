# VEYTAC — Product Requirements Document

**Version:** 0.1.0  
**Status:** implementation specification; no product or evaluation result is implied  
**Track:** Startup  
**Theme:** Push the Frontier  
**Owner:** Aryan Kumar  
**Repository:** `Aryanacoder/VEYTAC`  
**Prepared:** 2026-10-30  
**Companions:** [TRD](TRD.md), [Goals](GOALS.md), [Verification](VERIFICATION.md), [Sources/decisions](docs/SOURCES_AND_DECISIONS.md)

## 1. Product thesis

### 1.1 The company we are building

VEYTAC is **industrial apprenticeship infrastructure**: an AI apprentice that learns alongside experts so their judgment can be preserved and reused by future workers, engineers, AI agents, and robots.

Practical expertise includes more than visible motion or a final artifact. An experienced person interprets conditions, notices cues, chooses between alternatives, recognizes exceptions, and checks an outcome. A video may show the chosen action while leaving its determining context unstated. A drawing may show the result while omitting the rationale behind simplification or arrangement.

VEYTAC acquires this context while an expert is available. It connects observations and answers to a reviewed, versioned skill record, and tests whether the acquired knowledge helps on a different situation.

**Company promise:** make expertise easier to preserve, inspect, and transfer across generations and organizations.

**Hackathon proof:** a useful question uncovers context absent from passive observation; that context becomes traceable data; a new learner or system uses it correctly on an unseen case.

### 1.2 Do not misinterpret the vision

The phone application is an accessible entry point, not the whole company. Industrial cameras and sensors are future input modalities. Dataset exports, interactive lessons, simulations, and model-training examples are outputs. The marketplace is a contributor-controlled distribution channel. None is the core mission by itself.

Do not turn this project into only:
- a generic chatbot over videos;
- a manufacturing checklist or defect detector;
- a CAD-to-SCADA converter;
- a dataset hosting clone;
- a generated 3D animation;
- or a claim that narrated phone footage is already a complete robot-control dataset.

The system must remain useful across task families while demonstrating one complete, measurable acquisition loop first.

### 1.3 Product description

> VEYTAC observes expert work through a phone, screen, and optional data streams. It asks context-specific questions at appropriate moments, preserves the conditions and reasons behind decisions, and turns reviewed knowledge into reusable datasets and interactive lessons for people and machines.

## 2. Problem and source grounding

### 2.1 Problem statement

Critical decisions in skilled work are not fully represented in procedures, final drawings, or passive recordings. New workers and automation developers must repeatedly recover information that experienced people already know. The difficulty is not only storing more video; it is identifying what the recording does not explain and obtaining that information without overwhelming the expert.

The founder's engineering interviews describe drawing simplification, repeated CAD/SCADA representation, signal mapping, interface configuration, and responses to changing operating conditions. They motivate the opportunity but do not establish quantified time savings or validated customer demand.

The existence of expert commentary in Ego-Exo4D supports the distinction between recording actions and recording why/how well they are performed. It does not establish VEYTAC's effectiveness. See sources S15–S17 in [Sources](docs/SOURCES_AND_DECISIONS.md).

### 2.2 Product hypotheses to test

| Hypothesis | Required evidence | What would weaken it |
|---|---|---|
| Adaptive questions recover useful context missing from passive video. | Reviewed missing-context labels and controlled questioning comparison. | Questions merely repeat narration or lead the expert to an answer. |
| Reviewed context improves transfer to new situations. | Held-out cases with fixed expert-approved criteria. | No improvement over a fixed interview at equal expert time. |
| Experts tolerate the interaction. | Question burden, correction effort, and deferral observations. | Too many interruptions or substantial cleanup per episode. |
| The records are useful to downstream training systems. | Loadable exports and a documented training experiment. | Only transcripts are produced, or annotations never enter the learner. |
| A common acquisition core serves multiple tasks. | Primary live task plus separately labeled second-domain replay/import. | Every new task requires rewriting the application. |

These are research/business hypotheses, not existing results.

## 3. Users, jobs, and incentives

### 3.1 Expert contributor

A technician, engineer, experienced operator, skilled worker, or retired specialist demonstrates a task or reviews an authorized recording.

**Job:** explain consequential judgment once, correct the AI's interpretation, and control where the resulting knowledge goes.

**Needs:** low interruption, native-language expression, precise attribution, ability to disagree, private capture, and no implication of employee scoring.

### 3.2 Knowledge reviewer / quality lead

An authorized reviewer assesses whether the proposed records faithfully represent the demonstration and whether their conditions and limitations are clear.

**Job:** approve a version for a defined use without confusing expert opinion with independently validated engineering truth.

**Needs:** original evidence, change history, applicability boundaries, rejected claims, and permission controls.

### 3.3 Learner / next-generation worker

A less experienced person studies the recorded task and encounters decision-point exercises.

**Job:** learn when and why to use an approach, not merely memorize a sequence of motions.

**Needs:** evidence-linked explanations, contrasting cases, original language plus translation, and explicit unsupported situations.

### 3.4 AI/robotics developer

A developer imports permissioned observations and annotations into training or evaluation.

**Job:** determine whether a dataset contains the modalities and alignment required for a particular learning task.

**Needs:** schema versions, units, action meanings, timestamps, source licenses, missing-field indicators, splits, quality reports, and reproducible evaluation.

### 3.5 Organization administrator / dataset consumer

An administrator controls capture permissions, provider processing, publication, retention, and costs. A consumer browses approved releases.

**Job:** make expertise usable without accidentally exposing employer/customer information.

A single founder may fill several roles in the prototype. Role distinctions must still exist in the data and authorization checks.

## 4. Scope and delivery tiers

### 4.1 Core release, P0

The core release must provide the whole product loop:

1. Set task context and separate recording/provider-processing permissions.
2. Capture phone camera/audio live; support desktop screen capture or recorded-file ingestion.
3. Synchronize evidence and maintain a visible near-live timeline.
4. Use Meta inference to observe relevant changes and propose questions about missing context.
5. Ask only at an explicitly allowed pause; support original-language speech and typed fallback.
6. Review interpretations, conditions, alternatives, exceptions, and verification methods.
7. Reuse approved knowledge on a new case without rewriting model weights.
8. Export a validated skill episode and generate an evidence-linked lesson.
9. Preview a catalog listing and publish only after a separate authorization action.
10. Run fixed acceptance tests and a small held-out transfer evaluation.
11. Implement measured budget, error, access, and deletion handling.

### 4.2 Required research workstream, P1

The product's robot-learning thesis must not be reduced to an untested export claim. Implement:

- a registry and rights checks for public data;
- action/state alignment validation;
- a loadable robotics-compatible export for a dataset that actually has those fields;
- an executable BC training/evaluation configuration;
- a bounded offline IQL comparison when replay, reward, compute, and data checks pass;
- a report containing actual runs, failures, or explicit blocking reasons;
- an optional funded Glimmer SFT experiment after a baseline and reviewed examples exist.

P1 is a required workstream, not permission to fabricate completion. If compute or data is unavailable, the core may be released with `ROBOT_LEARNING_NOT_DEMONSTRATED`; the full research goal remains incomplete. No capability claim may hide that distinction.

### 4.3 Extensions, P2

Optional after the core gates: richer sensor ingest, a validated instrumented task, local model serving, Anatomy-based illustrations, a dedicated acoustic-event model, additional languages with tested output, multi-organization operations, actual licensing/payment flows, and sophisticated simulation assets.

### 4.4 Explicit non-goals for this event

- Universal autonomous industrial operation or authority to control live machinery.
- Medical diagnosis/advice, political fact-checking, war-related applications, or worker surveillance.
- Inferring unobserved forces, material properties, torque, or robot actions as measured truth.
- Reconstructing a validated physical digital twin from arbitrary video.
- Full foundation-model pretraining, continual live weight updates, or online exploration on factory robots.
- Full CAD authoring, naval design, ballast automation, or SCADA deployment.
- An unrestricted web scraper or automatic republication of public videos.
- Payments, revenue-sharing accounting, verified professional credentialing, or a production SaaS compliance claim.

## 5. Demo and task selection

### 5.1 Primary task selection criteria

At M0 the owner chooses one task that is safe, recordable with permission, and contains a decision whose rationale is not obvious from the visible result. A consenting domain expert must be able to review the record and define at least one contrasting situation.

Prefer a task with:
- two plausible approaches whose suitability depends on a specific condition;
- visible references or permitted documents that anchor the question;
- a clear outcome check;
- a short interval suitable for a 3–10 minute recording;
- and no need to interrupt dangerous work.

Do not choose a task merely because it looks complicated. A prerecorded industrial clip without access to its demonstrator cannot supply that person's actual unspoken reasoning.

### 5.2 Three honest evidence modes

| Mode | What it proves | Required label |
|---|---|---|
| Live human session | Capture, interaction, review, and actual expert response. | `LIVE_CAPTURE` |
| Replay of authorized recording | Offline observation and interview/review of a historical recording. | `RECORDED_REPLAY` |
| Simulator or rendered case | Controlled state, repeatable tests, and available simulated quantities. | `SIMULATED` |

An expert reviewing a public video supplies a **reviewer's interpretation**, not the original demonstrator's mental state. Preserve that attribution.

### 5.3 Broad vision without multi-industry overclaiming

A second domain, such as a clean-room engineering-screen example, should demonstrate format portability through the same pipeline. It does not prove broad industrial generalization. Keep domain-specific term dictionaries, constraints, and validators in adapter configuration rather than contaminating the common schema.

### 5.4 Demo narrative

Show the task; surface a genuine uncertainty; ask and confirm a useful question; display the new decision record; demonstrate a counterexample or new case; preview the lesson and export; report actual validation. A live demonstration must not use prewritten answers while claiming spontaneous acquisition. A disclosed replay is an acceptable failure fallback, not a substitute for a live claim.

## 6. User journeys

### 6.1 Expert records and teaches

The expert signs in or joins a scoped session, selects a language and task, sees data-processing information, and approves capture. The recording view shows the actual source, whether uploads are current, and whether the system is in live or replay mode. The expert or observer enables a short question window at a safe pause. The AI asks one grounded question at a time. The expert answers, defers, rejects the premise, or corrects a term. The resulting claim is a draft until reviewed.

### 6.2 Reviewer creates a trusted episode

The reviewer opens an evidence timeline and a draft decision card. Each card links to its source segment and original answer. The reviewer can amend scope, remove an unsupported inference, mark a conflict, request another observation, or approve the version. A correction creates a new revision. Existing lessons and exports based on superseded knowledge become stale and cannot silently present themselves as current.

### 6.3 Learner uses a lesson

The learner watches a permitted clip, answers a question before seeing the explanation, and explores a contrasting case. The lesson cites the expert and approved revision and shows limitations. A generated diagram is marked explanatory. A trained or evaluated skill is labeled only when a linked experiment supports it.

### 6.4 Developer imports a dataset

The developer sees capture modalities and capability levels before download. A phone-only recording exports observations and expert context, not a fictitious joint-action array. A properly instrumented or public robot dataset can pass an additional action-alignment gate. All releases include a manifest, quality report, licenses, split groups, and hashes. The developer can rerun validation and training using pinned configuration.

### 6.5 Contributor publishes

An approved episode remains private. Publishing requires a separate, explicit action describing the included media, rights, and audience. The application builds a sanitized immutable release. It does not expose original storage paths or private expert identity. A contributor can delist and request removal of hosted copies; the application cannot promise erasure of copies already downloaded by others.

## 7. Functional requirements

Priority P0 means core release blocker. P1 means research/integration workstream or extension of the core that must be tracked explicitly. P2 means optional later scope. Requirement IDs are stable across documents.

| ID | Priority | Requirement and observable acceptance |
|---|---|---|
| FR-01 | P0 | Create sessions with task, owner, language, source mode, and independently recorded capture/provider-processing/sharing/training permissions. No external processing without permission. |
| FR-02 | P0 | Capture phone camera and microphone over a secure context; pause, stop, and report device/network interruptions. Never silently mark replay as live. |
| FR-03 | P0 | Accept a permitted video/audio recording and a desktop screen source. Unsupported browser capture falls back explicitly to upload, not fabricated success. |
| FR-04 | P0 | Maintain media-relative timestamps, sequence IDs, source lineage, gaps, and synchronization uncertainty. Duplicate uploads are idempotent. |
| FR-05 | P0 | Capture English and Japanese answers; retain original text, transcription corrections, and translation provenance. Typed response works when audio fails. Mandarin is P1 until tested. |
| FR-06 | P0 | Attach a small permitted document/image/diagram context package; reference exact pages/regions/lines. Uploaded instructions are untrusted task data, not system commands. |
| FR-07 | P0 | Produce source-linked observations with uncertainty; reject references to nonexistent assets or future frames. |
| FR-08 | P1 | Offer selective SAM segmentation/tracking with source-frame mapping; indicate unsupported/tiny/occluded objects rather than invent geometry. Core falls back to evidence without masks. |
| FR-09 | P0 | Represent competing interpretations and missing information explicitly; generate a question or choose not to ask. |
| FR-10 | P0 | Rank bounded candidate questions by task relevance, decision consequence, nonredundancy, and expert burden; log selection reasons as concise evidence-grounded summaries. |
| FR-11 | P0 | Ask audible questions only during an explicit human-approved question window; defer safely, respect cooldown, and stop immediately when revoked. |
| FR-12 | P0 | Link answers to the right question and source interval; allow “not what happened,” “unknown,” and “skip.” Never invent an answer for silence. |
| FR-13 | P0 | Expert review, correction, rejection, and supersession are versioned and auditable. Approval changes review status, not measurement status. |
| FR-14 | P0 | Build a typed SkillEpisode with actions, conditions, alternatives, exceptions, checks, provenance, capabilities, and missing data. |
| FR-15 | P0 | Reuse only applicable approved knowledge during a new task; recognize out-of-scope conditions and conflicts. Describe this as memory/context adaptation, not weight training. |
| FR-16 | P0 | Validate schema, evidence spans, permissions, conflicting annotations, and publication prerequisites; emit a machine-readable quality report. |
| FR-17 | P0 | Export a private reviewed episode with media manifest and checksums; distinguish reference-only external assets from redistributed media. |
| FR-18 | P1 | Export/import supported robot trajectories through a pinned format adapter; reject action-policy export when required states/actions/calibration are unavailable. |
| FR-19 | P0 | Generate an evidence-linked lesson with decision points, reviewed explanations, and a counterexample where available; no unsupported causal claims. |
| FR-20 | P2 | Create an approved explanatory diagram/Anatomy view from known content; sandbox output and label illustration versus physical simulation. |
| FR-21 | P0 | Show private catalog drafts and publish only explicitly approved sanitized release versions; listing controls never publish raw captures automatically. |
| FR-22 | P1 | Produce permissioned training manifests and run a bounded SFT experiment when funded; distinguish proposed configuration, smoke execution, and actual evaluated checkpoint. |
| FR-23 | P1 | Implement and attempt the declared robot BC/IQL evaluation after replay/data gates; report incomplete work and negative results faithfully. |
| FR-24 | P0 | Reserve estimated spend before paid calls; track actual/unknown usage, per-session ceilings, and external coding-agent usage; pause before the global budget is exhausted. |
| FR-25 | P0 | Enforce authentication, role and object authorization, private media, secret handling, and prompt-injection resistance. |
| FR-26 | P0 | Resume acknowledged capture/events after reconnect, bound queues, and preserve an inspectable failure state. |
| FR-27 | P0 | Record latency, provider/model version, prompt/schema version, cost, evidence/approval lineage, and evaluation status without leaking raw secrets into logs. |
| FR-28 | P0 | Provide deterministic mocks and injectable provider adapters; mock output is always visibly labeled and never counts as live integration evidence. |
| FR-29 | P0 | Supply public code, setup instructions, source/asset manifest, contribution history, and reproducible test commands; no employer data or keys in Git. |
| FR-30 | P0 | Run a held-out transfer test comparing passive observation, fixed questions, and adaptive questions under comparable budgets. Report results, not guaranteed improvement. |
| FR-31 | P0 | Support stop, consent withdrawal, delisting, and deletion workflow with immediate access revocation and traceable artifact removal status. |
| FR-32 | P0 | Register source-specific license/use restrictions and dataset split groups before ingestion, training, or redistribution. |
| FR-33 | P0 | Keep task vocabulary, relevant decision fields, validators, and approved lesson assets in domain configuration, not hard-coded global industrial assumptions. |

## 8. Interface requirements

### 8.1 Session setup

Show task title, source mode, preferred language, organization/context label, evidence rights, privacy mode, provider processing, anticipated cost, and capture-device check. Explain that no industrial control action is performed. Record non-goal acknowledgment without presenting it as liability waiver or safety certification.

### 8.2 Live apprentice view

The primary screen contains source preview, connection/recording state, elapsed time, current question, answer transcript, and compact evidence cards. Prominent controls: pause capture, stop, allow questions, defer, correct transcript, and mark unclear. A question window never opens solely because a model infers the worker is idle.

Budget and lag indicators remain visible. Stale analysis must not appear as a current observation. Desktop reviewers may inspect detailed events; the phone view prioritizes a few large controls.

### 8.3 Review workspace

Three columns or tabs: synchronized evidence, decision records, and quality/permissions. Each record includes the original statement and a readable proposed interpretation. Approve, edit, reject, conflict, and supersede actions are explicit. Editing an approved item requires a new version and reapproval of dependent publication artifacts.

### 8.4 Dataset preview

Show capability badges: observations; expert context; measured action alignment; embodiment-specific validation. Show missing fields beside badges. Display units and observation/action rates only when known. Never display “robot ready” as a generic score.

### 8.5 Lesson and exchange views

Lessons display original evidence, decision checkpoints, and source-linked explanations. Catalog cards show dataset scope, language, review state, modalities, licenses, limitations, and download preview. Publishing is a separate screen with an artifact inventory. Payment buttons are out of scope; do not imply a transaction was completed.

## 9. Quality and nonfunctional targets

All numerical values below are initial engineering targets, not measured achievements. Tests must report actual results and environment.

| ID | Target | Interpretation |
|---|---|---|
| NFR-01 | One concurrent live capture, two authenticated review clients | Constrain demo scale before making throughput claims. |
| NFR-02 | 10-minute normal session; configurable hard cap at 15 minutes | Prevent accidental unbounded recording/inference during development. |
| NFR-03 | p95 observation-to-rendered-question ≤12 s on the rehearsed network when questions are allowed | Measure capture/upload/inference/render times separately; human wait time is not hidden. |
| NFR-04 | Session status/acknowledged metadata p95 ≤1 s locally | No promise of remote cloud latency. |
| NFR-05 | Normal reconnect ≤10 s after network restoration; duplicates produce no duplicate questions or charges | Correctness outranks seamless animation. |
| NFR-06 | Valid approved export has zero broken evidence references and zero fabricated measured fields | Deterministic release invariant. |
| NFR-07 | Controlled capture A/V alignment target ≤250 ms with uncertainty recorded | Robot trajectories require a task-specific tighter, declared tolerance; this target is not sufficient for all robotics. |
| NFR-08 | At most five autonomous questions per ten-minute session by default | User-requested elaboration is tracked separately; expert can reduce the cap. |
| NFR-09 | Default question cooldown 45 s, one outstanding question | Adjustable by task; changes logged. |
| NFR-10 | API keys never reach the browser, export, or committed files | Test with canary values and secret scan. |
| NFR-11 | End-to-end evidence trace preserved through edits and exports | Deletion removes personal content while retaining minimal non-content audit facts as permitted. |
| NFR-12 | No release says “verified robot improvement” without an evaluated artifact | Report labels are enforced, not marketing discretion. |

## 10. Success metrics and scientific claims

### 10.1 Product success

A contributor completes a real session; a useful question obtains missing context; reviewed records cite source intervals; an export loads and validates; a learner accesses a corresponding lesson; and publication remains controlled.

Track completion rate, synchronization failures, expert correction time, useful-question rate, redundant-question rate, source-reference completeness, export validity, and actual spend. Define denominators. Do not convert a single successful demo into an industry accuracy claim.

### 10.2 Knowledge-transfer success

Use the protocol in [Learning evaluation](verification/LEARNING_AND_ROBOT_EVALUATION.md). Predeclare scenarios, expected distinctions, controls, and limits. Preserve corrections and negative results. A positive result must be compared at equivalent observation and expert-time budgets.

### 10.3 Robot-learning success

Dataset compatibility, training execution, simulated policy performance, and real-world performance are separate claims. A schema-compatible file does not prove useful learning. A trained checkpoint does not prove improvement. Simulation improvement does not establish real-machine safety or transfer.

### 10.4 Startup success hypothesis

The initial commercial proposition is private capture and reuse of high-value expertise, plus integrations and validation. Potential benefits are faster handover, better onboarding, and richer learning data. Pricing, market size, cost reduction, and customer demand remain unvalidated. Gather reviewer feedback during the build; do not invent testimonials.

## 11. Learning scope and terminology

**Immediate adaptation:** reviewed contextual memory used in a later decision.

**SFT:** a separate training job updates parameters from reviewed examples. Report base model, data split, rights, training configuration, and held-out comparison.

**Interviewer RL:** a later or bounded experiment optimizes question selection using an objective downstream outcome and attention cost. Agreement from the expert or an unvalidated LLM score alone is not a sufficient reward.

**Robot imitation/RL:** uses genuine observation/action trajectories and declared reward/termination semantics. For the hackathon, use one simulator task and a compact policy; do not train a general industrial foundation model.

These distinctions must appear in the UI and pitch where relevant. Do not describe the live interaction as continual neural training when weights remain unchanged.

## 12. Budget and schedule

Confirmed planning envelope: **$150 Meta credits**. Proposed allocation: $45 coding, $40 live application development, $35 evaluation/rehearsal, $30 protected demo reserve. Conditional partner budgets are separate and zero until verified. The allocation is not a spending guarantee.

Use seven logical milestones, not a claim that seven calendar days remain. The documented deadline is November 4 at 21:00 Eastern / November 5 at 11:00 Japan time [S01]. Compress or parallelize implementation based on actual time. Freeze optional features before submission, not the evidence or security checks.

## 13. Risks and mitigations

| Risk | Product response |
|---|---|
| No authorized factory or expert access | Owner-approved safe bench task or clean-room screen task, labeled accurately; no fictional industry deployment. |
| Model misses subtle movements or hidden cues | Ask clarification, expose uncertainty, prefer visible larger events; do not infer measurements. |
| Expert cannot articulate a reason | Preserve “not established”; collect outcome checks or contrasting cases without forcing a rationale. |
| Expert explanations conflict | Scope and retain both; reviewer adjudicates; no silent majority truth. |
| Agent overgeneralizes a local rule | Explicit applicability fields, counterexamples, held-out tests, and abstention. |
| Data rights restrict hosting/training | Reference-only manifest or exclude from the use; verify each use independently. |
| Budget exhausted | Continue local capture/review, disable paid processing, expose backlog; preserve demo reserve. |
| Partner credits unavailable | Core loop works on Meta/local resources; research status remains honestly blocked if necessary. |
| Robot context shows no benefit | Publish negative result and limited claim; do not tune against the test set until a gain appears. |
| Marketplace distracts from core | Keep publishing, catalog, preview, and download only; no billing system. |

## 14. Definition of done

Core product completion requires every P0 requirement and critical acceptance test, one real-provider capture/review/export journey, an inspectable lesson, a permissions-safe catalog preview, and an actual held-out transfer report. Mocks alone do not satisfy integration gates.

Research completion additionally requires the supported robot data to load, the declared training/evaluation jobs to run, and an actual report at the supported claim level. A blocked job is not a pass. SFT or RL improvement may be negative; the requirement is honest execution and analysis, not manufactured success.

The broad vision remains intact even when a given advanced experiment is incomplete. The public submission must clearly separate what works today, what was measured, and what remains future work.

<!-- Primary source reference links; design requirements above remain proposed. -->
[S01]: https://dev.meta.ai/events/global-hackathon
