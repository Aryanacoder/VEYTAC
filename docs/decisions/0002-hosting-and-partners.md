# Decision 0002 — rehearsal hardware, self-hosting, partner budgets (2026-10-31)

Owner direction (chat, 2026-10-31):

1. Rehearsal uses this PC's camera/microphone for capture and Q&A
   (no phone required for the rehearsal loop). Phone joins later as a
   remote capture client over the same session API.
2. Live demo hosting: the app runs on the owner's own HTTP server; phones
   connect over the local network. Assumption: "tailwind" means **Tailscale**
   (mesh VPN) — to be confirmed; the runbook covers plain-LAN and Tailscale
   paths. Browsers require a secure context for camera/mic, so remote
   clients need HTTPS (Tailscale serves valid certs for tailnet names) or
   `localhost` on the host itself.
3. Open-source self-host: anyone can run the stack on their own WiFi.
   Consequence: setup must stay `pip install` + `npm install` + one `.env`,
   no cloud dependency for the core loop (mock mode works fully offline
   except CDN-free static serving; vite dev for contributors).
4. Partner budgets: **no limit** stated for Muse Glimmer LoRA training
   (Fireworks) and for other-model inference/training (Baseten).
   This lifts the $0-until-verified cap for those two lanes only; the $150
   Meta envelope and $30 protected demo reserve still hold. Each real
   training launch is still recorded as an ExperimentRun with config hash,
   data hash, and cost — unlimited does not mean unlogged.

Requirement IDs affected: FR-02, FR-03, FR-22, FR-23, NFR-03.
Resolved 2026-11-01: owner confirmed Tailscale. Runbook stands as written.
