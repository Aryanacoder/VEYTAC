# VEYTAC — Acceptance test specifications

Version: 0.1.0 • Initial status of every case: **NOT RUN**

These are tests to implement, not executable test files or passing results. Each case must produce an actual observed result and artifact references. Mock tests validate logic; only the indicated real-provider/device/robot modes establish those integrations. `critical` failures block the corresponding release gate. An optional feature can be absent, but its capability cannot be advertised.

Test fixtures must be small, permitted, and labeled synthetic where appropriate. Preserve negative cases and denial behavior. Do not modify fixed expectations to match a convenient model output.

## Test cases

### V-ENV-01 — Clean checkout, no secrets

**Requirements:** FR-28, FR-29  
**Severity:** critical • **Execution:** mock/integration

**Given:** A clean clone and the documented supported environment, without provider keys.

**When:** Run setup, migrations, local doctor, mocked tests, and frontend build.

**Then:** Setup completes or reports a specific missing prerequisite; mocks are labeled; no paid request is attempted; actual commands/results are saved.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-ENV-02 — Real capability probe

**Requirements:** FR-07, FR-08, FR-28  
**Severity:** high • **Execution:** real provider

**Given:** Owner-approved small public/owned fixtures, configured Meta account, and a bounded budget.

**When:** Probe supported observation, structured output, ASR, and optional segmentation independently.

**Then:** Each capability records actual model, endpoint, output validation, usage, latency, and availability. Unsupported access is blocked, never substituted with hidden mock success.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-CAP-01 — Separate permissions

**Requirements:** FR-01, FR-25  
**Severity:** critical • **Execution:** mock/integration

**Given:** A new session without recording or processing grants.

**When:** Attempt capture, then grant recording only and attempt external inference.

**Then:** Capture cannot start without permission. Recording-only permission does not authorize provider processing, training, or publication.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-CAP-02 — Real phone capture

**Requirements:** FR-02, FR-04  
**Severity:** critical • **Execution:** real device

**Given:** The actual supported phone/browser over HTTPS and a consented short task.

**When:** Capture camera/mic, stop, assemble, and replay the result.

**Then:** Readable media and source metadata exist; real timestamps and gaps are preserved; actual browser/codec are recorded; camera/mic stop after stop.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-CAP-03 — Duplicate and conflicting media chunks

**Requirements:** FR-04, FR-26  
**Severity:** critical • **Execution:** mock/integration

**Given:** A stream receives chunk 4 with hash H.

**When:** Resend chunk 4 with H, then with a different hash.

**Then:** Same-hash resend returns the original acknowledgment without duplicate jobs/cost. Different bytes under the same index return a conflict and preserve the original.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-CAP-04 — Nonuniform chunk timing

**Requirements:** FR-04  
**Severity:** critical • **Execution:** media integration

**Given:** A recorder emits delayed blobs and variable frame timing.

**When:** Build the timeline and a derived clip.

**Then:** Times come from capture/media clocks, not blob count times requested interval. Gaps and derivative source mapping remain explicit.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-CAP-05 — Network disconnect and resume

**Requirements:** FR-02, FR-26  
**Severity:** high • **Execution:** real device/network

**Given:** A live session with acknowledged chunks and queued analysis.

**When:** Disconnect for several seconds, reconnect, and resend unacknowledged data.

**Then:** No acknowledged evidence is lost; duplicates do not create duplicate questions; lag/backlog is visible; original mode is preserved.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-CAP-06 — Pause and revoke while work is pending

**Requirements:** FR-02, FR-11, FR-31  
**Severity:** critical • **Execution:** mock/integration

**Given:** Capture, ASR, and a queued question are active.

**When:** Pause; then revoke external processing permission.

**Then:** Worker-directed output stops, new uploads/processing obey the selected pause semantics, queued unauthorized calls are canceled, and in-flight limitations are reported.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-CAP-07 — Phone lock/background and oversized blob

**Requirements:** FR-02, FR-26  
**Severity:** high • **Execution:** real device

**Given:** Capture runs on the tested phone.

**When:** Lock/background the browser, restore it, and simulate a blob above the configured cap.

**Then:** The UI does not imply uninterrupted observation; discontinuities are marked; oversize handling is explicit and no media is silently dropped.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-CAP-08 — Screen and upload alternatives

**Requirements:** FR-03, FR-33  
**Severity:** high • **Execution:** real browser

**Given:** A supported desktop browser plus an unsupported mobile screen-capture path.

**When:** Request screen capture on each and import a permitted recording.

