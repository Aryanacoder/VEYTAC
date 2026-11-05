# Contributing to VEYTAC

Thanks for helping build an open foundation for capturing and transferring expert knowledge.

**Scope:** contribute to the phone/screen capture loop, evidence-linked decision records, multilingual dialogue, privacy and rights controls, dataset validation, interactive lessons, and controlled learning evaluations. Avoid claiming that vision models can infer hidden forces or reconstruct arbitrary physical simulation from video.

## Getting started

Read [START_HERE.md](START_HERE.md), [PRD.md](PRD.md), [TRD.md](TRD.md), [AGENTS.md](AGENTS.md) and [VERIFICATION.md](VERIFICATION.md) before major changes.

The mock mode runs without paid model access:

~~~powershell
python -m pip install -e '.[dev]'
Copy-Item .env.example .env
python -m veytac.cli doctor
python -m pytest tests/ -q
~~~

In `apps/web`:

~~~bash
npm ci
npm run build
npm run test:perceive
~~~

Run Playwright E2E tests on a device/CI environment that supports browser processes. Use the [LAN guide](docs/HOSTING.md) for phone capture.

## Pull requests

Describe the problem, the changed files, any data/schema migrations, affected privacy/consent gates, and exact tests run. Include clear screenshots or recordings **only when they are your own or you have explicit publication rights**. Use a separate branch or worktree when collaborating with Codex and Muse Code.

**No paid calls, cloud jobs, training runs, or public uploads without approval.** Keep secrets and local recordings out of commits.

## Data contributions

Every recording needs specific permissions for capture, third-party processing, training, and publication. Rights are **default deny**. A public YouTube video, scientific dataset, or proprietary engineering drawing is not automatically a reusable training source.

Mark each annotation as observed, expert-reported, model-inferred, or independently tested. Keep human corrections and original languages. Never fill missing robot states/actions, forces, timing or calibration with invented values.

Use [the dataset checklist](docs/DEMO_DATASET_CHECKLIST.md) and [robot evaluation rules](LEARNING_AND_ROBOT_EVALUATION.md).

## Project license

The code is publicly visible, but a project-level license has not yet been selected. Please do not assume that public visibility grants permission to copy or redistribute it. A license choice is a maintainer decision.

## Good first contributions

Improve a test that detects a false claim, add a deterministic example of a corrected expert decision, improve a reusable provider mock, or document a reproducible mobile capture failure. These are more valuable than adding unsupported models or superficial interfaces.
