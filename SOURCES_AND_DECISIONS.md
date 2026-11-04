# VEYTAC — Sources, decisions, assumptions, and unresolved dependencies

Version: 0.1.0  
Prepared: 2026-10-30  
Status: implementation specification, not a report of a working product

## 1. How to interpret this specification pack

**Founder requirements** come from the conversation and take precedence over our earlier discarded ideas. **Proposed defaults** are implementation choices made to give coding agents a concrete starting point. **Verified external capabilities** are supported by the primary sources below. **Unverified dependencies** must pass the specified integration gate before anyone claims they work.

Do not treat provider documentation as evidence that a VEYTAC integration, model result, or training job has already succeeded. No application, live capture test, fine-tune, robot policy, or industrial deployment was executed while preparing these documents.

## 2. Founder requirements preserved

| ID | Requirement or constraint | Interpretation |
|---|---|---|
| F-01 | Brand is VEYTAC; occasional voice transcriptions say Vitec/Veytac. | Use `VEYTAC` in product copy and `veytac` in code. |
| F-02 | Enter Startup track, Push the Frontier theme. | Build a reliable product slice and a measured technical experiment; do not claim winning probabilities. |
| F-03 | Preserve tacit expert judgment for future people and machines. | The company is not merely a video summarizer, marketplace, inspection checker, or CAD tool. |
| F-04 | Observe work, ask why/when/what-if questions, and capture conditions and exceptions. | Active knowledge acquisition is the defining workflow. |
| F-05 | Phone-first live demonstration; screens and future industrial sensors also matter. | Use a common episode schema with explicit modality capabilities. |
| F-06 | Multilingual expert interaction, especially English/Japanese; Mandarin is also desired. | English and Japanese are first acceptance languages; expose unsupported speech-output limitations honestly. |
| F-07 | High-quality datasets for human learning and robot/AI learning; test usefulness. | Include data validation, training interfaces, and actual evaluation work, not only a ZIP exporter. |
| F-08 | Use public datasets, diagrams, and Meta resources. | Enforce source-specific rights; public availability is not redistribution permission. |
| F-09 | Include imitation learning, fine-tuning, and RL where technically appropriate. | Distinguish live memory updates, SFT, interviewer-policy learning, and robot-policy RL. |
| F-10 | Open-source application; contributor-controlled dataset sharing/exchange. | Code openness does not make private recordings public. Marketplace is distribution, not the core thesis. |
| F-11 | $150 Meta credit envelope. | Budget the application and coding-agent use together; no approved unlimited spend. |
| F-12 | Baseten, Fireworks, and Modal credits require applications/approval. | Do not assume approved accounts or combine conditional credits into the guaranteed $150. |
| F-13 | Nakakita material may not be available or authorized. | No proprietary employer data is a prerequisite. |
| F-14 | Codex and Muse Code will implement the project. | Provide shared instructions, stable contracts, scoped work, and independent verification. |

The founder described a real engineering workflow: shipyard drawing → supplier CAD representation → SCADA graphics → signal mapping. This motivates a possible domain adapter. It is not a mandate to narrow the whole company to that workflow, nor permission to publish employer artifacts.

## 3. Read-only repository inspection

On 2026-10-30, the connected GitHub tool returned only `README.md` at the root of `Aryanacoder/VEYTAC`. Its introduction describes industrial apprenticeship infrastructure. That is a point-in-time observation; agents must inspect the repository again before editing. These files were created as a downloadable specification pack. No GitHub commits were made.

## 4. Proposed decisions, subject to explicit revision

