# Decision 0003 — live perception + voice loop (2026-10-31)

Owner direction (chat, 2026-10-31): the rehearsal must be fully live and
fully voice. No typed answers as the primary path. The system must see
what the expert holds (hands, objects, POV, screen) and ask proactively.
Explicitly offered: Glimmer training via Fireworks + open datasets if
required. Owner decisions on all three scoping questions: on-device
browser detection, Meta live ASR relay, no training yet.

1. Perception is two-tier. Tier 1 (always on, free): MediaPipe
   Tasks-Vision 0.10.20 in the browser (HandLandmarker + EfficientDet-Lite0,
   ~5fps @320px) emits change events only (held_object_new/gone,
   object_new, hands_changed, scene_changed). Tier 2 (paid, rare): frames
   POST only on events with a `trigger` string preserved on the
   observation. A steady scene costs zero model calls.
2. Model bundles (~12MB: 7.8MB hand + 4.6MB detector, URLs verified 200
   on 2026-10-31) download once at first use from pinned Google CDN URLs.
   New external-fetch disclosure in HOSTING.md. Unavailable library/models
   report NullTracker — never faked detections.
3. Voice transport is the Meta realtime relay `wss://api.meta.ai/v1/asr/
   realtime` (S04): handshake-first-frame auth (key server-side only),
   16-bit mono PCM @24kHz binary frames ~80ms, ENDPOINTING mode for
   hands-free turns. Server normalizes to partial/final/speaker/boundary/
   error; only speechComplete finals are preserved (partials ephemeral,
   late finals flagged per TRD 7.4). Browser Web Speech stays fallback;
   TTS barge-in yields when the expert talks.
4. No model training in this slice. Off-the-shelf detection covers
   hands/held-objects; training without in-domain labeled sessions would
   burn budget. Glimmer LoRA via Fireworks stays a stage-2 option with
   real sessions as data. No datasets downloaded.
5. New npm runtime dep `@mediapipe/tasks-vision` (owner runs `npm install`
   on a dev machine; sandbox npm is blocked). New pip dep `websockets`
   (already present via uvicorn[standard], now declared directly).

Requirement IDs affected: FR-02, FR-03, FR-06, FR-09, FR-10, FR-12.
Evidence: backend 44 passed/2 skipped; perceive 5/5; typecheck clean;
jsdom smoke PASS. Live relay + on-device tracking are NOT_RUN here
(sandbox blocks sockets/browser) — first live run is the owner's
rehearsal with key + `npm install`.