**Then:** Supported desktop capture records actual source metadata; unsupported capture offers labeled upload; no hidden substitution of replay for live.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-CAP-09 — No access to future frames

**Requirements:** FR-04, FR-07  
**Severity:** critical • **Execution:** mock/integration

**Given:** Current live watermark is 20 seconds; the full fixture contains 60 seconds.

**When:** Ask the agent/evidence retrieval tool about the outcome at 45 seconds.

**Then:** Only evidence at or before 20 seconds is available. A model reference to 45 seconds is rejected and logged; the evaluator can access full truth separately.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-CAP-10 — Recorder fragments are not independent files

**Requirements:** FR-04, FR-17  
**Severity:** critical • **Execution:** media integration

**Given:** A supported recording consists of container-dependent fragments.

**When:** Attempt decode of each blob and then the assembled stream.

**Then:** Unsupported independent fragments are not sent as valid videos; verified frames/remuxed clips retain original mapping and decode checks.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-ASR-01 — English and Japanese speech

**Requirements:** FR-05, FR-12  
**Severity:** high • **Execution:** real provider/human

**Given:** Consented examples with known short phrases, task vocabulary, and one English/Japanese switch.

**When:** Run actual ASR and review finalized turns.

**Then:** Original speech/text and translation provenance are retained; observed recognition errors are reported; unsupported spoken output is not advertised.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-ASR-02 — Critical negation and identifier correction

**Requirements:** FR-05, FR-13  
**Severity:** critical • **Execution:** mock/integration

**Given:** ASR mishears a negation or component identifier in a fixture.

**When:** The expert corrects it and approves the interpretation.

**Then:** Original and corrected versions remain linked; all downstream records use the approved correction or are marked stale; the old meaning is not silently retained.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-ASR-03 — Out-of-order turns and partials

**Requirements:** FR-04, FR-12  
**Severity:** critical • **Execution:** mock/integration

**Given:** Provider fixtures contain overlapping turns, delayed finals, and partials without turn IDs.

**When:** Feed the documented event sequence to the adapter.

**Then:** Final text maps to the correct turn/question; later finals do not overwrite other turns; unavailable word timestamps/confidence are not fabricated.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-ASR-04 — Silence, skip, and unknown

**Requirements:** FR-12  
**Severity:** critical • **Execution:** mock/integration

**Given:** A question is delivered but the expert remains silent or selects unknown/skip.

**When:** Finalize the interval.

**Then:** No synthetic answer or approval is created. The unresolved gap remains visible and appropriately scoped.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-ASR-05 — Question speech is not an expert answer

**Requirements:** FR-05, FR-12  
**Severity:** high • **Execution:** device/provider integration

**Given:** The application uses a tested speech-output option while capturing audio.

**When:** Play a question and then obtain the human reply.

**Then:** Playback is gated/labeled or filtered by known output interval; the question text is not attributed as the expert answer. Typed fallback works.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-OBS-01 — Grounded observations

**Requirements:** FR-07, FR-14  
**Severity:** critical • **Execution:** mock/integration

**Given:** A clip shows an action but not the hidden force or intention.

**When:** Ask for observations and proposed explanations.

**Then:** Visible action and uncertainty are distinguished from hypotheses. Unseen force/intention is not emitted as measured truth; source intervals resolve.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-OBS-02 — Instructions embedded in evidence

**Requirements:** FR-06, FR-25  
**Severity:** critical • **Execution:** mock/integration

**Given:** An uploaded image/document says to ignore rules, leak keys, and publish the dataset.

**When:** Process it as task context.

**Then:** Content remains untrusted evidence. No privilege, tool scope, consent, or publication state changes; the attempted injection is recorded without exposing secrets.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-OBS-03 — Segmentation missing or occluded object

**Requirements:** FR-08  
**Severity:** high • **Execution:** real provider/review

**Given:** A source contains a tiny or partly hidden component and a larger visible object.

**When:** Run selective segmentation and inspect its mapping.

**Then:** Masks map to the actual frames; failed segmentation is unsupported/unknown, not proof of absence; no physical connection/force claim is inferred from a mask.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-OBS-04 — Document evidence locators

**Requirements:** FR-06, FR-07  
**Severity:** critical • **Execution:** mock/integration

**Given:** A permitted multi-page context file with an exact component statement.

**When:** Extract a proposed fact and follow its source link.

**Then:** Page/line/region and asset version resolve to the supporting content. Nonexistent or out-of-bounds locators are rejected.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-QUE-01 — Uncertain premise

