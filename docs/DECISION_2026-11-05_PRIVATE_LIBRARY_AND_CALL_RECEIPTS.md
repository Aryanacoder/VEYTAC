# Private library and model-call receipts — 2026-11-05

## Decision

Replace session-ID-first navigation with an owner-cookie-scoped recording list. The opaque session ID remains an internal API key. The Library can finalize contiguous previously uploaded chunks, download original video, and export a private evidence backup. Users may import an MP4 or WebM with explicit permission to store it privately; import does not grant provider processing or training rights.

The live demo may opt into a model-call panel. Store and return only call kind, provider, model, running/completed/error status, timestamps, latency, numeric usage, and estimated cost. No prompt, raw model response, frame, audio, provider error body, or credential is stored in these receipts. An estimated cost is labeled as such and may differ from billing.

## Contracts and limits

- `GET /api/v1/library/recordings` lists only sessions with this browser's owner cookie; at most the newest 100 sessions are inspected. It is not account sync across devices.
- `POST /api/v1/library/import` accepts one MP4/WebM up to 150 MB with `capture_permission=true`. It creates a private replay session.
- `POST /api/v1/library/import-backup` restores a VEYTAC private ZIP as a new replay session. Entity IDs are remapped; decisions, labels, and observations are marked unreviewed or imported. Processing and training permissions are not inherited.
- `GET /api/v1/sessions/{id}/backup/download` streams a private ZIP with the concatenated recording, hashes, and selected source-linked JSON. It is an owner backup, not a public or training-ready export.
- `GET /api/v1/sessions/{id}/model-calls` is owner-cookie gated and returns metadata only. The UI polls this endpoint only while capture is active and the checkbox is on. The checkbox controls display, not whether budgeted inference occurs.
- The recording-finalization request no longer waits for successful tracking upload. Tracking upload failure is reported separately.

## Open questions

Account-backed cross-device access, actual provider billing reconciliation for SAM/voice, and on-device Safari verification remain separate gates. The phone capture cannot be labeled robot action data.
