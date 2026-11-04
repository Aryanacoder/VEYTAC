# Decision 0005 — live observation contract and same-IP HTTPS (2026-11-04)

Owner reported a real provider HTTP 400 on `/frames` (strict schema `required`
error), no object detection or questions, and no phone/iPad access on WiFi.

1. The previous strict-schema normalization is retained. The provider now
   receives only `ObservationInference`: description, visible object labels,
   tentative action, uncertainty, and unavailable cues. The server creates
   IDs, timestamps, model metadata, and the frame evidence reference. This
   avoids requiring the model to invent server-owned values and lets the
   validated observation ground a question. Health exposes the contract
   version so a stale backend process is detectable. No mock result is
   substituted for a provider failure.
2. On-device hand/object inference errors are surfaced instead of silently
   reporting zero boxes; timed model observations remain the fallback. The
   active screen distinguishes an unreviewed live model description from a
   mock observation. A zero count means no *supported* objects were detected
   in that frame, not proof that the scene contains none. The bundled generic
   EfficientDet detector does not establish industrial-tool coverage.
3. The old `npm run dev:https` command failed under Vite 5 (`--https` is not
   a CLI option). LAN mode now reads a generated certificate in Vite config.
   `cert:lan` creates a certificate with the current WiFi IP in its SAN and a
   local CA whose private key is discarded. The public CA must be installed
   and explicitly trusted on iPhone/iPad. The API remains on loopback; Vite
   proxies HTTP and WebSocket traffic. The certificate directory is ignored
   by Git.
4. The recorder now chooses a supported WebM or MP4 MIME type before capture
   and records it in stream metadata. This removes the WebM-only assumption
   for Safari; actual iPhone/iPad capture and chunk upload remain device tests.

Requirement focus: FR-01, FR-02, FR-06, FR-11, FR-24, FR-28, NFR-01.
Offline tests and local HTTPS/health checks are evidence of code and routing,
not a successful paid Meta observation, actual iOS trust installation, or
industrial object recognition. Those remain separate live gates.
