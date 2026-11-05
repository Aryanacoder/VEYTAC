# VEYTAC — Long-term Vision

## Expertise should be infrastructure, not a disappearing resource

Experienced people carry knowledge that is hard to copy: when to stop a machine, which signal is relevant, why a wiring pattern is chosen, when a drawing detail is safe to simplify, and when the usual procedure does not fit the situation.

Their actions can be recorded. Their judgment is often missing from the recording.

Manufacturing, construction, shipping, data centers, energy systems, software engineering, and many other fields face the same transfer problem. As technology becomes more automated, both new human workers and intelligent machines need access to more than polished how-to videos. They need **the conditions, alternatives, exceptions, and evidence behind decisions**.

**VEYTAC's ambition is to build the world's most useful open infrastructure for acquiring and transferring practical expert judgment.**

## The missing layer between video and intelligence

A conventional demonstration typically gives us:

- A video or screen recording.
- An approximate sequence of observable actions.
- Sometimes a transcript, task label, or successful outcome.

But it often does not tell us:

- What condition made the expert change plans.
- What they knew from experience but did not articulate.
- Which alternative they rejected and why.
- Whether they relied on a hidden measurement, feel, sound, or previous experience.
- When the same action would be inappropriate.
- Which inspection or test actually validated the result.

**VEYTAC aims to acquire those missing facts while an expert is still available.** The AI apprentice observes, identifies consequential uncertainty, asks one grounded question at a worker-approved moment, preserves the answer in the original language, and allows the expert to correct the model's interpretation.

The result is a versioned, evidence-linked **decision episode**. It is not an unreviewed summary and not a claim that every spoken explanation is physically verified.

## The long-term system

**1. Universal observation.** Start with an ordinary smartphone, screen share and microphone. Expand to industrial cameras, PLC/SCADA logs, tactile sensors, robot states/actions, CAD edits, and other synchronized measurements.

**2. Active knowledge acquisition.** Use multimodal models to identify a consequential decision or missing cause. Ask about conditions, rejected alternatives, exceptions, and outcome checks. Do not infer what a camera could not measure.

**3. Evidence-grade knowledge records.** Store time-indexed observations, original speech, source documents, expert claims, corrections, applicability boundaries, rights, and known unknowns.

**4. Transfer and evaluation.** Turn approved knowledge into interactive lessons and machine-usable research data. Test whether adaptive questioning improves handling of held-out tasks compared with passive recording and generic questions.

**5. Contribution network.** Let workers, retired experts, organizations and researchers publish or privately share **permissioned** datasets. Support attribution, discoverability, license controls, and quality labels. The future marketplace is a distribution mechanism, not a claim that all expertise must be made public.

**6. Robotics and physical AI.** Where actual synchronized robot states, actions, calibration and outcomes exist, associate decision context with those trajectories and evaluate its contribution to policy training. Rich sensors may enable closer models of physical behavior. **A phone video alone cannot provide missing forces or robot joint actions.**

## Why this matters for robots

Robot systems can learn from demonstrations and simulation. But a trajectory often tells a learner **what action occurred**, not the operational cue or exception that motivated it.

For example, two experts might stop a fitting operation at the same visual moment for very different reasons. A useful dataset should distinguish a visible pause from a reported tactile cue, a measured force peak, and a confirmed repair outcome. Conflating them creates low-quality labels.

The VEYTAC thesis is that **decision-context annotations—when genuinely aligned with the task and evaluated—can become an additional learning signal** for task understanding, high-level policies, recovery behaviors, and future robot training.

This is a research hypothesis. It is not yet a demonstrated general improvement in robot performance.

## The startup wedge and expansion

Start with a reproducible core workflow and a narrow set of expert demonstrations, where reviewers can confirm that a question exposed a distinction that video alone did not.

From there:

| Horizon | Product capability | Evidence required |
| --- | --- | --- |
| Prototype | Phone/screen capture; meaningful follow-up; reviewed episode; lesson | Consent, successful live session, traceable evidence |
| First product | Private team capture, permissions, search, versioned knowledge, evaluation | Reduced errors or expert time on a specified workflow |
| Research platform | Skill datasets with annotations, quality reports, curated releases, baseline training | Held-out transfer and controlled model/policy experiments |
| Industrial deployment | Multi-camera and industrial sensor synchronization | Calibration, validated modality alignment, deployment reliability |
| Ecosystem | Contributor-controlled dataset discovery, licensing and compensation | Demonstrated useful demand, trustworthy rights and payout workflows |

The product can support **human apprenticeship**, **engineering agents**, and **robotic learning** without pretending those three destinations have identical data requirements.

## The frontier question

**Can an AI systematically ask experts the smallest set of questions needed to turn an ordinary demonstration into knowledge that transfers to a new situation?**

That is more interesting than “can an LLM describe a factory video?”

The research comparison is explicit:

- Passive video or screen capture.
- Capture plus fixed/generic questions.
- VEYTAC's observation-grounded, adaptive questions.

Match expert time and model budgets. Use unseen tasks and real outcomes, not model-self-scored confidence. Publish failures, abstentions and uncertainty separately from successful transfers.

## What we refuse to claim

- We have not learned arbitrary industrial skills or shipped universal autonomy.
- A dataset package is not a verified physical simulation.
- A recorded expert explanation is not an independent sensor measurement.
- Phone-only recordings are not LeRobot-compatible action-policy trajectories unless genuine actions and states are aligned and validated.
- “Live memory updates” are not reinforcement learning. Fine-tuning and RL require separate training/evaluation evidence.
- The public repository does not authorize publication or third-party processing of customer data.

## North star

> **Every skill deserves to be understood, not just recorded.**
>
> The next generation of engineers and machines should be able to build on the judgment humans have already earned—without depending on that knowledge surviving by accident.
