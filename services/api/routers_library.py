"""Private-session recording replay and source-linked visual annotations.

This local prototype addresses a recording by its opaque session ID. It does
not list other owners' media or publish a capture. Account authentication is
still a separate release gate.
"""

from __future__ import annotations

import re
import json
import io
import shutil
import tempfile
import hashlib
import hmac
import subprocess
import secrets
from pathlib import Path
from typing import Literal
from zipfile import ZIP_STORED, BadZipFile, ZipFile

from fastapi import APIRouter, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator

from veytac.schemas import Principal, Role, make_id, new_session, utcnow_iso

from .db import get_session, insert_session, list_entities, put_entity, reserve_session_call, reconcile_session_call
from .deps import db
from .routers_capture import _live_enabled, storage_root

router = APIRouter()


def _session(session_id: str, request: Request) -> dict:
    payload = get_session(db(), session_id)
    if payload is None:
        raise HTTPException(404, "session not found")
    token = request.cookies.get("veytac_local_owner")
    expected = payload.get("owner_cookie_hash")
    if not token or not expected or not hmac.compare_digest(
        hashlib.sha256(token.encode()).hexdigest(), expected
    ):
        raise HTTPException(403, "recording belongs to another browser or predates private library access")
    if not payload.get("capture_granted"):
        raise HTTPException(403, "capture consent required")
    return payload


def _stream_and_parts(session_id: str) -> tuple[dict, list[tuple[int, Path, int]]]:
    streams = list_entities(db(), "stream", session_id)
    if not streams:
        raise HTTPException(404, "recording stream not found")
    stream = streams[-1]
    rows = db().execute(
        "SELECT sequence_no,locator,size_bytes FROM chunks "
        "WHERE session_id=? AND stream_id=? AND epoch_id=? ORDER BY sequence_no",
        (session_id, stream["id"], stream["epoch_id"]),
    ).fetchall()
    if not rows:
        raise HTTPException(404, "recording chunks not found")
    root = storage_root().resolve()
    parts: list[tuple[int, Path, int]] = []
    for expected, (seq, locator, size) in enumerate(rows):
        if seq != expected:
            raise HTTPException(409, "recording has a missing chunk")
        path = Path(locator).resolve()
        if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size != size:
            raise HTTPException(409, "recording chunk is missing or outside storage")
        parts.append((seq, path, size))
    return stream, parts


def _recording_info(session_id: str) -> dict:
    stream, parts = _stream_and_parts(session_id)
    manifests = list_entities(db(), "recording_manifest", session_id)
    manifest = next((m for m in manifests if m["stream_id"] == stream["id"]), None)
    complete = bool(manifest and manifest["chunk_count"] == len(parts))
    return {
        "session_id": session_id, "stream_id": stream["id"],
        "source_type": stream.get("source_type", "unknown"),
        "mime": stream.get("codec") or "video/webm",
        "chunk_count": len(parts), "size_bytes": sum(size for _, _, size in parts),
        "complete": complete,
        "replay_duration_ms": manifest.get("replay_duration_ms") if manifest else None,
        "seekable": bool(manifest and manifest.get("replay_locator")),
        "tracking_samples": sum(len(b.get("samples", [])) for b in
                                list_entities(db(), "track_batch", session_id)),
        "object_labels": len(list_entities(db(), "object_label", session_id)),
    }


BACKUP_KINDS = ("asset", "observation", "gap", "question", "turn", "decision",
                "expert_note", "object_label", "track_batch", "mask", "chunk_timing")


@router.get("/api/v1/library/recordings")
def owned_recordings(request: Request) -> dict:
    """Discover this browser's captures; opaque IDs stay an internal key."""
    token = request.cookies.get("veytac_local_owner")
    if not token:
        return {"recordings": []}
    owner_hash = hashlib.sha256(token.encode()).hexdigest()
    rows = db().execute("SELECT id,payload FROM sessions ORDER BY rowid DESC LIMIT 100").fetchall()
    found = []
    for session_id, raw in rows:
        payload = json.loads(raw)
        if not payload.get("capture_granted") or not hmac.compare_digest(
            str(payload.get("owner_cookie_hash") or ""), owner_hash
        ):
            continue
        streams = list_entities(db(), "stream", session_id)
        if not streams:
            continue
        try:
            info = _recording_info(session_id)
        except HTTPException:
            info = {"chunk_count": 0, "size_bytes": 0, "complete": False,
                    "source_type": streams[-1].get("source_type", "unknown"),
                    "replay_duration_ms": None}
        found.append({"id": session_id, "created_at": payload.get("created_at"),
                      "title": str(payload.get("task_brief") or "Work recording")[:90],
                      "source_type": info["source_type"],
                      "chunk_count": info["chunk_count"],
                      "size_bytes": info["size_bytes"],
                      "complete": info["complete"],
                      "duration_ms": info.get("replay_duration_ms")})
    return {"recordings": found}


@router.get("/api/v1/sessions/{session_id}/model-calls")
def get_model_calls(session_id: str, request: Request) -> dict:
    """Private call metadata for an explicitly enabled demo panel."""
    _session(session_id, request)
    receipts = sorted(list_entities(db(), "model_call", session_id),
                      key=lambda item: item.get("started_at", ""), reverse=True)[:30]
    allowed = ("id", "kind", "provider", "model", "status", "started_at",
               "finished_at", "latency_ms", "usage", "estimated_cost_micro",
               "cost_estimate_micro")
    return {"calls": [{key: item.get(key) for key in allowed} for item in receipts]}


