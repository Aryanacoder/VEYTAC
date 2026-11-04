# Decision 0004 — live 502 root cause + detection overlay (2026-11-04)

Owner report with screenshot: live frames failed with HTTP 502 —
`live observation failed (provider HTTP 400: 'required' is required to
be supplied ... Missing 'cand...')`. Same session requested colored live
detectors (humans blue, objects red, motion trails) for higher-quality
data generation.

1. Root cause: the Meta chat API with `strict: True` rejects
   Pydantic-style JSON schemas — every object must list `required`
   containing every property key, `$ref`/`$defs` are not resolved, and
   constraining keywords are unsupported. Our schemas had all three
   violations. New `src/veytac/providers/strict.py` (`to_strict_schema`)
   inlines refs, completes `required`, forces
   `additionalProperties: false`, and strips unsupported keywords, applied
   at the single choke point (`LiveMetaClient`) for both observe and
   propose. Proven structurally (`tests/unit/test_strict_schema.py`:
   raw schemas fail the audit, transformed pass); a live paid re-run on
   the owner's machine is still the closing proof.
2. Detection overlay (`apps/web/src/perceive/overlay.ts`): blue boxes for
   persons/hands, red for all other objects, fading motion trails
   (suppressed under `prefers-reduced-motion`), aligned through the video
   element's center-crop, with a color legend. Tracks persist briefly
   through occlusion. Per-frame box persistence in the database was
   deferred (bloat vs value); triggers already record what changed.
3. Motion energy: frame-diff pixel energy per analyzed frame feeds a new
   `motion_burst` track event (rising edge), so waves, carried objects,
   and body movement trigger model frames even when labels are static.

Requirement IDs affected: FR-02, FR-06, FR-09. Evidence: backend 53
passed/2 skipped; perceive 10/10; typecheck clean; jsdom smoke PASS
(rewritten for the current live UI after the 11-03 rework). Live-provider
proof of the schema fix and on-device overlay rendering remain
owner-machine runs.
