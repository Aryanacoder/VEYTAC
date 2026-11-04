# Muse Code follow-up: iPhone replay, object grounding, and dataset evidence

## What changed

Codex changed the live video and overlay to show the whole frame, repaired stale session writes that erased a spoken task brief, added private recording replay and time-aligned tracking samples, and added spoken expert object labels. A label absent from the on-device classes can receive one budgeted SAM concept localization attempt; a result is explicitly a suggested region. Failure asks the expert for another view or a tap. The new library has Video library and Robot dataset sections. The dataset is observation-only and blocks robot action-policy claims.

The last pre-change iPhone Safari session was `ses_[redacted]`: 56 chunks, first video chunk 1280×720, 13 proposed observations, and diagnostics showing TTS and ASR final. Task brief and answered records were missing at rest because of a session write race. This is diagnostic evidence, not a passing interview or robot dataset. Older sessions lack the private owner cookie and are not shown in the new replay library.

## Next device run

1. Restart the backend so the new router and SQLite session mutation code load. On the same Wi-Fi HTTPS origin, refresh iPhone Safari. Start a short consented session, speak the task brief, then say “This is a screw” while showing it. Check that the entire camera field is visible, the heard answer and proposed follow-up remain in the transcript, and the label says whether it is unlocalized, suggested, or expert pointed. Tap the object if needed. Try Japanese in a separate consented session.
2. Stop. Confirm camera preview remains live while recording ends. Open Video library; play, seek, and rotate the phone. Check audio, actual duration, saved boxes/hand points, and any point or SAM cue at the correct time. If it fails, record the session ID and sanitized browser/backend error, plus video codec and dimensions via `ffprobe`. Do not paste raw video, transcripts, or keys into an issue.
3. In Robot dataset, confirm action-policy training is blocked and the missing fields are named. Only if the owner separately approves private training use for that session, download the observation ZIP and inspect its manifest. Do not start training or call it robot-ready. Publication still needs its own permission and gate.
4. Validate with a pen, screw, and iPad under good and poor framing. Record whether on-device detection, SAM concept candidate, expert tap, or a request for another angle handled each case. A SAM box from one frame is not a persistent object track or measured depth. If the result is empty or wrong, retain that negative result and inspect provider response under the approved cost cap before changing prompts.

## Open engineering work

- The phone's concatenated raw WebM had no duration metadata. A temporary FFmpeg stream-copy probe yielded a 111.067-second seekable derivative, and completion now generates that derivative. Real Safari playback of it and real 9:16 versus 16:9 sensor behavior need a device result. Preserve raw chunks and explicit timing gaps; measure any overlay drift against media timestamps.
- A local-owner cookie is not account authentication. Add an owner and reviewer authorization model before multi-user or production access; plan a consented migration path for older recordings.
- Expert point and SAM box are short-lived visual cues. Evaluate open-vocabulary localization and temporal association on owned, reviewed examples before claiming arbitrary object tracking. Keep review state and failure cases visible.
- Align replay overlays to actual media timestamps and discontinuities, not just elapsed wall time, under V-CAP-04. The current samples use `recording_elapsed` and may drift after Safari pauses or delayed chunks.
