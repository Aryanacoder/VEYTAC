# Muse Code follow-up: screen capture and dataset evidence

Codex added desktop screen selection, shared recording/voice/observation flow, sampled SAM mask display, chunk timing/hashes, a per-session dataset quality report, a deterministic postprocess review queue, rights-gated reviewed-decision JSONL, and localized acknowledgments. LeRobot v3 is the owner's selected future robot-policy target. The current observation ZIP is **not** a LeRobot dataset and has no measured robot state/action trajectory. Keep that gate blocked.

Latest stored camera session at inspection: `ses_[redacted]` had 32 contiguous, hash-verified chunks and a seekable 62.955-second recording; seven live observations, nine on-device track samples, a saved brief and four expert notes. No question, answer, decision, SAM mask or chunk-timing record was saved. The live question proposer was passing scene description instead of the observation's uncertainty; Codex changed that and added question lifecycle diagnostics. This is a code fix awaiting a real device retest, not evidence that conversation now works.

## Review next

1. On desktop Chrome/Edge, consent to a short screen recording of owned material. Confirm the screen picker appears from Start, the preview and spoken task question work, expert speech is captured, Stop ends sharing, camera preview resumes, and the private library replays the right source with aligned masks. Screen capture on iPhone Safari is not established; report browser support as a capability check, not an app success.
2. Run a camera sample with a person and small object. Check the live SAM response actually contains decoded SVG paths and that the filled outline sits on the intended pixels. Record empty or wrong masks as negative evidence. Confirm SAM billing and metadata against the actual provider response under the existing cost gate before further live calls. Do not paste keys, raw media, or transcripts into reports.
3. Inspect `/api/v1/sessions/{id}/dataset/quality` and the Robot/AI dataset library tabs. Verify raw chunk SHA-256 and clock continuity, FFmpeg seekability, approved latest decision revisions with observation evidence, source rights declaration, and consent gates. Test that unreviewed decisions, camera or screen data without rights, and older sessions without owner cookie cannot be exported as reviewed AI data.
4. If robot sensors become available, define a versioned LeRobot v3 adapter in an isolated robotics package: actual camera frames, measured state/action arrays, units, calibration, control rate, timestamps, episode metadata, and a loader round trip. Require action alignment validation and held-out evaluation. Never fill null fields with inferred values from video.
5. For a code-agent harness, collect consented screen plus tool-call traces, code diffs, task constraints, test outputs and reviewer outcomes. Use session-preserving splits and executable evaluations before creating a training export. The current postprocess roles are deterministic gates, not an autonomous agent fleet.

## Verification still required

Real desktop screen picker and audio, iPhone Safari speaker/ASR interaction, actual SAM mask geometry, replay timing after gaps, privacy redaction, and any model/robot training evaluation are NOT_RUN until measured. Do not call a candidate dataset training-ready or robot-ready.
