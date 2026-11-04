# Decision 0001 — MVP scope and resource placement (2026-10-30)

Owner direction (chat, 2026-10-30):

1. Live demo: the expert answers the system's questions live during a real
   task demonstration (factory/human task, or PC screen-share such as
   CAD-to-SCADA). No prerecorded stand-in for the live claim.
2. $150 Meta credits cover coding use plus Meta API use (SAM, smart models).
   Inference/training overflow goes to partner credits
   (Baseten / Fireworks / Modal) via API, never silently.
3. Language support follows tested Meta + open-model capability, not a fixed list.
   English/Japanese first per PRD FR-05; others only after a real smoke test.
4. Build order: core MVP (M1–M4) first, then stage 2 (robot/SFT, M5).
   The final demo contains both; stage 2 stays `ROBOT_LEARNING_NOT_DEMONSTRATED`
   until its gates pass.
5. Headless browser testing: Playwright + Chromium (Lightpanda dropped;
   `brew` is unavailable on the Windows build machine).
6. UI: Meta-like font/colour grading, animated transitions; blue full-screen
   sweep when the AI asks, red sweep when the expert answers; side-by-side
   live transcription; post-stream dataset + simulation-lesson generation
   visible in the same demo flow.
7. Latency: verifier/evaluation layers at critical points (observation
   validation, question grounding, record construction) to block hallucinations.
8. Every live stream is recorded and saved, not only sampled.
9. Agent is authorized to edit spec docs; changes are logged here.

Consequences: TRD/GOALS unchanged in normative content; this note records
owner-approved scope and placement choices only.
Requirement IDs affected: FR-02, FR-03, FR-05, FR-09–FR-12, FR-18, FR-22,
FR-23, NFR-03.