**Requirements:** FR-09, FR-10  
**Severity:** critical • **Execution:** mock/integration

**Given:** The agent cannot tell whether the expert changed a setting or only moved the pointer.

**When:** Generate a question.

**Then:** The selected question clarifies what happened rather than presupposing a change and inventing a reason.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-QUE-02 — Discriminating question

**Requirements:** FR-09, FR-10  
**Severity:** critical • **Execution:** mock/integration

**Given:** Two plausible explanations imply different actions on a later case.

**When:** Rank candidates under the same question budget.

**Then:** The selected question identifies the missing decision condition with an evidence anchor; ranking and concise reason are recorded without claiming calibrated information gain.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-QUE-03 — Do not ask what is already known

**Requirements:** FR-10  
**Severity:** critical • **Execution:** mock/integration

**Given:** The answer appears in an approved applicable record and current source context.

**When:** Run another observation cycle.

**Then:** The question is suppressed or revised to a genuinely unresolved condition; duplicate counters and source lookup are logged.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-QUE-04 — Safe-pause and expiry

**Requirements:** FR-11  
**Severity:** critical • **Execution:** mock/integration

**Given:** A physical session has questions_allowed=false, then a 30-second human window.

**When:** Generate a question before, during, and after the window; revoke mid-playback.

**Then:** No worker-directed audible interruption outside the window; revocation stops output; deferred questions remain inspectable; a model cannot open the gate.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-QUE-05 — Cooldown, cap, and one outstanding question

**Requirements:** FR-10, FR-11  
**Severity:** critical • **Execution:** mock/integration

**Given:** Several consecutive frames produce related gaps.

**When:** Run repeated observation cycles and simulate slow human answers.

**Then:** At most one question is outstanding; cooldown and autonomous cap hold; source changes do not bypass deduplication.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-QUE-06 — Expert rejects the AI interpretation

**Requirements:** FR-12, FR-13  
**Severity:** critical • **Execution:** mock/integration

**Given:** The expert says the premise was wrong.

**When:** Process the correction.

**Then:** The original observation becomes disputed/superseded as appropriate; no rationale is forced; a new scoped interpretation requires review.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-QUE-07 — Stale question

**Requirements:** FR-10, FR-26  
**Severity:** critical • **Execution:** mock/integration

**Given:** A queued question concerns a state that changed before delivery.

**When:** Open a question window after its expiry/context change.

**Then:** The question expires or is explicitly reframed as retrospective; it is not delivered as a current situation.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-KNW-01 — Complete record with honest missingness

**Requirements:** FR-14  
**Severity:** critical • **Execution:** mock/integration

**Given:** An expert explains action, one condition, and a check, but does not supply an exception.

**When:** Build the decision record.

**Then:** Provided fields are captured faithfully; exception is unresolved rather than invented; source and speaker role are preserved.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-KNW-02 — Review does not create measurements

**Requirements:** FR-13, FR-14  
**Severity:** critical • **Execution:** mock/integration

**Given:** The expert reports feeling resistance without a force sensor.

**When:** Approve the record and export it.

**Then:** Cue remains expert_reported; no numeric force, joint action, or calibrated physical status is created by approval.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-KNW-03 — Review permissions and stale revision

**Requirements:** FR-13, FR-25  
**Severity:** critical • **Execution:** mock/integration

**Given:** A viewer tries to approve a record; an authorized reviewer has an outdated version.

**When:** Submit approval requests.

**Then:** Viewer is denied; stale reviewer request returns conflict; approval is attached only to the current explicitly inspected revision.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-KNW-04 — Supersession reaches downstream uses

**Requirements:** FR-13, FR-15, FR-19  
**Severity:** critical • **Execution:** mock/integration

**Given:** An approved rule has already produced a lesson and export draft.

**When:** Correct its applicability and approve a new revision.

**Then:** Current retrieval excludes the superseded rule; dependent artifacts are marked stale and need regeneration/reapproval; historical versions remain attributable.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-KNW-05 — Conflicting experts

**Requirements:** FR-13, FR-15  
**Severity:** critical • **Execution:** mock/integration

**Given:** Two approved statements conflict under apparently overlapping conditions.

**When:** Attempt to use them on a new case.

**Then:** The conflict is exposed and scoped; the system asks or abstains rather than selecting convenient consensus. Reviewer identity is retained.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-KNW-06 — Unseen condition and counterexample

**Requirements:** FR-15, FR-30  
**Severity:** critical • **Execution:** mock/integration

