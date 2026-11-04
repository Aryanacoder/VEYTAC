# Decision: responsive live capture and reviewed learning card (2026-11-04)

## Scope and reason

The live voice socket closed with provider policy code 1008. The client also sent tiny audio frames hundreds of times per second while the relay slept after each frame. Browser vision initialization could block speech timers. Stop removed the camera stream, contrary to the requested always-on preview.

## Contracts and permissions

- Meta ASR now sends a model-bearing handshake with an array `languageBias`, a URL `sessionId`, and an `endStream` marker. Browser audio is batched as 80 ms, 24 kHz, mono PCM16 frames. Provider errors are surfaced as voice errors and browser speech may take over. No provider key enters browser code.
- Camera preview is acquired independently of a recording session. Start still requires explicit capture, external-processing, and spoken-question permission. Stop ends recording, microphone use, question permission, and tracking while retaining the local camera preview. The 15-minute recording cap remains.
- Local, pinned MediaPipe models and WASM are installed by `scripts/setup_vision_assets.py` into an ignored folder and served from the LAN origin. In supported browsers the CPU detectors run in a classic worker to avoid blocking voice and controls. The visible hand landmarks and generic object boxes are derived image observations; they do not establish object identity, forces, robot joint states, or action alignment.
- The lesson list API returns persisted lessons for a session. A learning card uses the review's `approved_scope` and displays the original expert statement and limitations. Review now asks the reviewer for an ID and approved scope; these are not supplied by the runtime.
- The existing 45-second question cooldown is retained. The client now retries once it expires when a grounded observation is waiting.

## Evidence and limits

Offline backend tests, browser mocks, and local model initialization cover the code path. They do not establish real Meta ASR, real pen/iPad classification, iOS worker support, physical simulation, or robot-ready trajectories. No paid call, training job, or third-party asset redistribution was authorized or performed by this change. Model assets remain local and Git-ignored.

Affected requirements: PRD FR-01, FR-02, FR-05, FR-07, FR-08, FR-11, FR-13 (review), FR-18 (robot action boundary), FR-19 (lesson), NFR-02, NFR-03, NFR-09, NFR-10. This change does not establish full acceptance of those requirements.

## Phone-session failure and response (2026-11-04)

The latest owner phone session (`ses_[redacted]`) recorded 46 video chunks, but all seven Meta observations failed validation. Six provider replies had no visible response body; the model used nearly all of the 800-token output limit for reasoning. No voice reservation or finalized answer was recorded. This is failed live evidence, even though video capture worked. The stored budget ledger estimates $0.080136 plus $0.0165 of unknown cost; these are internal estimates, not a provider invoice.

- Observation and question calls now request minimal reasoning and reserve for 1400 and 800 output tokens respectively. An empty provider response is saved as `PROVIDER_EMPTY`; raw provider output and secrets are not exposed in the error. A failed observation pauses further paid frame requests in that browser session while local tracking and recording continue.
- The session diagnostics endpoint accepts only bounded status names and timestamps. It cannot accept audio, transcripts, keys, or arbitrary client fields. The client records TTS start/end/failure and ASR relay/browser milestones to distinguish speaker failure from microphone or socket failure on the next consented run.
- On the user's iPhone Safari speaker path, a short localized speech cue runs in the Start tap to initiate audio output. Questions still use browser speech synthesis, then ASR begins after playback. If the recorded microphone track is muted or ended after playback, the client reacquires audio for ASR and stops that auxiliary stream with listening. Manual Hear question and Listen now controls give a direct recovery action; Listen now starts browser recognition in the tap handler when available so Safari can use that user gesture.
- Camera constraints request 9:16 in portrait and 16:9 in landscape, and update the live video track on viewport rotation. The browser may choose another supported sensor format, so the UI displays the actual video resolution. Recording starts from the same live preview track and does not wait for a second `play()` promise when frames are already present.
- The Vite API and WebSocket proxy points explicitly at IPv4 `127.0.0.1:8000` to match the local backend listener.

No additional paid provider call was made during these fixes. Chromium/browser mocks verify flow, not real iPhone speaker output, Meta ASR, or sensor aspect selection. A new consented phone run is required to establish those results. A schema change here is limited to the status-only diagnostics request model and endpoint; the session/observation/answer schemas are unchanged. Affected requirements: FR-02, FR-05, FR-07, FR-11, NFR-02, NFR-03, NFR-10.