@router.post("/api/v1/library/import")
async def import_video(request: Request, response: Response,
                       file: UploadFile = File(...),
                       capture_permission: bool = Form(False)) -> dict:
    """Owner-initiated private video import; no inference or training consent."""
    if not capture_permission:
        raise HTTPException(403, "confirm permission to store this video")
    name = Path(file.filename or "").name
    suffix = Path(name).suffix.lower()
    if suffix not in (".mp4", ".webm"):
        raise HTTPException(415, "import an MP4 or WebM video")
    data = await file.read(150 * 1024 * 1024 + 1)
    await file.close()
    if len(data) > 150 * 1024 * 1024:
        raise HTTPException(413, "video exceeds 150 MB import limit")
    if not data or not (data.startswith(b"\x1aE\xdf\xa3") if suffix == ".webm"
                        else len(data) >= 12 and data[4:8] == b"ftyp"):
        raise HTTPException(415, "file does not have the selected video container")
    owner_token = request.cookies.get("veytac_local_owner") or secrets.token_urlsafe(32)
    owner = Principal(id="usr_owner", workspace_id="ws_demo", role=Role.OWNER,
                      auth_provenance="owner-account-prototype")
    session = new_session(owner, "Imported video", mode="RECORDED_REPLAY")
    insert_session(db(), session.id, {**session.model_dump(),
                                     "owner_cookie_hash": hashlib.sha256(owner_token.encode()).hexdigest(),
                                     "capture_granted": True, "processing_granted": False,
                                     "training_granted": False,
                                     "task_brief": Path(name).stem[:90],
                                     "import_permission_at": utcnow_iso()})
    response.set_cookie("veytac_local_owner", owner_token, httponly=True,
                        samesite="strict", max_age=30 * 24 * 3600, path="/")
    stream_id = make_id("str")
    mime = "video/mp4" if suffix == ".mp4" else "video/webm"
    put_entity(db(), "stream", stream_id, session.id, {
        "id": stream_id, "session_id": session.id, "source_type": "upload",
        "epoch_id": "e0", "clock_id": "imported_media", "codec": mime,
        "status": "complete"})
    root = storage_root() / session.id / stream_id / "e0"
    root.mkdir(parents=True, exist_ok=True)
    locator = root / "0.bin"
    locator.write_bytes(data)
    db().execute("INSERT INTO chunks(session_id,stream_id,epoch_id,sequence_no,sha256,size_bytes,locator) "
                 "VALUES(?,?,?,?,?,?,?)", (session.id, stream_id, "e0", 0,
                 hashlib.sha256(data).hexdigest(), len(data), str(locator)))
    db().commit()
    record = {"id": f"recording_{stream_id}", "stream_id": stream_id,
              "chunk_count": 1, "size_bytes": len(data), "private": True,
              "completed_at": utcnow_iso(), "imported_file_name": name[:120]}
    derived = _derive_playback([(0, locator, len(data))], mime)
    if derived:
        record["replay_locator"], record["replay_duration_ms"] = derived
        record["replay_derivation"] = "ffmpeg_stream_copy"
    put_entity(db(), "recording_manifest", record["id"], session.id, record)
    return {"recording": {"id": session.id, **_recording_info(session.id)}}


