# VEYTAC — Dataset quality, knowledge transfer, SFT, and robot evaluation

Version: 0.1.0 • All experiment statuses begin **PLANNED / NOT RUN**

This file is the experiment contract. Implementing it is distinct from obtaining a positive result. The product needs evidence that active acquisition creates usable information; it must not assume that more explanation automatically improves every model.

## 1. Questions we are testing

**Q1 — Acquisition:** Do observation-grounded questions recover useful context that passive recording misses?

**Q2 — Transfer:** Does the reviewed context improve decisions on new situations at an acceptable expert-time cost?

**Q3 — Dataset correctness:** Are observations, annotations, actions, permissions, and provenance represented faithfully enough for a supported consumer to use?

**Q4 — Robot learning:** On one declared simulator task, does the added reviewed context help a policy compared with the same demonstrations without that context?

**Q5 — Adaptation:** Does a targeted fine-tune improve question selection or record extraction over its base model under the same evaluation?

These are separate experiments. A successful Q1/Q2 interview does not answer Q4. A Q4 result on public robotic trajectories does not prove transfer from an unrelated factory phone recording.

## 2. Evidence and rights prerequisites

Before any training:
1. Record source versions, hashes, owners, and permitted processing/training/redistribution uses.
2. Decode the selected media and inspect actual annotations; do not infer content from a README.
3. Obtain consent for new expert commentary and its intended uses.
4. Identify original demonstrator versus retrospective reviewer.
5. Freeze source grouping, held-out sets, and relevant outcome criteria.
6. Confirm that the model receives only information available in the evaluated setting.
7. Obtain a budget/resource approval for any paid run.

Store a manifest even for a very small pilot. Proprietary employer data is not required and must not be introduced without authorization. Public recordings may be processed locally without being eligible for republication; enforce that distinction.

## 3. Study A — Active knowledge acquisition

### 3.1 Unit of analysis and task selection

A unit is an expert decision episode with a meaningful condition and a subsequent transfer case. Adjacent video frames are not independent participants or trials.

Choose a task whose correct response can depend on context not fully established by the visible action. Obtain approved expected distinctions and counterexamples before evaluation. Use at least one real consenting demonstrator. Synthetic episodes may test plumbing but are reported separately.

Freeze a scenario manifest containing task ID, session family, equipment/version, observable inputs, hidden evaluator facts, expected scope, and review rubric. The runtime agent must not access evaluator-only facts.

### 3.2 Conditions

| Arm | Available material | Additional interaction |
|---|---|---|
| A0 — Passive | Same permitted recording, normal narration, and initial documents. | None. |
| A1 — Fixed questions | Same initial material. | A predeclared generic interview, maximum three questions or 180 seconds. |
| A2 — Active apprentice | Same initial material. | Up to the same question/time budget, selected from observed uncertainty. |

A0 establishes the value of additional context; A1 versus A2 evaluates whether adaptive questions are worth their complexity. Do not describe A2 versus A0 alone as proof that adaptive selection beats interviewing.

Use the same base Meta model, prompt budget, output schema, and downstream solver where possible. Account for extra expert time explicitly. Counterbalance task variants across conditions; an expert who has already answered a question should not unknowingly teach that answer to the supposedly passive condition. Separate people/variants or disclose crossover effects.

### 3.3 Labels and rubric

A reviewer marks, for each question and resulting claim:
- Was the premise supported by current observations?
- Was the answer already available?
- Did the answer resolve a task-relevant ambiguity?
- Was the question leading or unnecessarily burdensome?
- Were conditions and exceptions preserved faithfully?
- Does the new claim include unsupported physical/casual assertions?
- Did the expert need to correct it?

Use a fixed rubric with categorical outcomes and reasons. A second reviewer is desirable; otherwise disclose the single-reviewer limitation. A model can assist annotation but cannot be the sole correctness authority.

### 3.4 Held-out transfer

After acquisition, freeze the approved knowledge package. Present new cases that vary the relevant condition, including:
- a case inside the learned rule's scope;
- a superficially similar case outside scope;
- a case missing the decisive condition;
- and, where feasible, a correction that supersedes an earlier rule.

The downstream model must act, ask, or abstain according to the approved criteria. Do not give the correct answer in the evaluation prompt or allow retrieval of hidden gold labels.

### 3.5 Pilot size and reporting

A useful exploratory target is three sessions per arm and at least twelve held-out decision cases per arm. Report actual available counts. A smaller result is a case study; it cannot justify broad statistical claims. One illustrative before/after scene does not establish industry-wide improvement.

Report task correctness, correct exception handling, inappropriate application, abstention, useful-question rate, redundancy, correction time, total expert time, and total inference cost. Include baseline failures and active-agent failures. Confidence intervals should respect session/task clustering; do not bootstrap individual frames as independent evidence.

### 3.6 Interpretation

A2 improving over A1 under comparable budgets supports adaptive questioning within the tested task. A2 only improving over A0 may show the value of expert explanation, not the value of live question selection. No improvement is a valid result; preserve it and investigate the failure without silently changing the test set.