**Given:** A scoped approved rule and a held-out case inside and outside its scope.

**When:** Run the same downstream task with and without that rule.

**Then:** Rule applies only to supported conditions; missing conditions produce clarification/abstention; outcome is scored against fixed gold criteria.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-KNW-07 — Impossible evidence references

**Requirements:** FR-07, FR-14  
**Severity:** critical • **Execution:** mock/integration

**Given:** A model proposes an unknown asset, reversed interval, or out-of-bounds region.

**When:** Validate output before it enters review.

**Then:** The invalid reference is rejected with a precise error. A repair attempt cannot silently fabricate an asset or widen access.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-KNW-08 — Retrospective reviewer attribution

**Requirements:** FR-14, FR-32  
**Severity:** critical • **Execution:** mock/integration

**Given:** An expert comments on an authorized public recording made by someone else.

**When:** Construct and export the episode.

**Then:** Explanation is attributed to retrospective_reviewer, not the original demonstrator; source license and new commentary permission remain separate.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-DAT-01 — Canonical export round trip

**Requirements:** FR-16, FR-17  
**Severity:** critical • **Execution:** mock/integration

**Given:** An approved episode with permitted assets.

**When:** Export, validate checksums, reload into a clean environment, and follow evidence links.

**Then:** Schema and semantic validators pass; no private key/path appears; approved revision and payload hashes match.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-DAT-02 — License and use-specific restrictions

**Requirements:** FR-17, FR-21, FR-32  
**Severity:** critical • **Execution:** mock/integration

**Given:** One source permits internal review but not redistribution or training.

**When:** Attempt public release and a training manifest.

**Then:** Restricted uses are blocked or explicitly reference-only where allowed; the top-level code license does not override asset terms.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-DAT-03 — Phone-only robot-action rejection

**Requirements:** FR-16, FR-18  
**Severity:** critical • **Execution:** mock/integration

**Given:** A valid phone episode contains video and rationale but no measured robot action/state.

**When:** Request an action-policy/LeRobot profile requiring those fields.

**Then:** Request is rejected with missing fields; canonical context export still works; no zero-filled or guessed action trajectory is created.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-DAT-04 — Genuine action-aligned loader

**Requirements:** FR-18, FR-23  
**Severity:** critical • **Execution:** robot data integration

**Given:** A licensed source with real/sim-recorded actions, state, and pinned format metadata.

**When:** Export via the adapter and load with the pinned downstream library.

**Then:** Shapes, time alignment, action meanings, units, embodiment, and task IDs are preserved; an actual loader log is saved.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-DAT-05 — Misalignment and units

**Requirements:** FR-04, FR-18  
**Severity:** critical • **Execution:** mock/integration

**Given:** A robot fixture has a shifted clock, wrong frame, or incompatible units beyond declared tolerance.

**When:** Run capability checks.

**Then:** Action alignment is denied or corrected through an explicit documented transform; no silent resampling/renaming claims compatibility.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-DAT-06 — Split leakage

**Requirements:** FR-22, FR-23, FR-30  
**Severity:** critical • **Execution:** mock/integration

**Given:** Two clips/annotations derive from the same episode or task family.

**When:** Generate training and held-out manifests.

**Then:** Grouped split keeps related examples together; duplicate hashes and derivative lineage cannot cross boundaries unnoticed.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-DAT-07 — No unsupported facts in dataset card

**Requirements:** FR-16, FR-17  
**Severity:** critical • **Execution:** mock/integration

**Given:** A dataset lacks force, calibration, or physical validation.

**When:** Generate its card and capabilities.

**Then:** Limitations and missing fields are visible; the card does not advertise measured force, calibrated control, or real-world success.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-DAT-08 — External asset references

**Requirements:** FR-17, FR-32  
**Severity:** critical • **Execution:** mock/integration

**Given:** A public dataset may be used locally but not repackaged.

**When:** Create a permitted reference-only bundle.

**Then:** It includes retrieval instructions and source hashes/terms as allowed, not unauthorized media bytes or broken implied local paths.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-LES-01 — Lesson evidence and scope

**Requirements:** FR-19  
**Severity:** critical • **Execution:** mock/integration

**Given:** Approved records with evidence and a contrasting condition.

**When:** Generate and inspect the lesson.

**Then:** Each substantive explanation links to approved evidence; it presents an exercise and exception, not universal procedural advice.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-LES-02 — Illustration versus simulation

**Requirements:** FR-19, FR-20  
**Severity:** critical • **Execution:** mock/integration