| Decision | Default | Why / change condition |
|---|---|---|
| Architecture | React/TypeScript SPA, Python/FastAPI modular monolith, SQLite, filesystem artifacts, one worker | Small deployment and inspectable evidence; scale later based on measured load. |
| Main inference | Meta Spark; bounded Wonder escalation; dedicated ASR; selective SAM | Meaningful Meta use without running every expensive capability continuously. |
| Capture transport | Timestamped media chunks + periodic still frames + separate speech stream | Avoid assuming arbitrary recorder chunks are independent videos or that a provider accepts an endless video socket. |
| First live task | Safe, permissioned physical demonstration with a genuine decision and a known reviewer | Owner selects actual task at milestone M0. A clean-room screen demonstration is a fallback, not an invented factory visit. |
| Robot experiment | robomimic/robosuite single task, BC baseline and bounded offline IQL comparison | Reuse real action/state trajectories; pin compatible versions and establish replay first. |
| Immediate “learning” | Versioned reviewed memory | No unsupervised live weight updates or uncontrolled online industrial control. |
| SFT | Optional funded Muse Glimmer LoRA experiment after baseline and rights checks | Partner availability and measured dataset readiness are gates, not assumptions. |
| Visual lesson | Evidence-linked replay + interactive diagram first | Anatomy integration is optional; illustrative geometry is not a physics twin. |
| Sharing | Private default; approved immutable release; lightweight catalog | No payment processing or public storage bucket by default. |
| License | Recommend Apache-2.0 for newly authored code; owner confirms before adding LICENSE | Third-party data, model, and asset licenses remain separate. |

## 5. Primary technical sources

Links are included so implementation agents can re-check current contracts. Accessed 2026-10-30. The descriptions below are source summaries; the detailed system architecture elsewhere is VEYTAC's proposed design.

### S01 — Hackathon scope and judging
https://dev.meta.ai/events/global-hackathon

Startup track emphasizes technical execution and production suitability. Push the Frontier includes software, robotics, manufacturing, energy, and physical systems. The page gives November 4, 2026, 21:00 Eastern as submission deadline: November 5, 2026, 11:00 Asia/Tokyo. Verify organizer updates before submission. Do not assume seven full days remain when implementation starts.

### S02 — Meta model catalog
https://dev.meta.ai/docs/models

Documents Spark/Wonder multimodal reasoning and tool use, SAM segmentation, Voice Transcribe speech transcription, and open-weight options. Model names and supported modalities must be probed against the actual account. Provider capability is not task accuracy.

### S03 — Meta video input
https://dev.meta.ai/docs/video-understanding

Documents uploaded/referenced video analysis. VEYTAC implements near-live orchestration over bounded inputs; these docs do not establish our capture latency or a general continuous-video endpoint.

### S04 — Meta speech transcription
https://dev.meta.ai/docs/speech-to-text

Documents live audio and recording endpoints, language support, and speech turns. It returns turn-level rather than word-level timestamps and does not supply acoustic-event detection or speech synthesis. Follow the actual handshake and event ordering; do not fabricate unavailable confidence or timestamp fields.

### S05 — Meta structured output
https://dev.meta.ai/docs/structured-output

Documents JSON-schema-constrained output. Validate it again locally: schema conformity does not prove evidence support, authorization, or truth.

### S06 — Meta tool execution
https://dev.meta.ai/docs/tool-calling

Application code executes developer-defined tools. An LLM request never bypasses VEYTAC authorization, budget, safe-pause, or publication gates.

### S07 — Meta pricing and modes
https://dev.meta.ai/docs/pricing-rate-limits

At inspection, standard Spark input/output were $1.25/$4.25 per million tokens; Wonder $4/$20. Voice transcription was $0.18/hour; SAM video $0.20/1,000 frames with a 50-frame minimum per request, and image segmentation $2.50/1,000 images. Contributor mode permits provider training use; use Standard mode by default. Rates are snapshots, not promises. Reconcile billed usage and re-check before jobs.

### S08 — Muse Code installation and operation
https://dev.meta.ai/docs/muse-code

Documents `muse`, interactive use, `muse exec`, authentication, and sandboxed approvals. Runtime app credentials are separate from an interactive coding-agent session.

### S09 — Muse Code project guidance
https://dev.meta.ai/docs/muse-code/configuration

Documents `AGENTS.md`, `muse init`, and launch flags. Do not run `muse init --force` over this pack's instructions. Confirm installed-build flags with `--help` before use.

### S10 — Codex repository guidance
https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex

Official OpenAI guidance describes durable project instructions and goal-oriented workflows. `AGENTS.md` in this pack is shared developer guidance, not an instruction to replace Meta inference in the product.

### S11 — Muse Glimmer post-training
https://dev.meta.ai/docs/muse-glimmer/post-training

Distinguishes supervised training from reward-based methods and stresses a measurable baseline. No inference here that the founder's credits cover unrestricted training.