## 4. Study B — Dataset correctness and capability levels

### 4.1 Levels

- **L0 observations:** permissioned media plus timestamps and context.
- **L1 expert decisions:** reviewed, source-linked reasoning, conditions, exceptions, and checks.
- **L2 action alignment:** actual recorded/sim-recorded actions and states with units, frame, embodiment, and time mapping.
- **L3 task-specific validated use:** downstream load/replay/training compatibility demonstrated for a named task.

These are VEYTAC labels, not universal industry standards. Physical robot readiness and certification are not implied by L3.

### 4.2 Quality checks

| Check | Required behavior |
|---|---|
| Media decode | Every advertised local asset decodes or is explicitly unavailable. |
| Timing | Interval bounds, clock epochs, gaps, and uncertainty are preserved. |
| Source attribution | Original demonstrator, reviewer, and model inference remain distinguishable. |
| Semantic faithfulness | Reviewed facts match the cited statement and do not add unobserved quantities. |
| Provenance | Model/schema/prompt versions and edits are traceable. |
| Missingness | Unknown quantities remain absent/null with reasons. |
| Rights | Each output use is permitted; code license does not license the data. |
| Split integrity | No source episode or near-duplicate derivative leaks across train/test. |
| Consumer compatibility | Pinned loader accepts actual fields; round-trip retains meanings. |
| Task value | A separate evaluation tests usefulness, not only format validity. |

No single opaque quality score substitutes for this report. Report per-check status and severity.

### 4.3 Phone-only and robot-aligned outputs

A phone-only episode may validly support L0/L1 and human/high-level reasoning tasks. It must fail an export profile requiring robot joint actions that were never recorded.

For public robot data, preserve the original action type: joint position, velocity, end-effector delta, gripper command, or other declared semantics. Never equate video frame rate with controller rate. Do not replace missing state with zeros or infer sensor values from the expert's description.

An expert can review robot clips and add contextual annotations to their exact intervals. This is a valid retrospective review of those trajectories. It is not the original demonstrator's unrecorded reasoning, and it is not proof that an unrelated phone capture was converted into that robot trajectory.

## 5. Study C — Robot-learning experiment

### 5.1 Default scope

Use one compatible robomimic/robosuite task, initially investigate a single-nut assembly task. Verify the actual dataset/task name and environment version in the selected release; do not hard-code a guessed identifier. If compatibility or observation availability blocks the task, choose a documented alternative before training and update the manifest.

Start with low-dimensional observations for a bounded compute check, then optionally image observations if feasible. Report those modalities separately. A rendered robot on screen does not make a state-based policy a visual policy.

**Required pretraining gate:** load a demonstration, replay recorded actions in its compatible environment, and reproduce a plausible documented outcome. Record deviations and exact environment/controller/MuJoCo versions. A failed replay blocks training claims.

### 5.2 Data contract

For every transition preserve `observation`, `next_observation` where required, `action`, timestamps, episode boundary, terminated/truncated distinction, and genuine reward if using offline RL. State/action shapes, units, control rate, action frame, robot ID, environment version, and source split are mandatory.

If rewards or termination semantics are absent, do not invent them to run IQL. Either reconstruct them with a documented simulator replay and report that derivation, or mark RL blocked.

Begin with a small rights-checked subset; derive train/validation/test groups by original episode/demonstrator/configuration. A tentative 60/20/20 episode split is acceptable only if it respects those groups and preserves existing source restrictions. Record counts rather than implying a large corpus exists.

### 5.3 How expert context enters learning

The first experiment should use a concrete, inspectable mechanism rather than claim that natural-language sidecars automatically improve a policy.

**Proposed mechanism: auxiliary decision-phase supervision.**

Experts review the same selected trajectories and annotate supported phase/subgoal labels such as approach, align, insert, or recover, plus conditions explaining transitions. Use only phases supported by the actual task/data. If no recovery trajectories exist, do not fabricate a recovery-class benefit.

The active apprentice helps obtain and scope these annotations. The expert reviews timestamps and meaning. An annotation not observable to the policy at test time may be used as training supervision, but must never be supplied as privileged test-time input.

Use a policy encoder and action head with a small auxiliary phase head:

`L_total = L_action + lambda * mask_known * L_phase`

All arms share the same backbone/action head and observation/action space. Keep the auxiliary head present in all configurations; set its supervised weight according to the arm. Tune lambda on validation data only. This tests annotation-derived supervision, not automatic causal understanding of all the expert's prose.

### 5.4 Comparison arms

| Arm | Trajectories | Extra supervision |
|---|---|---|
| R0 | Same base demonstrations. | None beyond ordinary action learning. |
| R1 | Same base demonstrations. | Passive/generic phase annotation from the same allowed observations, reviewed under a declared budget. |
| R2 | Same base demonstrations. | Active-question-derived reviewed phase/condition annotations. |

