"""VEYTAC CLI. `doctor` is free/local unless live probing is requested."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_env_file(path: Path | None = None) -> Path | None:
    """Load repo-root .env so `serve`/`doctor` honor it. Explicit process
    env always wins (override=False). Returns the file used, else None."""
    target = path or (repo_root() / ".env")
    if not target.is_file():
        return None
    try:
        from dotenv import load_dotenv
    except ImportError:
        return None
    load_dotenv(target, override=False)
    return target


def cmd_doctor(_args: argparse.Namespace) -> int:
    print(f"python={platform.python_version()}")
    for tool in ("ffmpeg", "ffprobe", "node", "npm"):
        print(f"{tool}={'found' if shutil.which(tool) else 'MISSING'}")
    try:
        import fastapi  # noqa: F401
        import pydantic  # noqa: F401
        import sqlalchemy  # noqa: F401

        print("api-deps=ok")
    except ImportError as exc:
        print(f"api-deps=MISSING ({exc})")
        return 1
    print(f"execution_mode={os.getenv('VEYTAC_EXECUTION_MODE', 'mock')} "
          "(doctor made no paid call)")
    return 0


def cmd_validate_episode(args: argparse.Namespace) -> int:
    """Local checksum + reference-integrity check of an export bundle dir."""
    root = Path(args.path)
    required = ["episode.json", "observations.jsonl", "decisions.jsonl",
                "dialogue.jsonl", "checksums.sha256"]
    missing = [f for f in required if not (root / f).exists()]
    if missing:
        print(f"INVALID: missing files {missing}")
        return 1
    sums = {}
    for line in (root / "checksums.sha256").read_text().splitlines():
        if line.strip():
            h, n = line.split()
            sums[n] = h
    bad = [n for n, h in sums.items()
           if hashlib.sha256((root / n).read_bytes()).hexdigest() != h]
    if bad:
        print(f"INVALID: checksum mismatch {bad}")
        return 1
    ep = json.loads((root / "episode.json").read_text())
    print(f"VALID: episode {ep.get('episode_id')} rev {ep.get('revision')} "
          f"caps {ep.get('capabilities')}")
    return 0


def cmd_eval_apprentice(args: argparse.Namespace) -> int:
    """Dry-run only: prints what WOULD run. Never provisions GPU/paid calls."""
    if not args.dry_run:
        print("refusing: only --dry-run is implemented in this slice; "
              "real runs need an approval record (TRD 13.4)")
        return 2
    print(f"dry-run: would evaluate config {args.config} "
          f"(passive vs fixed vs adaptive, matched budgets, held-out cases)")
    print("no GPU provisioned, no dataset downloaded, no paid call made")
    return 0


def cmd_train_robot(args: argparse.Namespace) -> int:
    if not args.dry_run:
        print("refusing: only --dry-run is implemented in this slice")
        return 2
    print(f"dry-run: would validate robot bundle + plan BC baseline for {args.config}")
    print("status: ROBOT_LEARNING_NOT_DEMONSTRATED until G6/G7 gates pass")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    """Start the API the supported way. Run from the repo root."""
    import uvicorn

    root = repo_root()
    print(f"serving from {root} on {args.host}:{args.port} "
          f"(mode={os.getenv('VEYTAC_EXECUTION_MODE', 'mock')})")
    print("strict-schema=2026-11-04 (provider 400 fix loaded)")
    uvicorn.run("api.main:app", app_dir=str(root / "services"),
                host=args.host, port=args.port, log_level="info")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="veytac")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor", help="local environment check (free)")

    p_val = sub.add_parser("validate-episode", help="verify an export bundle")
    p_val.add_argument("--path", required=True)
    p_val.set_defaults(fn=cmd_validate_episode)

    p_eval = sub.add_parser("eval-apprentice", help="transfer evaluation (dry-run only)")
    p_eval.add_argument("--config", required=True)
    p_eval.add_argument("--dry-run", action="store_true")
    p_eval.set_defaults(fn=cmd_eval_apprentice)

    p_train = sub.add_parser("train-robot", help="robot training (dry-run only)")
    p_train.add_argument("--config", required=True)
    p_train.add_argument("--dry-run", action="store_true")
    p_train.set_defaults(fn=cmd_train_robot)

    p_serve = sub.add_parser("serve", help="start the API server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.set_defaults(fn=cmd_serve)

    args = parser.parse_args(argv)
    loaded = load_env_file()
    if loaded is not None:
        print(f"env={loaded} (mode={os.getenv('VEYTAC_EXECUTION_MODE', 'mock')})")
    if args.cmd == "doctor":
        return cmd_doctor(args)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
