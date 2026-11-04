# Start here

VEYTAC is an industrial apprenticeship prototype. It records permitted expert work, asks for missing decision context, keeps answers with the original evidence, and supports human review before lessons or research exports. The app has a React/TypeScript web client, a FastAPI backend, SQLite storage, offline mocks, and an opt-in Meta inference path.

## Read the project

1. [README](README.md) — run the current prototype.
2. [AGENTS.md](AGENTS.md) — coding, permission, and claim boundaries.
3. [PRD.md](PRD.md) — product requirements and user journeys.
4. [TRD.md](TRD.md) — architecture and contracts. It contains target interfaces; check current code before relying on a command.
5. [GOALS.md](GOALS.md) — milestones and demo scope.
6. [VERIFICATION.md](VERIFICATION.md), [acceptance tests](ACCEPTANCE_TESTS.md), and [learning evaluation](LEARNING_AND_ROBOT_EVALUATION.md) — evidence gates.
7. [Implementation status](docs/IMPLEMENTATION_STATUS.md) and dated [decision notes](docs/decisions/) — chronological implementation record. Older entries may be superseded by newer code and tests.

## Current limits

This repository contains executable code and tests. A local mock run is not a real-provider result. Public source does not include API keys, recordings, customer data, local model binaries, or a production authentication system. Phone video supplies visual and spoken observations; it does not supply robot state or actions. Review [verification](VERIFICATION.md) before making a release or performance claim.