R0/R2 can establish an initial contrast; R1 is needed to distinguish active acquisition from the generic benefit of extra labels. Match annotation scope/time as closely as possible and disclose remaining differences. Do not cherry-pick more successful trajectories for R2.

### 5.5 Imitation learning

Use robomimic BC. A compact two-layer MLP is a reasonable low-dimensional starting policy; final hyperparameters depend on the compatible implementation and must be recorded. Begin with a dry-run minibatch and short smoke training, not an expensive sweep.

Train the selected arms with identical action targets, train sets, batch/step budgets, evaluation frequency, and seeds where applicable. Save checkpoints and hashes. Loss reduction only establishes optimization behavior, not task success.

### 5.6 Offline reinforcement learning

After BC and reward/termination gates, use the existing robomimic IQL implementation. Keep the replay data, reward definition, and evaluator fixed. Context can affect the actor through the same reviewed auxiliary supervision, while critic/value objectives remain comparable. Document any parameter-sharing change; do not quietly change model capacity or supply new observations exclusively to the enriched arm.

If modifying the actor loss cannot be implemented and tested within the deadline, run a clearly separate IQL baseline and report the enriched-RL arm incomplete. Do not label a BC model as RL or an unused IQL config as an executed experiment.

No online exploration is performed on real industrial machines.

### 5.7 Compute stages and stopping

1. **Smoke:** one minibatch, short training, and a few rollouts. Verifies plumbing only.
2. **Pilot:** baseline/enriched policies with a declared fixed step budget and at least one completed held-out evaluation. Exploratory evidence only.
3. **Comparison target:** three training seeds and 50 paired evaluation initial conditions per checkpoint/arm where budget permits. The same seeds/conditions are used across arms.

Profile before authorizing a full run. Stop at approved time/cost limits. Do not extrapolate success rates from smoke runs or claim statistically robust gains from one successful rollout.

### 5.8 Metrics and artifacts

Report success numerator/denominator, return, episode length, recovery if supported, declared constraint violations, annotation effort, training/inference runtime, and costs. Use paired initial conditions. Report distributions across training seeds; uncertainty from multiple rollouts of one seed is not the same as training variability.

Required artifacts: source/split manifest, annotation version, config, code commit, seeds, checkpoint hashes, training logs, rollout records/videos, metrics CSV/JSON, failure examples, and conclusion with limitations.

### 5.9 Leakage and ablations

- Remove expert labels while preserving trajectories and architecture.
- Shuffle annotations within the training set as a negative diagnostic where appropriate; do not use it as a production model.
- Verify that test prompts/policy inputs exclude gold phase labels and hidden evaluator state.
- Group near-duplicates and related episodes in splits.
- Do not repeatedly adjust the test environment after viewing results.
- Report results separately for in-distribution and deliberately changed conditions.

A measured simulator gain supports only this simulator/task/observation/data setting. It does not prove that arbitrary phone videos train general industrial robots.

## 6. Study D — Meta model adaptation

### 6.1 Target

Choose one component: non-leading question generation/ranking or faithful decision-record extraction. Use approved text/image examples supported by the selected model. Do not assume raw video fine-tuning is supported by every open-weight model/provider.

### 6.2 Dataset

Include good questions, valid `no_question` cases, correction handling, scope limits, and examples where information is unavailable. Retain source/session groups. Do not train the model to always invent a rationale or always ask a question.

No arbitrary minimum sample count makes a dataset sufficient. Begin with a small schema-valid smoke set and report its size. Train a meaningful adaptation only when enough reviewed examples and held-out cases exist. Synthetic examples must be marked and evaluated separately.

### 6.3 Run and comparison

Freeze the baseline output set, prompts, schema, test cases, and rubric. Use a permitted SFT/LoRA recipe after account confirmation and budget approval. Report base model identity, dataset hash, adapter/checkpoint ID, job receipt, actual cost, and held-out results.

Evaluate faithfulness, useful-question rate, overgeneralization, redundant questions, and abstention. Training completion alone does not mean the adapted model is better.

### 6.4 Interviewer RL extension

Only after the question-selection task has an objective evaluable outcome, consider a bounded policy-learning experiment. A possible reward is downstream task correctness minus question/time cost and unsupported-claim penalties. Validate the reward against loopholes such as suppressing every question, asking the evaluator for the answer, or inducing agreement.

Live expert-memory acquisition is not this experiment. Keep its state updates and training claims distinct.

## 7. Final research report structure

```text
1. Task and scope
2. Source data and permissions
3. Hypotheses and fixed protocol
4. Conditions, algorithms, and exact information available
5. Expert effort and annotation process
6. Split groups, seeds, environment and code versions
7. Actual runs, failures, and exclusions
8. Metrics with denominators and uncertainty
9. Ablations and leakage checks
10. Costs and timing
11. What the evidence supports
12. What remains untested
```

A zero or negative gain is reported directly. The implementation may still be useful, but the corresponding improvement claim is not earned. The founder's long-term robotics vision remains a vision until each additional evidence stage is demonstrated.