### S12 — Fireworks Glimmer recipe
https://docs.fireworks.ai/fine-tuning/training-api/cookbook/muse-glimmer

Documents a Glimmer LoRA SFT recipe and a time-limited promotional offer. Check eligibility and exact billable components in the account. Do not assume RL, deployment, or evaluation sampling is free.

### S13 — Baseten training
https://docs.baseten.co/training

Documents training and supported-model workflows. Treat proposed serving/training use as conditional on account access, compatibility, and an approved estimate.

### S14 — Modal compute
https://modal.com/docs/guide/gpu

Documents GPU functions and configuration. VEYTAC must impose explicit job duration, concurrency, and budget limits; an adapter file is not evidence that a job ran.

### S15 — Ego-Exo4D expert commentary
https://docs.ego-exo4d-data.org/annotations/expert_commentary/

Contains expert commentary tied to skilled demonstrations, including why and quality judgments. Useful for annotation research; it is not a complete answer oracle for arbitrary real-time questions. Follow separate dataset access and license requirements.

### S16 — IndustReal
https://github.com/TimSchoonbeek/IndustReal

Provides assembly/maintenance research recordings, annotations, geometries, and baselines. The assembly setting is industrial-like, not a production factory. Inspect the actual archive, licensing, and relevant sequences before selecting a subset.

### S17 — REASSEMBLE
https://github.com/TUWIEN-ASL/REASSEMBLE

Documents multimodal robotic assembly data, including state/action-related and physical sensing resources. Useful for aligning observations with measured quantities; not proof of any VEYTAC robot-learning improvement.

### S18 — LeRobot dataset format
https://huggingface.co/docs/lerobot/en/lerobot-dataset-v3

Documents video and time-series dataset organization. Export through a pinned library version and round-trip load the result. A phone-only episode must not receive fabricated robot actions merely to fit a schema.

### S19 — robomimic algorithms
https://robomimic.github.io/docs/introduction/implemented_algorithms.html

Provides behavior-cloning and offline-learning implementations. Our default research comparison is BC followed by IQL, not a newly invented RL implementation.

### S20 — robomimic demonstrations
https://robomimic.github.io/docs/datasets/robomimic_v0.1.html

Documents demonstrations and observation variants. Environment/controller versions and replay compatibility are mandatory checks before annotation or training.

### S21 — robosuite environments
https://robosuite.ai/docs/modules/environments.html

Documents simulation task interfaces. Select one compatible task; a simulation result is not a physical deployment result.

### S22 — Anatomy
https://github.com/wheresryan22/anatomy

An agent skill for interactive explanatory illustrations, not a robotics dataset or validated physical solver. Pin, inspect, and license-check before integrating. Never execute generated HTML or scripts unsandboxed.

### S23 — Browser recording timing
https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/dataavailable_event

Recorder timing can vary, especially across device interruptions. Preserve actual timestamps and media presentation timestamps rather than deriving time from the number of chunks.

### S24 — Browser media permission
https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia

Camera/microphone access requires appropriate permission and secure contexts. Phone-on-LAN HTTP must not be assumed to work like desktop localhost.

## 6. Unresolved dependencies and required handling

1. Actual expert, safe task, and recording permissions: owner selects at M0; no fictional factory access.
2. Dataset download success and content rights: verify small subsets before announcing integration.
3. Provider access, quota, and billing mode: a single approved smoke call per capability; log model/version.
4. Partner credit approval: unknown until account evidence is available; core flow remains local/Meta-hosted.
5. English/Japanese recognition on relevant terms and optional TTS voice availability: test actual devices; permit typed corrections.
6. Robot simulator and dataset compatibility: prove one recorded episode replay before training.
7. Robot-context benefit: unknown until controlled evaluation; negative results must be retained.
8. “EarSound 3.0.2”: exact identity remains unresolved. Do not install a guessed package.
9. Nakakita artifacts: not authorized by this specification. Use a permitted alternative.
10. Generated lesson/Anatomy runtime: optional and isolated. A simple replay lesson is the required fallback.

## 7. Change-control rule

When a proposed default is changed, record the reason, affected requirement IDs, test IDs, cost effect, and owner approval where needed. Do not silently redefine “robot ready,” “live,” “expert approved,” or “verified” to make the demo pass. Revised implementation choices are allowed; unsupported claims are not.