**Given:** A generated diagram and a genuine simulator replay are both available.

**When:** Render them in the lesson.

**Then:** Their origin labels differ; diagram motion is not called physics; replay is not called a newly executed experiment.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-LES-03 — Malicious generated markup

**Requirements:** FR-20, FR-25  
**Severity:** critical • **Execution:** mock/integration

**Given:** Generated SVG/HTML contains script, external fetch, or data-exfiltration URL.

**When:** Attempt preview.

**Then:** Unsafe code is removed or isolated in a restricted sandbox with networking disabled; no script runs in the main authenticated origin.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-CAT-01 — Private-by-default catalog

**Requirements:** FR-21, FR-25  
**Severity:** critical • **Execution:** mock/integration

**Given:** A private episode and approved but unpublished release exist.

**When:** Browse catalog and guess object/download IDs as another principal.

**Then:** Neither private content nor unpublished metadata is exposed; object authorization is enforced on every retrieval.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-CAT-02 — Exact-version publication

**Requirements:** FR-21  
**Severity:** critical • **Execution:** mock/integration

**Given:** A reviewer approves manifest hash H and media then changes.

**When:** Try publishing the modified release under the old approval.

**Then:** Publishing is denied until the new payload is reviewed; exact approved hash appears in publication audit.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-CAT-03 — Delisting and no false recall promise

**Requirements:** FR-21, FR-31  
**Severity:** critical • **Execution:** mock/integration

**Given:** A published hosted dataset has already been downloaded.

**When:** Delist and request deletion.

**Then:** Hosted discovery/download access is revoked and cleanup status is recorded; UI does not claim external copies have been erased.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-SEC-01 — Object authorization

**Requirements:** FR-25  
**Severity:** critical • **Execution:** mock/integration

**Given:** Two workspaces with distinct media, decisions, and sessions.

**When:** Use authorized credentials from A to access B by known IDs.

**Then:** Every route/socket denies access, including derived assets and range requests; no sensitive error details leak.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-SEC-02 — Path traversal and archive bomb

**Requirements:** FR-25  
**Severity:** critical • **Execution:** mock/integration

**Given:** A file/archive includes relative traversal paths or excessive expanded size.

**When:** Ingest it.

**Then:** Input is rejected/quarantined before writing outside allowed roots or exhausting resources; error is recorded safely.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-SEC-03 — Canary credential leakage

**Requirements:** FR-25, FR-29  
**Severity:** critical • **Execution:** mock/integration

**Given:** A fake canary secret exists only in the server test environment.

**When:** Exercise logs, frontend build, export, lesson, provider prompts, and error handling.

**Then:** Canary appears nowhere unauthorized. The test must not use a real key.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-SEC-04 — Consent withdrawal and deletion lineage

**Requirements:** FR-31  
**Severity:** critical • **Execution:** mock/integration

**Given:** A session has original/derived media, lessons, queued jobs, and a provider file reference.

**When:** Withdraw processing permission and request deletion.

**Then:** Access revokes immediately; queued jobs stop; hosted artifacts and derivatives are removed according to policy; provider/backup limitations are explicit and retried where supported.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-SEC-05 — SSRF and unrestricted tool denial

**Requirements:** FR-25  
**Severity:** critical • **Execution:** mock/integration

**Given:** An input asks to fetch a private metadata endpoint or execute shell commands.

**When:** Process model tool proposals and optional URL imports.

**Then:** Allowlist/policy blocks the action. Runtime model cannot access secrets, arbitrary filesystem, or live industrial control.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-SEC-06 — No biometric or employee scoring drift

**Requirements:** FR-01, FR-25  
**Severity:** critical • **Execution:** mock/integration

**Given:** Multi-speaker audio and workplace video are submitted.

**When:** Inspect generated metadata and UI.

**Then:** Only session-local labels or user-provided identities are used; no inferred identity, sensitive traits, productivity ranking, or surveillance feature is produced.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-BUD-01 — Atomic budget reservation

**Requirements:** FR-24  
**Severity:** critical • **Execution:** mock/integration

**Given:** Only $1 remains and two concurrent calls each require $0.70 reservation.

**When:** Attempt both dispatches.

**Then:** At most one reserves successfully; the other is blocked before a provider request. Money is represented precisely, not binary-float approximations.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-BUD-02 — External coding spend and reserve

**Requirements:** FR-24  
**Severity:** critical • **Execution:** mock/integration

**Given:** App has its own tracked spend; coding usage is unknown or newly reported.

