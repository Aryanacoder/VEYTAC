# Decision: recorded replay, expert object labels, and observation dataset (2026-11-05)

## Evidence and cause

The latest iPhone Safari session (`ses_[redacted]`) stored 56 video chunks. Its first chunk reported 1280×720 video. The live preview used `object-fit: cover`, which cropped the landscape camera image on a portrait phone. The session also recorded ASR final and question-proposal diagnostics, but the persisted task brief and related records were absent. The voice budget reconciliation wrote an older session payload over newer fields.

## Contract and implementation decisions

- Show the full camera frame with `contain`, remove the standby artwork once preview is ready, and project live boxes, hand points, and replay overlays through the same letterbox geometry. The camera may still select a sensor crop for its own aspect-ratio constraints; a real phone comparison is required.
- Serialize session budget reservation/reconciliation and session-field updates against the latest SQLite row. Never replace a session with a stale request-local copy. Keep the existing session budget cap and reserve before a paid call.
- Save time-aligned on-device boxes and hand points in bounded batches during recording. Preserve the original chunks and declare a recording complete only after the final MediaRecorder event and all uploads resolve. A local FFmpeg stream copy derives a duration-bearing, seekable playback file when FFmpeg is present; raw chunks remain the fallback. Stream replay with Range support. The browser stores only its own opaque session IDs; new private replay endpoints require a matching local-owner cookie and capture consent. This is a local prototype privacy boundary, not account authentication. Recordings made before the owner cookie cannot be opened by the new library.
- Extract an expert-named object from English, Japanese, or Mandarin speech without requiring a fixed detector class. The label is always `expert_speech`, `unreviewed`. A nearby on-device object is only a suggested match. If none exists, one consented, budget-reserved live SAM concept request can suggest a box. If it finds no credible box or is unavailable, ask for a closer or different view and allow the expert to tap the item. Point and box cues carry their actual capture times. None of these establishes depth or a durable identity across frames.
- Keep a distinct Robot dataset section. A separately granted `training` permission enables a private ZIP with original video, tracking samples, expert labels, and notes. Its manifest explicitly has `robot_state: null` and `robot_action: null`; action-policy readiness remains false. No training job or public release is started.

## Verification boundary

Mock/unit, local FFmpeg, and Chromium checks exercise the persistence race, Range streaming, upload completion, remux duration, label localization contract, privacy gate, responsive preview mapping, and UI tabs. The owner's prior 56-chunk iPhone VP9/Opus stream was copy-remuxed in a temporary local probe and yielded a readable 111.067-second WebM. That does not prove the new replay works in Safari. Device playback, speaker/ASR coexistence, arbitrary small-object segmentation quality, 9:16 sensor selection, and tracking persistence over occlusion remain **NOT_RUN** after this change. No paid provider call was made by Codex while implementing it.

Affected requirements: FR-01, FR-02, FR-04, FR-05, FR-07, FR-08, FR-11, FR-17, FR-18, FR-19, FR-25, FR-26; V-CAP-01/02/04 and the separate robot-learning evidence gate. Implementation alone does not pass the real-device or robot-training acceptance cases.
