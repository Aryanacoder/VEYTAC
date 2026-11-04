# Muse Code follow-up: iPhone Safari voice and camera formats (2026-11-04)

## Owner's latest phone result

Session `ses_[redacted]` on iPhone Safari with the speaker recorded 46 chunks over about 95 seconds. The sampled recording was 480x640 with video and audio tracks. Questions appeared but were not heard or answered through live STT. Seven model observations failed; six exhausted the 800-token reasoning budget with no visible JSON. There were no voice budget reservations or answer records. This is a failed live session, not a passing voice or observation test.

## Changes for the next run

- Meta observation and question requests use minimal reasoning with larger output reservations. Empty visible output is an explicit `PROVIDER_EMPTY` failure. The browser stops further paid frame requests after a failed observation while retaining recording and local tracking.
- Start plays a brief language-matched cue from the user's tap before the spoken opening question. TTS/ASR progress is logged as status-only session diagnostics. The browser can reacquire a muted microphone track after playback. Hear question and Listen now are visible recovery controls.
- Portrait and landscape request 9:16 and 16:9 camera formats and update constraints on rotation. The actual preview dimensions are shown; the sensor may choose a different format.
- The Vite `/api` and voice WebSocket proxy targets the running IPv4 backend.

## Next evidence to collect

1. In a consented iPhone Safari speaker session, confirm an audible ready cue and opening question. Answer the task brief aloud. Record the session ID and report whether the question was audible and whether the answer appeared on screen. Inspect only the diagnostic event names and timing: `tts_started`, `tts_ended`, `asr_relay_ready`, `asr_audio_started`, `asr_final`, or failure events. Do not copy raw audio or secrets into an issue.
2. If the question is silent, tap Hear question once. If STT remains idle, tap Listen now once. Compare status events to distinguish Safari speech synthesis, WebSocket, microphone, and provider ASR failures. Investigate iPhone Safari playback and microphone coexistence using the device, not Chromium mocks.
3. Rotate the same phone between portrait and landscape. Check preview size and saved chunk dimensions with `ffprobe`; verify the recording aspect on that device. If Safari cannot switch the current track, restart only the camera track while preserving the session and noting the recording gap.
4. After one answered brief, verify a nonempty grounded observation, proposed/delivered follow-up, final transcript, and a reviewed decision. If Meta still returns empty output, collect sanitized finish reason, token counts, and request ID; revise the prompt/output budget under the cost gate. Do not silently turn failed observations into mock detections.

## Verification boundary

Offline Python tests, TypeScript build, tracker tests, and Chromium browser mocks passed on 2026-11-04. Real iPhone Safari TTS, STT, Meta response quality, and 9:16/16:9 recording are **NOT_RUN after the fixes**. No paid call was made by this repair. Meta provider use in the owner's earlier session is represented by the internal budget ledger; actual billing is unverified.
