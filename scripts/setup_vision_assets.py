"""Install public MediaPipe runtime assets locally for LAN/browser tracking.

The source models are downloaded to a Git-ignored directory. Their license and
redistribution terms must be reviewed before packaging them in a public build.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
DEST = WEB / "public" / "vision"
WASM_SOURCE = WEB / "node_modules" / "@mediapipe" / "tasks-vision" / "wasm"
RUNTIME_BUNDLE = WASM_SOURCE.parent / "vision_bundle.cjs"
WASM_FILES = (
    "vision_wasm_internal.js",
    "vision_wasm_internal.wasm",
    "vision_wasm_nosimd_internal.js",
    "vision_wasm_nosimd_internal.wasm",
)
MODELS = {
    "hand_landmarker.task": (
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
        "hand_landmarker/float16/1/hand_landmarker.task"
    ),
    "efficientdet_lite0.tflite": (
        "https://storage.googleapis.com/mediapipe-models/object_detector/"
        "efficientdet_lite0/int8/1/efficientdet_lite0.tflite"
    ),
}
MODEL_SHA256 = {
    "hand_landmarker.task": "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1",
    "efficientdet_lite0.tflite": "0720bf247bd76e6594ea28fa9c6f7c5242be774818997dbbeffc4da460c723bb",
}
MAX_MODEL_BYTES = 32 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def install() -> None:
    if not WASM_SOURCE.is_dir():
        raise SystemExit("Install apps/web npm dependencies before vision assets.")
    DEST.mkdir(parents=True, exist_ok=True)
    bundle_target = DEST / "vision_bundle_classic.js"
    if not RUNTIME_BUNDLE.is_file():
        raise SystemExit("Missing pinned MediaPipe runtime bundle")
    if not bundle_target.is_file() or sha256(bundle_target) != sha256(RUNTIME_BUNDLE):
        shutil.copyfile(RUNTIME_BUNDLE, bundle_target)
    print(f"{bundle_target.relative_to(ROOT)} {sha256(bundle_target)}")
    wasm_dest = DEST / "wasm"
    wasm_dest.mkdir(parents=True, exist_ok=True)
    for name in WASM_FILES:
        source = WASM_SOURCE / name
        if not source.is_file():
            raise SystemExit(f"Missing pinned MediaPipe runtime file: {name}")
        target = wasm_dest / name
        if not target.is_file() or sha256(target) != sha256(source):
            shutil.copyfile(source, target)
        print(f"{target.relative_to(ROOT)} {sha256(target)}")
    for name, url in MODELS.items():
        target = DEST / name
        if not target.is_file() or sha256(target) != MODEL_SHA256[name]:
            temporary = DEST / f"{name}.download"
            try:
                size = 0
                with urlopen(url, timeout=30) as response, temporary.open("wb") as output:
                    while chunk := response.read(1024 * 1024):
                        size += len(chunk)
                        if size > MAX_MODEL_BYTES:
                            raise ValueError(f"Model exceeds {MAX_MODEL_BYTES} byte limit")
                        output.write(chunk)
                if sha256(temporary) != MODEL_SHA256[name]:
                    raise ValueError(f"Downloaded model checksum mismatch: {name}")
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
        print(f"{target.relative_to(ROOT)} {sha256(target)}")


if __name__ == "__main__":
    install()