@router.post("/api/v1/library/import-backup")
async def import_private_backup(request: Request, response: Response,
                                file: UploadFile = File(...),
                                capture_permission: bool = Form(False)) -> dict:
    """Restore a VEYTAC private backup as a new, unreviewed replay session."""
    if not capture_permission:
        raise HTTPException(403, "confirm permission to store this backup privately")
    if Path(file.filename or "").suffix.lower() != ".zip":
        raise HTTPException(415, "import a VEYTAC backup ZIP")
    packed = await file.read(160 * 1024 * 1024 + 1)
    await file.close()
    if len(packed) > 160 * 1024 * 1024:
        raise HTTPException(413, "backup exceeds 160 MB")
    try:
        with ZipFile(io.BytesIO(packed)) as archive:
            names = set(archive.namelist())
            if len(names) != len(archive.namelist()) or len(names) > 20:
                raise ValueError("unexpected backup entries")
            manifest = json.loads(archive.read("manifest.json"))
            if manifest.get("schema_version") != "veytac-private-backup-v1":
                raise ValueError("unsupported backup schema")
            video_name = manifest.get("video_ref")
            if video_name not in ("recording.mp4", "recording.webm") or video_name not in names:
                raise ValueError("backup recording missing")
            allowed = {"manifest.json", video_name} | {f"{kind}.json" for kind in BACKUP_KINDS}
            if not names.issubset(allowed) or sum(i.file_size for i in archive.infolist()) > 160 * 1024 * 1024:
                raise ValueError("unexpected or oversized backup contents")
            video = archive.read(video_name)
            if not video or not (video.startswith(b"\x1aE\xdf\xa3") if video_name.endswith("webm")
                                else len(video) >= 12 and video[4:8] == b"ftyp"):
                raise ValueError("backup recording has an invalid container")
            records = {kind: json.loads(archive.read(f"{kind}.json"))
                       for kind in BACKUP_KINDS if f"{kind}.json" in names}
            if any(not isinstance(rows, list) or len(rows) > 5000 or
                   any(not isinstance(row, dict) or not isinstance(row.get("id"), str)
                       for row in rows) for rows in records.values()):
                raise ValueError("invalid backup records")
    except (BadZipFile, KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(422, f"invalid VEYTAC backup ({type(exc).__name__})") from exc
    owner_token = request.cookies.get("veytac_local_owner") or secrets.token_urlsafe(32)
    owner = Principal(id="usr_owner", workspace_id="ws_demo", role=Role.OWNER,
                      auth_provenance="owner-account-prototype")
    session = new_session(owner, "Imported backup", mode="RECORDED_REPLAY")
    insert_session(db(), session.id, {**session.model_dump(),
                                     "owner_cookie_hash": hashlib.sha256(owner_token.encode()).hexdigest(),
                                     "capture_granted": True, "processing_granted": False,
                                     "training_granted": False,
                                     "task_brief": str(manifest.get("task_brief") or "Imported backup")[:90],
                                     "backup_source_session_id": str(manifest.get("source_session_id") or "")[:100],
                                     "import_permission_at": utcnow_iso()})
    response.set_cookie("veytac_local_owner", owner_token, httponly=True,
                        samesite="strict", max_age=30 * 24 * 3600, path="/")
    stream_id = make_id("str")
    mime = "video/mp4" if video_name.endswith("mp4") else "video/webm"
    put_entity(db(), "stream", stream_id, session.id, {
        "id": stream_id, "session_id": session.id, "source_type": "backup_import",
        "epoch_id": "e0", "clock_id": "imported_media", "codec": mime,
        "status": "complete"})
    root = storage_root() / session.id / stream_id / "e0"
    root.mkdir(parents=True, exist_ok=True)
    locator = root / "0.bin"
    locator.write_bytes(video)
    db().execute("INSERT INTO chunks(session_id,stream_id,epoch_id,sequence_no,sha256,size_bytes,locator) "
                 "VALUES(?,?,?,?,?,?,?)", (session.id, stream_id, "e0", 0,
                 hashlib.sha256(video).hexdigest(), len(video), str(locator)))
    db().commit()
    id_map = {row["id"]: make_id("imp") for rows in records.values() for row in rows}
    if manifest.get("source_session_id"):
        id_map[str(manifest["source_session_id"])] = session.id

    def remap(value):
        if isinstance(value, dict):
            return {key: remap(item) for key, item in value.items()}
        if isinstance(value, list):
            return [remap(item) for item in value]
        if isinstance(value, str):
            return id_map.get(value, value)
        return value

    for kind, rows in records.items():
        for original in rows:
            row = remap(original)
            row["session_id"] = session.id
            row["imported_unverified"] = True
            if kind == "decision":
                row["review"] = {"state": "unreviewed"}
            elif kind == "object_label":
                row["review_state"] = "unreviewed"
            elif kind == "observation":
                row["execution_mode"] = "imported_unverified"
            put_entity(db(), kind, row["id"], session.id, row)
    record = {"id": f"recording_{stream_id}", "stream_id": stream_id,
              "chunk_count": 1, "size_bytes": len(video), "private": True,
              "completed_at": utcnow_iso(), "imported_backup": True}
    derived = _derive_playback([(0, locator, len(video))], mime)
    if derived:
        record["replay_locator"], record["replay_duration_ms"] = derived
        record["replay_derivation"] = "ffmpeg_stream_copy"
    put_entity(db(), "recording_manifest", record["id"], session.id, record)
    return {"recording": {"id": session.id, **_recording_info(session.id)}}


def _derive_playback(parts: list[tuple[int, Path, int]], mime: str) -> tuple[str, int] | None:
    """Copy-remux MediaRecorder's headerless chunks into a seekable derivative."""
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        return None
    if sum(size for _, _, size in parts) > 512 * 1024 * 1024:
        return None
    suffix = ".mp4" if mime.startswith("video/mp4") else ".webm"
    folder = parts[0][1].parent
    with tempfile.NamedTemporaryFile(dir=folder, suffix=suffix, delete=False) as handle:
        input_path = Path(handle.name)
        for _, part, _ in parts:
            with part.open("rb") as source:
                shutil.copyfileobj(source, handle, 256 * 1024)
    with tempfile.NamedTemporaryFile(dir=folder, suffix=suffix, delete=False) as handle:
        output_path = Path(handle.name)
    target = folder / f"recording-playback{suffix}"
    try:
        command = ["ffmpeg", "-y", "-v", "error", "-i", str(input_path), "-c", "copy"]
        if suffix == ".mp4":
            command += ["-movflags", "+faststart"]
        result = subprocess.run(command + [str(output_path)], capture_output=True,
                                timeout=120, check=False)
        if result.returncode or output_path.stat().st_size == 0:
            return None
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "default=noprint_wrappers=1:nokey=1", str(output_path)],
                               capture_output=True, text=True, timeout=30, check=False)
        duration_ms = round(float(probe.stdout.strip()) * 1000) if probe.returncode == 0 else 0
        if duration_ms <= 0:
            return None
        output_path.replace(target)
        return str(target), duration_ms
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None
    finally:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)


@router.get("/api/v1/sessions/{session_id}/recording/info")
def recording_info(session_id: str, request: Request) -> dict:
    _session(session_id, request)
    return _recording_info(session_id)


class CompleteBody(BaseModel):
    stream_id: str
    epoch_id: str = "e0"
    expected_chunks: int = Field(ge=1, le=10000)


@router.post("/api/v1/sessions/{session_id}/recording/complete")
def complete_recording(session_id: str, body: CompleteBody, request: Request) -> dict:
    _session(session_id, request)
    stream, parts = _stream_and_parts(session_id)
    if (stream["id"] != body.stream_id or stream["epoch_id"] != body.epoch_id
            or len(parts) != body.expected_chunks):
        raise HTTPException(409, "recording uploads are incomplete")
    record = {
        "id": f"recording_{stream['id']}", "stream_id": stream["id"],
        "chunk_count": len(parts), "size_bytes": sum(size for _, _, size in parts),
        "completed_at": utcnow_iso(), "private": True,
    }
    derived = _derive_playback(parts, stream.get("codec") or "video/webm")
    if derived:
        record["replay_locator"], record["replay_duration_ms"] = derived
        record["replay_derivation"] = "ffmpeg_stream_copy"
    put_entity(db(), "recording_manifest", record["id"], session_id, record)
    return {"recording": _recording_info(session_id)}