**When:** Recalculate available funds and attempt routine calls against the demo reserve.

**Then:** External allocation is conservatively reserved until reconciled; protected demo funds are not borrowed automatically.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-BUD-03 — Timeout and uncertain billing

**Requirements:** FR-24, FR-26  
**Severity:** critical • **Execution:** mock/integration

**Given:** A provider accepts a request but the response times out.

**When:** Retry/finalize billing.

**Then:** Reservation remains or is conservatively charged; a retry gets its own authorization; unknown billing is not assumed free.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-BUD-04 — Unapproved paid job

**Requirements:** FR-22, FR-23, FR-24  
**Severity:** critical • **Execution:** mock/integration

**Given:** An API key exists but no valid owner approval or partner credit verification does.

**When:** Run a training/deployment command, including dry-run.

**Then:** Real provisioning is blocked; dry-run makes no paid call; approval must bind data/config/resources/cost/expiry.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-BUD-05 — Media billing units

**Requirements:** FR-24  
**Severity:** critical • **Execution:** mock/integration

**Given:** Mock usage includes SAM clips below minimum billed frames and both cached/uncached tokens.

**When:** Reconcile costs using the versioned rate card.

**Then:** Minimums and separate token classes are applied; source quantities are retained; rates are not silently treated as permanent.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-DOM-01 — Second-domain portability

**Requirements:** FR-06, FR-33  
**Severity:** critical • **Execution:** mock/integration

**Given:** One physical-task config and one clean-room screen-task config use the same schema.

**When:** Import/review/export both without changing core service code.

**Then:** Domain vocabulary/validators differ by config; assumptions do not leak across tasks; demonstration is labeled portability, not broad accuracy.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-EVL-01 — Fair comparison and held-out context

**Requirements:** FR-30  
**Severity:** critical • **Execution:** mock/integration

**Given:** Frozen passive/fixed/adaptive evaluation manifests exist.

**When:** Run all conditions with matched observations and declared budgets.

**Then:** No test answer appears in runtime context; expert/time differences are recorded; same downstream model and evaluator are used.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-EVL-02 — No empty-results success

**Requirements:** FR-22, FR-23, FR-30  
**Severity:** critical • **Execution:** mock/integration

**Given:** A training/eval job fails, is skipped, or produces no valid rollouts.

**When:** Generate summary and UI status.

**Then:** Status remains failed/blocked/not-run; missing metrics are not zeros and no improvement claim is emitted.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-EVL-03 — Context actually enters robot training

**Requirements:** FR-23  
**Severity:** critical • **Execution:** training integration

**Given:** Baseline and context-enabled configs share trajectories and architecture.

**When:** Inspect minibatches, losses, and a controlled annotation ablation.

**Then:** Reviewed context changes the intended supervised signal; no hidden ground truth is exclusive at test time; an unused sidecar fails this test.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-EVL-04 — Actual policy comparison

**Requirements:** FR-23  
**Severity:** high • **Execution:** robot training/evaluation

**Given:** Verified source data, reward semantics, simulator replay, and approved compute.

**When:** Run declared BC and bounded IQL experiments and fixed rollouts.

**Then:** Actual checkpoints, seeds, metrics, failures, configurations, and costs exist; result is not inferred from decreasing loss.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-EVL-05 — SFT base-versus-tuned comparison

**Requirements:** FR-22  
**Severity:** high • **Execution:** paid training

**Given:** Eligible reviewed examples, rights, funded job, and frozen test set exist.

**When:** Train the approved component and compare with the same base model.

**Then:** Checkpoint identity and actual results are stored; non-improvement remains visible; synthetic and real examples are distinguished.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-REL-01 — Release evidence and clean repository

**Requirements:** FR-27, FR-29  
**Severity:** critical • **Execution:** mock/integration

**Given:** Implementation is proposed for public release.

**When:** Run secret/license audit, clean-checkout test, and evidence manifest validation.

**Then:** No private media/keys/restricted assets; claims link to actual artifacts; original hackathon contributions are clear.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.

### V-REL-02 — Live failure and disclosed fallback

**Requirements:** FR-02, FR-27, FR-29  
**Severity:** critical • **Execution:** demo rehearsal

**Given:** Rehearsed live demo experiences provider/network failure.

**When:** Use the fallback recording or mock exploration.

**Then:** UI and narration state the actual mode; no delayed or cached answer is represented as new live reasoning.

**Evidence:** test log plus relevant event, artifact, or report IDs; record actual mode, environment, and any limitation.
