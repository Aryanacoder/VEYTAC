# VEYTAC

**Observe the work. Preserve the why.**

VEYTAC is a prototype for capturing expert judgment during permitted work. Its browser app records camera or screen input, asks spoken questions when a decision needs context, and keeps the expert's answer tied to the evidence. Review and dataset gates separate proposed knowledge from approved material.

We are building industrial apprenticeship infrastructure: AI that learns alongside experts so their knowledge can train the next generation of people and machines.

## Run locally

Requires Python 3.11, Node.js, npm, and optionally FFmpeg for seekable recording derivatives.

```powershell
python -m pip install -e '.[dev]'
Copy-Item .env.example .env
python -m veytac.cli doctor
python -m veytac.cli serve --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
Set-Location apps/web
npm ci
python ../../scripts/setup_vision_assets.py
npm run dev
```

Open the URL printed by Vite. `.env.example` defaults to mock mode. Live Meta inference requires a personal key, separate processing consent, and explicit paid-call settings. Do not put a key in browser code or commit `.env`.

For iPhone/iPad access on the same WiFi, follow the [HTTPS LAN setup](docs/HOSTING.md). Camera and microphone capture require a trusted secure origin. The backend stays bound to loopback; Vite proxies API traffic.

## Check the build

```powershell
python -m pytest tests/unit -q
Set-Location apps/web
npm run build
npm run test:perceive
npx playwright test
```

Browser tests use deterministic API fixtures. They do not prove a real provider or phone session. See [verification](VERIFICATION.md) and the [demo script](docs/DEMO_VIDEO_3_MIN_2026-11-05.md) for the next evidence checks.

## Data and safety boundaries

Record only material you have permission to capture. Recording permission does not grant training or publication rights. Imported backup approvals require fresh review. Phone and screen captures are observation data; robot policy training requires aligned robot state, actions, and calibration. No live machinery or robot actuation is included.

Project context: [start here](START_HERE.md) · [requirements](PRD.md) · [technical contract](TRD.md) · [agent guidance](AGENTS.md).