def _byte_range(header: str | None, total: int) -> tuple[int, int, bool]:
    if not header:
        return 0, total - 1, False
    match = re.fullmatch(r"bytes=(\d*)-(\d*)", header.strip())
    if not match or (not match[1] and not match[2]):
        raise HTTPException(416, "unsupported byte range")
    if not match[1]:
        suffix = int(match[2])
        if suffix <= 0:
            raise HTTPException(416, "invalid byte range")
        return max(0, total - suffix), total - 1, True
    start = int(match[1])
    end = min(int(match[2]), total - 1) if match[2] else total - 1
    if start >= total or end < start:
        raise HTTPException(416, "invalid byte range")
    return start, end, True


@router.get("/api/v1/sessions/{session_id}/recording")
def replay_recording(session_id: str, request: Request) -> StreamingResponse:
    _session(session_id, request)
    stream, parts = _stream_and_parts(session_id)
    manifest = next((item for item in list_entities(db(), "recording_manifest", session_id)
                     if item["stream_id"] == stream["id"]), None)
    if manifest and manifest.get("replay_locator"):
        replay = Path(manifest["replay_locator"]).resolve()
        if replay.is_relative_to(storage_root().resolve()) and replay.is_file():
            parts = [(0, replay, replay.stat().st_size)]
    total = sum(size for _, _, size in parts)
    start, end, partial = _byte_range(request.headers.get("range"), total)
    mime = stream.get("codec") or "video/webm"
    if not (mime.startswith("video/webm") or mime.startswith("video/mp4")):
        raise HTTPException(415, "recording format cannot be replayed")

    def chunks():
        offset = 0
        for _, path, size in parts:
            local_start = max(0, start - offset)
            local_end = min(size - 1, end - offset)
            if local_start <= local_end:
                with path.open("rb") as source:
                    source.seek(local_start)
                    remaining = local_end - local_start + 1
                    while remaining:
                        data = source.read(min(256 * 1024, remaining))
                        if not data:
                            raise OSError("recording chunk ended early")
                        remaining -= len(data)
                        yield data
            offset += size
            if offset > end:
                break

    headers = {
        "Accept-Ranges": "bytes", "Content-Length": str(end - start + 1),
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
    }
    if partial:
        headers["Content-Range"] = f"bytes {start}-{end}/{total}"
    return StreamingResponse(chunks(), status_code=206 if partial else 200,
                             media_type=mime, headers=headers)


@router.get("/api/v1/sessions/{session_id}/backup/download")
def download_private_backup(session_id: str, request: Request) -> StreamingResponse:
    """Owner's private evidence backup; not a training or publication release."""
    payload = _session(session_id, request)
    stream, parts = _stream_and_parts(session_id)
    if sum(size for _, _, size in parts) > 512 * 1024 * 1024:
        raise HTTPException(413, "recording exceeds local backup limit")
    video_name = "recording.mp4" if str(stream.get("codec", "")).startswith("video/mp4") else "recording.webm"
    kinds = BACKUP_KINDS
    manifest = {
        "schema_version": "veytac-private-backup-v1",
        "source_session_id": session_id, "created_at": payload.get("created_at"),
        "source_type": stream.get("source_type"), "video_ref": video_name,
        "video_mime": stream.get("codec"), "task_brief": payload.get("task_brief"),
        "complete": _recording_info(session_id)["complete"],
        "chunk_hashes": [dict(sequence_no=row[0], sha256=row[1], size_bytes=row[2])
                         for row in db().execute(
                             "SELECT sequence_no,sha256,size_bytes FROM chunks WHERE session_id=? "
                             "AND stream_id=? ORDER BY sequence_no", (session_id, stream["id"]))],
        "included_data": [f"{kind}.json" for kind in kinds],
        "purpose": "private owner backup; not training-ready",
    }
    archive = tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024)
    try:
        with ZipFile(archive, "w", compression=ZIP_STORED) as bundle:
            with bundle.open(video_name, "w") as target:
                for _, path, _ in parts:
                    with path.open("rb") as source:
                        shutil.copyfileobj(source, target, 256 * 1024)
            bundle.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            for kind in kinds:
                bundle.writestr(f"{kind}.json", json.dumps(
                    list_entities(db(), kind, session_id), ensure_ascii=False))
        archive.seek(0)
    except Exception:
        archive.close()
        raise

    def body():
        try:
            while data := archive.read(256 * 1024):
                yield data
        finally:
            archive.close()

    return StreamingResponse(body(), media_type="application/zip", headers={
        "Content-Disposition": 'attachment; filename="veytac-session-backup.zip"',
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
    })


