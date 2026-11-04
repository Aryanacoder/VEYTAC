# Decision 0005 — SAM 3.1 live segmentation lane (2026-11-04)

Owner direction (chat, 2026-11-04): use SAM 3 capabilities to detect and
highlight every object in real time as the video starts, tracking all
movements — not just humans. Verified first against the Meta docs
(media-segmentation, sam/segmenting, reading-segmentation,
client-libraries, 2026-11-04): `sam-3.1` over the Responses API
(`POST {base}/responses`, Bearer header, SSE stream), one concept noun
phrase OR box/point grammar per request (never both; comma lists match
nothing), one `output_text` lane with `<Nf>id<|box;...|><|mask;...|>`
lines, stable object ids within a response, empty output = zero matches
(valid). Official packages: `@meta-sam/parser` (TS) and
`meta-sam-parser` 0.1.0 (Python, API surface inspected from the wheel).

1. Honest real-time architecture — three tiers, not one magic call.
   A per-frame SAM round-trip takes seconds and is billed per call, so
   true 30fps server masks are not feasible on any connection. Tier 1
   (free, 4fps, on-device): boxes, hand-skeleton dots, trails, motion
   bursts. Tier 2 (paid, event frames only): SAM refines whatever Tier 1
   points at via box prompts (one request covers all boxes) and returns
   precise boxes with stable ids + mask payloads. Tier 3 (next): clip +
   box prompt for SAM video tracking across frames.
2. Coverage rule: SAM segments what it is pointed at. Box prompts come
   from live tracks, so every tracked object gets a mask; concept mode
   (one request per noun phrase) is reserved, not the default, to bound
   spend. "Every object" = every tracked object, stated in the UI by
   showing SAM boxes distinctly (thicker + id badge).
3. Server (`src/veytac/providers/sam.py`, `meta-sam-parser>=0.1`
   declared): concept validation refuses lists unpaid; local grammar
   builder/parser implement the documented ABNF exactly (doc fixtures as
   tests); mask decode uses the official parser when installed, opaque
   payload otherwise — never an invented codec. Frame flow attaches
   masks as derived evidence (frame index + coordinates, TRD 7.5) with
   budget reserve/reconcile; enrichment never blocks the observation.
4. Client sends tracked boxes + frame pixels with each event frame and
   draws SAM boxes (cover-crop-aligned, blue person/hand, red object).
   SVG fills wait on verifying mask-raster placement against the first
   live run — boxes are exact, fills are not shipped on a guess.
5. First live run still required: exact `metadata.mask_encoding` /
   `include_confidence` keys, data-URL media acceptance, and per-call
   cost are flagged VERIFY-ON-FIRST-RUN; failures are stored, not hidden.

Requirement IDs affected: FR-02, FR-06, FR-07, FR-16. Evidence: backend
66 passed/2 skipped (incl. 9 SAM grammar/parse + mock-shape tests);
perceive 11/11; typecheck clean; jsdom smoke PASS. Live SAM call,
mask-fill rendering, and video tracking remain owner-machine runs.