class Point(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class Box(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    w: float = Field(gt=0, le=1)
    h: float = Field(gt=0, le=1)

    @model_validator(mode="after")
    def inside_frame(self):
        if self.x + self.w > 1.001 or self.y + self.h > 1.001:
            raise ValueError("box exceeds frame")
        return self


class TrackMark(BaseModel):
    key: str = Field(min_length=1, max_length=80)
    kind: Literal["human", "object"]
    label: str = Field(min_length=1, max_length=80)
    box: Box


class TrackSample(BaseModel):
    at_ms: int = Field(ge=0, le=900000)
    frame_w: int = Field(ge=1, le=8192)
    frame_h: int = Field(ge=1, le=8192)
    tracks: list[TrackMark] = Field(max_length=30)
    hand_points: list[list[Point]] = Field(max_length=2)


class TrackBatch(BaseModel):
    samples: list[TrackSample] = Field(min_length=1, max_length=12)


@router.post("/api/v1/sessions/{session_id}/tracking")
def save_tracking(session_id: str, body: TrackBatch, request: Request) -> dict:
    _session(session_id, request)
    record = {"id": make_id("trk"), "clock_id": "recording_elapsed",
              "source": "on_device", "samples": [s.model_dump() for s in body.samples]}
    put_entity(db(), "track_batch", record["id"], session_id, record)
    return {"accepted": len(body.samples)}


@router.get("/api/v1/sessions/{session_id}/tracking")
def get_tracking(session_id: str, request: Request) -> dict:
    _session(session_id, request)
    samples = [sample for batch in list_entities(db(), "track_batch", session_id)
               for sample in batch.get("samples", [])]
    return {"clock_id": "recording_elapsed", "source": "on_device",
            "samples": sorted(samples, key=lambda s: s["at_ms"])}


@router.get("/api/v1/sessions/{session_id}/masks")
def get_masks(session_id: str, request: Request) -> dict:
    _session(session_id, request)
    stored = sorted((item for item in list_entities(db(), "mask", session_id)
                     if item.get("recording_elapsed_ms") is not None),
                    key=lambda item: item["recording_elapsed_ms"])
    return {"source": "sam-3.1", "total": len(stored), "truncated": len(stored) > 300,
            "masks": [{key: item.get(key) for key in (
                "id", "recording_elapsed_ms", "frame_w", "frame_h", "object_id",
                "label", "box", "svg", "decoded", "confidence", "execution_mode", "model")}
                | {"mask_size": [item.get("mask", {}).get("h"), item.get("mask", {}).get("w")]}
                for item in stored[:300]]}


class ObjectLabelBody(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    utterance: str = Field(min_length=1, max_length=300)
    language: Literal["en", "ja", "zh"]
    at_ms: int = Field(ge=0, le=900000)
    localization: Literal["unlocalized", "on_device_candidate", "sam_candidate", "expert_pointed"]
    track_key: str | None = Field(default=None, max_length=80)
    point: Point | None = None

    @model_validator(mode="after")
    def location_is_explicit(self):
        if self.localization == "on_device_candidate" and not self.track_key:
            raise ValueError("candidate track key required")
        if self.localization == "expert_pointed" and self.point is None:
            raise ValueError("expert point required")
        return self


@router.post("/api/v1/sessions/{session_id}/object-labels")
def save_object_label(session_id: str, body: ObjectLabelBody, request: Request) -> dict:
    _session(session_id, request)
    record = {"id": make_id("lbl"), "session_id": session_id,
              "source": "expert_speech", "review_state": "unreviewed",
              "clock_id": "recording_elapsed", "created_at": utcnow_iso(),
              "localization_history": [],
              **body.model_dump()}
    put_entity(db(), "object_label", record["id"], session_id, record)
    return {"label": record}


@router.get("/api/v1/sessions/{session_id}/object-labels")
def get_object_labels(session_id: str, request: Request) -> dict:
    _session(session_id, request)
    return {"labels": list_entities(db(), "object_label", session_id)}


class PointCue(Point):
    at_ms: int = Field(ge=0, le=900000)


@router.post("/api/v1/sessions/{session_id}/object-labels/{label_id}/point")
def point_object_label(session_id: str, label_id: str, body: PointCue, request: Request) -> dict:
    _session(session_id, request)
    record = next((item for item in list_entities(db(), "object_label", session_id)
                   if item["id"] == label_id), None)
    if record is None:
        raise HTTPException(404, "object label not found")
    record.setdefault("localization_history", []).append({
        "localization": record["localization"], "point": record.get("point"),
        "track_key": record.get("track_key"), "changed_at": utcnow_iso(),
    })
    record["localization"] = "expert_pointed"
    record["point"] = {"x": body.x, "y": body.y}
    record["point_at_ms"] = body.at_ms
    record["track_key"] = None
    put_entity(db(), "object_label", label_id, session_id, record)
    return {"label": record}


class LocalizeBody(BaseModel):
    jpeg_b64: str = Field(min_length=100, max_length=3_000_000)
    frame_w: int = Field(ge=1, le=8192)
    frame_h: int = Field(ge=1, le=8192)
    at_ms: int = Field(ge=0, le=900000)


@router.post("/api/v1/sessions/{session_id}/object-labels/{label_id}/localize")
def localize_object_label(session_id: str, label_id: str, body: LocalizeBody,
                          request: Request) -> dict:
    """One paid, budgeted concept attempt. A result is only a visual candidate."""
    from veytac.providers.sam import SamClient, SamConfig, SamError, build_concept_text, estimate_sam_micro

    payload = _session(session_id, request)
    record = next((item for item in list_entities(db(), "object_label", session_id)
                   if item["id"] == label_id), None)
    if record is None:
        raise HTTPException(404, "object label not found")
    if not body.jpeg_b64.startswith("data:image/jpeg;base64,"):
        raise HTTPException(422, "JPEG data URL required")
    if record["localization"] != "unlocalized":
        return {"status": "already_localized", "label": record}
    if not payload.get("processing_granted"):
        raise HTTPException(403, "external inference permission required")
    if not _live_enabled(payload):
        return {"status": "unavailable", "reason": "live segmentation is not enabled",
                "label": record}
    config = SamConfig()
    try:
        config.require_ready()
        concept = build_concept_text(record["label"])
    except SamError as exc:
        return {"status": "unavailable", "reason": str(exc), "label": record}
    call_id = make_id("call")
    if not reserve_session_call(db(), session_id, call_id, estimate_sam_micro(1)):
        return {"status": "budget_exhausted", "label": record}
    from .model_calls import begin_model_call, finish_model_call
    begin_model_call(db(), session_id, call_id, kind="object localization",
                     provider="Meta", model=config.model,
                     estimated_micro=estimate_sam_micro(1))
    try:
        result = SamClient(config).segment_image(image_url=body.jpeg_b64, prompt_text=concept)
    except SamError as exc:
        reconcile_session_call(db(), session_id, call_id, None)
        finish_model_call(db(), session_id, call_id, status="error")
        return {"status": "failed", "reason": str(exc), "label": record}
    reconcile_session_call(db(), session_id, call_id, None)
    finish_model_call(db(), session_id, call_id, status="completed")
    candidates = [item for item in result.get("records", []) if isinstance(item.get("box"), dict)]
    candidates.sort(key=lambda item: item.get("c") or 0, reverse=True)
    if not candidates:
        return {"status": "no_match", "label": record}
    raw = candidates[0]["box"]
    try:
        x1, y1, x2, y2 = (int(raw[key]) for key in ("x1", "y1", "x2", "y2"))
        width, height = int(raw["w"]), int(raw["h"])
        if width != body.frame_w or height != body.frame_h or not (0 <= x1 < x2 < width and 0 <= y1 < y2 < height):
            raise ValueError("candidate box outside frame")
        box = Box(x=x1 / width, y=y1 / height, w=(x2 - x1) / width, h=(y2 - y1) / height)
    except (KeyError, TypeError, ValueError):
        return {"status": "invalid_candidate", "label": record}
    record.setdefault("localization_history", []).append({
        "localization": record["localization"], "changed_at": utcnow_iso(),
    })
    record.update({"localization": "sam_candidate", "box": box.model_dump(),
                   "localized_at_ms": body.at_ms, "segmentation_model": result.get("model"),
                   "segmentation_mode": result.get("execution_mode"),
                   "confidence": candidates[0].get("c")})
    match = candidates[0]
    mask = match.get("mask") or {}
    if (match.get("decoded") and isinstance(match.get("svg"), str)
            and len(match["svg"]) < 120_000
            and isinstance(mask.get("h"), int) and mask["h"] > 0
            and isinstance(mask.get("w"), int) and mask["w"] > 0):
        record["mask_svg"] = match["svg"]
        record["mask_size"] = [mask.get("h"), mask.get("w")]
        record["mask_rle"] = match.get("rle")
    put_entity(db(), "object_label", label_id, session_id, record)
    return {"status": "candidate", "label": record}


class ExpertNoteBody(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    language: Literal["en", "ja", "zh"]
    at_ms: int = Field(ge=0, le=900000)


@router.post("/api/v1/sessions/{session_id}/expert-notes")
def save_expert_note(session_id: str, body: ExpertNoteBody, request: Request) -> dict:
    _session(session_id, request)
    record = {"id": make_id("note"), "session_id": session_id,
              "source": "expert_speech", "review_state": "unreviewed",
              "clock_id": "recording_elapsed", "created_at": utcnow_iso(),
              **body.model_dump()}
    put_entity(db(), "expert_note", record["id"], session_id, record)
    return {"note": record}


@router.get("/api/v1/sessions/{session_id}/expert-notes")
def get_expert_notes(session_id: str, request: Request) -> dict:
    _session(session_id, request)
    return {"notes": list_entities(db(), "expert_note", session_id)}


@router.get("/api/v1/sessions/{session_id}/robot-dataset")
def robot_dataset(session_id: str, request: Request, include_manifest: bool = False) -> dict:
    payload = _session(session_id, request)
    info = _recording_info(session_id)
    samples = [sample for batch in list_entities(db(), "track_batch", session_id)
               for sample in batch.get("samples", [])]
    labels = list_entities(db(), "object_label", session_id)
    stream = next((item for item in list_entities(db(), "stream", session_id)
                   if item["id"] == info["stream_id"]), {})
    hashes = [dict(sequence_no=row[0], sha256=row[1], size_bytes=row[2])
              for row in db().execute(
                  "SELECT sequence_no,sha256,size_bytes FROM chunks WHERE session_id=? "
                  "AND stream_id=? ORDER BY sequence_no", (session_id, info["stream_id"]))]
    return {
        "session_id": session_id, "kind": "observation_only",
        "training_permission": bool(payload.get("training_granted")),
        "recording_complete": info["complete"],
        "video_bytes": info["size_bytes"], "tracking_samples": len(samples),
        "expert_labels": len(labels),
        "action_policy_ready": False,
        "missing_for_action_policy": ["robot_state", "robot_action", "calibration", "action_alignment"],
        "observation_manifest": {
            "schema_version": "veytac-observation-dataset-v1",
            "mode": payload.get("mode"), "source_type": stream.get("source_type"),
            "video_ref": f"/api/v1/sessions/{session_id}/recording",
            "video_mime": info["mime"], "chunk_hashes": hashes,
            "chunk_timing": list_entities(db(), "chunk_timing", session_id),
            "clock_id": "recording_elapsed", "samples": samples,
            "object_labels": labels,
            "expert_notes": list_entities(db(), "expert_note", session_id),
            "sam_masks": list_entities(db(), "mask", session_id),
            "training_target": "visual observation only; no robot policy",
            "robot_state": None, "robot_action": None,
        } if include_manifest and payload.get("training_granted") and info["complete"] else None,
    }


def _latest_decisions(session_id: str) -> list[dict]:
    latest: dict[str, dict] = {}
    for item in list_entities(db(), "decision", session_id):
        current = latest.get(item["record_id"])
        if current is None or item["revision"] > current["revision"]:
            latest[item["record_id"]] = item
    return list(latest.values())


class SourceRightsBody(BaseModel):
    origin: str = Field(min_length=3, max_length=200)
    attribution: str = Field(max_length=200)
    training_rights_confirmed: bool


@router.post("/api/v1/sessions/{session_id}/source-rights")
def declare_source_rights(session_id: str, body: SourceRightsBody, request: Request) -> dict:
    _session(session_id, request)
    record = {"id": f"rights_{session_id}", **body.model_dump(),
              "basis": "owner_declaration", "declared_at": utcnow_iso()}
    put_entity(db(), "source_rights", record["id"], session_id, record)
    return {"source_rights": record}


@router.get("/api/v1/sessions/{session_id}/dataset/quality")
def dataset_quality(session_id: str, request: Request) -> dict:
    """Local, deterministic postprocessing. No model call or invented actions."""
    payload = _session(session_id, request)
    try:
        info = _recording_info(session_id)
        stream = next(item for item in list_entities(db(), "stream", session_id)
                      if item["id"] == info["stream_id"])
    except HTTPException as exc:
        if exc.status_code != 404:
            raise
        info = None
        stream = {}
    observations = list_entities(db(), "observation", session_id)
    live = sum(item.get("execution_mode") == "live" and item.get("status") != "failed"
               for item in observations)
    masks = list_entities(db(), "mask", session_id)
    decoded_masks = sum(bool(item.get("decoded") and item.get("svg")) for item in masks)
    decisions = _latest_decisions(session_id)
    approved = [item for item in decisions if item.get("review", {}).get("state") == "approved"]
    observed_assets = {ref.get("asset_id") for item in observations
                       if item.get("status") == "proposed"
                       for ref in item.get("evidence_refs", [])}
    grounded = [item for item in approved if any(
        ref.get("asset_id") in observed_assets
        for ref in item.get("observed_action_evidence", []))]
    turns = list_entities(db(), "turn", session_id)
    labels = list_entities(db(), "object_label", session_id)
    timing = list_entities(db(), "chunk_timing", session_id)
    gaps = [item.get("gap_before_ms") for item in timing if item.get("gap_before_ms")]
    complete = bool(info and info["complete"])
    permitted = bool(payload.get("training_granted"))
    source = stream.get("source_type", "unknown")
    rights = list_entities(db(), "source_rights", session_id)
    rights_declared = bool(rights and rights[-1].get("training_rights_confirmed"))
    visual_reasons = []
    if not complete:
        visual_reasons.append("recording incomplete or absent")
    if not live:
        visual_reasons.append("no successful live provider observations")
    if not permitted:
        visual_reasons.append("training permission not granted")
    if not rights_declared:
        visual_reasons.append("source training rights declaration required")
    if info and len(timing) != info["chunk_count"]:
        visual_reasons.append("some chunks lack recording clock timing")
    if gaps:
        visual_reasons.append("recording gaps require review")
    ai_reasons = list(visual_reasons)
    if not approved:
        ai_reasons.append("no latest approved decision records")
    elif len(grounded) != len(approved):
        ai_reasons.append("approved decisions missing observation evidence")
    return {
        "schema_version": "veytac-dataset-quality-v1", "session_id": session_id,
        "source_type": source,
        "target_robot_format": "LeRobot v3 (future action-aligned adapter)",
        "evidence": {"recording_complete": complete,
                     "seekable": bool(info and info["seekable"]),
                     "video_bytes": info["size_bytes"] if info else 0,
                     "chunk_count": info["chunk_count"] if info else 0,
                     "timed_chunks": len(timing), "recording_gap_count": len(gaps),
                     "live_observations": live,
                     "mock_or_failed_observations": len(observations) - live,
                     "sam_masks": len(masks), "decoded_sam_masks": decoded_masks,
                     "tracking_samples": info["tracking_samples"] if info else 0,
                     "expert_labels": len(labels), "dialogue_turns": len(turns),
                     "approved_latest_decisions": len(approved),
                     "grounded_approved_decisions": len(grounded),
                     "training_permission": permitted},
        "source_rights": {"declared": rights_declared,
                          "basis": rights[-1].get("basis") if rights else None,
                          "origin": rights[-1].get("origin") if rights else None},
        "gates": {
            "visual_ai": {"status": "CANDIDATE" if not visual_reasons else "BLOCKED",
                          "reasons": visual_reasons,
                          "format": "VEYTAC observation ZIP; adapter needed for model-specific loader"},
            "reviewed_sft": {"status": "CANDIDATE" if not ai_reasons else "BLOCKED",
                             "reasons": ai_reasons,
                             "format": "VEYTAC reviewed-decision JSONL; multi-session split and target-model validation required"},
            "robot_policy": {"status": "BLOCKED", "reasons": [
                "no measured robot state/action trajectories, calibration, or action alignment"],
                "format": "LeRobot v3 requires synchronized observation/state/action episodes"},
            "code_agent_harness": {"status": "BLOCKED", "reasons": [
                "no reviewed tool-call traces, outcomes, or executable evaluations"],
                "format": "no harness export"},
        },
        "postprocess_stages": [
            {"role": "media_integrity", "status": "PASS" if complete else "BLOCKED"},
            {"role": "visual_evidence", "status": "PASS" if live else "BLOCKED"},
            {"role": "dialogue_linking", "status": "PASS" if turns else "BLOCKED"},
            {"role": "human_review", "status": "PASS" if approved else "BLOCKED"},
            {"role": "format_gate", "status": "PASS" if not ai_reasons else "BLOCKED"},
        ],
    }


@router.post("/api/v1/sessions/{session_id}/postprocess/run")
def run_postprocess(session_id: str, request: Request) -> dict:
    """Bounded evidence-linking roles; no model call, training or publication."""
    report = dataset_quality(session_id, request)
    observations = list_entities(db(), "observation", session_id)[:300]
    labels = list_entities(db(), "object_label", session_id)[:300]
    questions = list_entities(db(), "question", session_id)[:300]
    turns = list_entities(db(), "turn", session_id)[:300]
    decisions = _latest_decisions(session_id)[:300]
    answered = {item.get("question_id") for item in turns}
    evidence_ids = {ref.get("asset_id") for item in decisions
                    if item.get("review", {}).get("state") == "approved"
                    for ref in item.get("observed_action_evidence", [])}
    review_queue = [
        {"kind": "object_label", "id": item["id"], "at_ms": item.get("at_ms"),
         "reason": "expert label needs visual confirmation"}
        for item in labels if item.get("review_state") != "approved"
    ] + [
        {"kind": "question", "id": item["id"], "reason": "delivered question lacks saved answer"}
        for item in questions if item.get("status") == "delivered" and item["id"] not in answered
    ] + [
        {"kind": "observation", "id": item["id"],
         "recording_elapsed_ms": item.get("recording_elapsed_ms"),
         "reason": "uncertainty needs expert answer or review"}
        for item in observations if item.get("status") == "proposed" and
        item.get("uncertainty") and not any(
            ref.get("asset_id") in evidence_ids for ref in item.get("evidence_refs", []))
    ]
    source = json.dumps({
        "quality_evidence": report["evidence"],
        "source_rights": report["source_rights"],
        "chunks": [(row[0], row[1]) for row in db().execute(
            "SELECT sequence_no,sha256 FROM chunks WHERE session_id=? ORDER BY sequence_no",
            (session_id,))],
        "observations": [item["id"] for item in observations],
        "labels": [item["id"] for item in labels],
        "questions": [(item["id"], item.get("status")) for item in questions],
        "turns": [item["id"] for item in turns],
        "decisions": [(item["record_id"], item["revision"],
                       item.get("review", {}).get("state")) for item in decisions],
    }, sort_keys=True)
    digest = hashlib.sha256(source.encode()).hexdigest()
    result = {
        "id": f"postprocess_{session_id}", "session_id": session_id,
        "schema_version": "veytac-postprocess-v1", "source_digest": digest,
        "execution_mode": "deterministic_local", "model_calls": 0,
        "stages": report["postprocess_stages"],
        "review_queue": review_queue[:300],
        "approved_grounded_record_ids": [item["record_id"] for item in decisions
                                         if item.get("review", {}).get("state") == "approved"
                                         and item.get("observed_action_evidence")],
        "gates": report["gates"],
    }
    put_entity(db(), "postprocess_run", result["id"], session_id, result)
    return {"postprocess": result}


@router.get("/api/v1/sessions/{session_id}/ai-dataset/download")
def download_ai_dataset(session_id: str, request: Request) -> StreamingResponse:
    """Private reviewed examples only; no model job or synthetic tool trace."""
    report = dataset_quality(session_id, request)
    if not report["evidence"]["training_permission"]:
        raise HTTPException(403, "training dataset permission required")
    if not report["evidence"]["recording_complete"]:
        raise HTTPException(409, "recording must be complete")
    if not report["source_rights"]["declared"]:
        raise HTTPException(403, "source training rights declaration required")
    if report["gates"]["reviewed_sft"]["status"] != "CANDIDATE":
        raise HTTPException(409, "reviewed dataset quality gate is blocked")
    approved = [item for item in _latest_decisions(session_id)
                if item.get("review", {}).get("state") == "approved"]
    if not approved:
        raise HTTPException(409, "no latest approved decisions")
    observations = list_entities(db(), "observation", session_id)

    def source_observation(item: dict) -> dict:
        refs = {ref.get("asset_id") for ref in item.get("observed_action_evidence", [])}
        return next(obs for obs in observations
                    if obs.get("status") == "proposed" and any(
                        ref.get("asset_id") in refs for ref in obs.get("evidence_refs", [])))

    rows = [{
        "schema_version": "veytac-reviewed-decision-v1",
        "session_id": session_id, "split_group": session_id,
        "source_type": report["source_type"],
        "record_id": item["record_id"], "revision": item["revision"],
        "task_id": item["task_id"],
        "source_observation_id": source_observation(item)["id"],
        "observation_text": source_observation(item)["description"],
        "input_text": (f"Task: {item['task_id']}\n"
                       f"Observation: {source_observation(item)['description']}\n"
                       f"Expert ({item['expert_original_language']}): "
                       f"{item['expert_original_statement']}"),
        "output_json": json.dumps(item, ensure_ascii=False),
        "observed_action_description": item["observed_action_description"],
        "expert_original_statement": item["expert_original_statement"],
        "expert_original_language": item["expert_original_language"],
        "decision_interval_start_ms": item["decision_interval_start_ms"],
        "decision_interval_end_ms": item["decision_interval_end_ms"],
        "review": item["review"],
        "target_decision_record": item,
    } for item in approved]
    data = ("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n").encode()
    return StreamingResponse(iter([data]), media_type="application/x-ndjson", headers={
        "Content-Disposition": f'attachment; filename="veytac-reviewed-{session_id}.jsonl"',
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
    })


@router.get("/api/v1/sessions/{session_id}/robot-dataset/download")
def download_observation_dataset(session_id: str, request: Request) -> StreamingResponse:
    """Export genuine visual evidence, explicitly lacking robot actions/states."""
    payload = _session(session_id, request)
    if not payload.get("training_granted"):
        raise HTTPException(403, "training dataset permission required")
    rights = list_entities(db(), "source_rights", session_id)
    if not rights or not rights[-1].get("training_rights_confirmed"):
        raise HTTPException(403, "source training rights declaration required")
    info = _recording_info(session_id)
    if not info["complete"]:
        raise HTTPException(409, "recording must be completed before export")
    _, parts = _stream_and_parts(session_id)
    if info["size_bytes"] > 512 * 1024 * 1024:
        raise HTTPException(413, "recording exceeds local export limit")
    manifest = robot_dataset(session_id, request, include_manifest=True)["observation_manifest"]
    video_name = "recording.mp4" if info["mime"].startswith("video/mp4") else "recording.webm"
    manifest["video_ref"] = video_name
    archive = tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024)
    try:
        with ZipFile(archive, "w", compression=ZIP_STORED) as bundle:
            with bundle.open(video_name, "w") as target:
                for _, path, _ in parts:
                    with path.open("rb") as source:
                        shutil.copyfileobj(source, target, 256 * 1024)
            bundle.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        archive.seek(0)
    except Exception:
        archive.close()
        raise

    def body():
        try:
            while data := archive.read(256 * 1024):
                yield data
        finally:
            archive.close()

    return StreamingResponse(body(), media_type="application/zip", headers={
        "Content-Disposition": f'attachment; filename="veytac-observation-{session_id}.zip"',
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
    })
