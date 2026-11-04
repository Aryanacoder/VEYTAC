"""Private recording replay, synchronized labels, and robot-data honesty."""

import io
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services"))

from api import routers_capture, routers_library  # noqa: E402
from api.db import connect, get_session, insert_session, list_entities, put_entity, update_session  # noqa: E402
from api.main import app  # noqa: E402


def test_recording_range_tracking_and_dataset_gate(tmp_path, monkeypatch):
    conn = connect(":memory:")
    session_id = "ses_library"
    stream_id = "str_library"
    insert_session(conn, session_id, {"id": session_id, "capture_granted": True,
                                      "owner_cookie_hash": hashlib.sha256(b"owner-test-token").hexdigest(),
                                      "training_granted": False, "mode": "LIVE_CAPTURE"})
    put_entity(conn, "stream", stream_id, session_id,
               {"id": stream_id, "epoch_id": "e0", "codec": "video/webm"})
    monkeypatch.setattr(routers_capture, "db", lambda: conn)
    monkeypatch.setattr(routers_library, "db", lambda: conn)
    monkeypatch.setattr(routers_capture, "storage_root", lambda: tmp_path)
    monkeypatch.setattr(routers_library, "storage_root", lambda: tmp_path)
    routers_capture.store_chunk(session_id, stream_id, "e0", 0, b"AAA", None, 10)
    routers_capture.store_chunk(session_id, stream_id, "e0", 1, b"BBB", None, 20)

    client = TestClient(app)
    url = f"/api/v1/sessions/{session_id}"
    assert client.get(f"{url}/recording").status_code == 403
    client.cookies.set("veytac_local_owner", "owner-test-token")
    response = client.get(f"{url}/recording", headers={"Range": "bytes=2-4"})
    assert response.status_code == 206
    assert response.content == b"ABB"
    assert response.headers["content-range"] == "bytes 2-4/6"
    assert client.get(f"{url}/recording").content == b"AAABBB"
    assert client.get(f"{url}/recording", headers={"Range": "bytes=6-"}).status_code == 416
    assert client.get(f"{url}/recording/info").json()["complete"] is False
    assert client.post(f"{url}/recording/complete", json={
        "stream_id": stream_id, "expected_chunks": 3,
    }).status_code == 409
    assert client.post(f"{url}/recording/complete", json={
        "stream_id": stream_id, "expected_chunks": 2,
    }).json()["recording"]["complete"] is True

    sample = {"at_ms": 1000, "frame_w": 1280, "frame_h": 720,
              "tracks": [{"key": "object:tool:0", "kind": "object", "label": "tool",
                          "box": {"x": 0.2, "y": 0.3, "w": 0.1, "h": 0.1}}],
              "hand_points": [[{"x": 0.25, "y": 0.32}]]}
    assert client.post(f"{url}/tracking", json={"samples": [sample]}).json()["accepted"] == 1
    assert client.get(f"{url}/tracking").json()["samples"] == [sample]
    label = client.post(f"{url}/object-labels", json={
        "label": "screw", "utterance": "This is a screw", "language": "en",
        "at_ms": 1000, "localization": "unlocalized",
    }).json()["label"]
    pointed = client.post(f"{url}/object-labels/{label['id']}/point",
                          json={"x": 0.25, "y": 0.32, "at_ms": 1250}).json()["label"]
    assert pointed["localization"] == "expert_pointed"
    assert pointed["point_at_ms"] == 1250
    assert pointed["localization_history"][0]["localization"] == "unlocalized"
    assert client.post(f"{url}/expert-notes", json={
        "text": "I am holding a screw", "language": "en", "at_ms": 1000,
    }).status_code == 200

    status = client.get(f"{url}/robot-dataset").json()
    assert status["action_policy_ready"] is False
    assert status["observation_manifest"] is None
    assert client.get(f"{url}/robot-dataset/download").status_code == 403
    payload = get_session(conn, session_id)
    payload["training_granted"] = True
    update_session(conn, session_id, payload)
    assert client.post(f"{url}/source-rights", json={
        "origin": "my own camera recording", "attribution": "session owner",
        "training_rights_confirmed": True,
    }).status_code == 200
    package = client.get(f"{url}/robot-dataset/download")
    assert package.status_code == 200
    with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert archive.read("recording.webm") == b"AAABBB"
    assert manifest["robot_state"] is None
    assert manifest["robot_action"] is None
    assert manifest["object_labels"][0]["label"] == "screw"
    assert manifest["samples"][0]["tracks"][0]["label"] == "tool"


def test_spoken_label_concept_localization_is_bounded_and_unreviewed(monkeypatch):
    from veytac.providers import sam

    conn = connect(":memory:")
    session_id = "ses_concept"
    token = "owner-concept-token"
    insert_session(conn, session_id, {
        "id": session_id, "capture_granted": True, "processing_granted": True,
        "owner_cookie_hash": hashlib.sha256(token.encode()).hexdigest(),
        "budget_cap_usd": "0.10",
    })
    monkeypatch.setattr(routers_library, "db", lambda: conn)
    monkeypatch.setattr(routers_library, "_live_enabled", lambda _payload: True)
    monkeypatch.setattr(sam.SamConfig, "require_ready", lambda _self: None)
    prompts = []

    def segment(_self, *, image_url, prompt_text):
        prompts.append(prompt_text)
        assert image_url.startswith("data:image/jpeg;base64,")
        return {"model": "test-sam", "execution_mode": "live", "records": [
            {"box": {"x1": 320, "y1": 180, "x2": 640, "y2": 360,
                     "w": 1280, "h": 720}, "c": 0.8},
        ]}

    monkeypatch.setattr(sam.SamClient, "segment_image", segment)
    client = TestClient(app)
    client.cookies.set("veytac_local_owner", token)
    url = f"/api/v1/sessions/{session_id}"
    label = client.post(f"{url}/object-labels", json={
        "label": "screw", "utterance": "This is a screw", "language": "en",
        "at_ms": 900, "localization": "unlocalized",
    }).json()["label"]
    response = client.post(f"{url}/object-labels/{label['id']}/localize", json={
        "jpeg_b64": "data:image/jpeg;base64," + "A" * 100,
        "frame_w": 1280, "frame_h": 720, "at_ms": 1000,
    })
    assert response.status_code == 200
    found = response.json()
    assert found["status"] == "candidate"
    assert found["label"]["box"] == {"x": 0.25, "y": 0.25, "w": 0.25, "h": 0.25}
    assert found["label"]["review_state"] == "unreviewed"
    assert found["label"]["localized_at_ms"] == 1000
    assert prompts == ["screw"]
    assert client.post(f"{url}/object-labels/{label['id']}/localize", json={
        "jpeg_b64": "data:image/jpeg;base64," + "A" * 100,
        "frame_w": 1280, "frame_h": 720, "at_ms": 1100,
    }).json()["status"] == "already_localized"
    assert prompts == ["screw"]
    assert get_session(conn, session_id)["budget"]["unknown_micro"] == sam.estimate_sam_micro(1)


def test_screen_dataset_quality_and_reviewed_export_are_gated(tmp_path, monkeypatch):
    conn = connect(":memory:")
    sid, stream_id, token = "ses_screen_quality", "str_screen_quality", "screen-owner"
    insert_session(conn, sid, {"id": sid, "capture_granted": True,
                               "owner_cookie_hash": hashlib.sha256(token.encode()).hexdigest(),
                               "training_granted": False, "mode": "LIVE_CAPTURE"})
    put_entity(conn, "stream", stream_id, sid, {"id": stream_id, "epoch_id": "e0",
                                                 "codec": "video/webm", "source_type": "screen"})
    monkeypatch.setattr(routers_capture, "db", lambda: conn)
    monkeypatch.setattr(routers_library, "db", lambda: conn)
    monkeypatch.setattr(routers_capture, "storage_root", lambda: tmp_path)
    monkeypatch.setattr(routers_library, "storage_root", lambda: tmp_path)
    routers_capture.store_chunk(sid, stream_id, "e0", 0, b"screen", None, 1000,
                                recording_elapsed_ms=1000)
    client = TestClient(app)
    client.cookies.set("veytac_local_owner", token)
    url = f"/api/v1/sessions/{sid}"
    assert client.post(f"{url}/recording/complete", json={
        "stream_id": stream_id, "expected_chunks": 1}).status_code == 200
    report = client.get(f"{url}/dataset/quality").json()
    assert report["source_type"] == "screen"
    assert report["target_robot_format"].startswith("LeRobot v3")
    assert report["gates"]["robot_policy"]["status"] == "BLOCKED"
    assert report["gates"]["reviewed_sft"]["status"] == "BLOCKED"
    assert client.get(f"{url}/ai-dataset/download").status_code == 403
    payload = get_session(conn, sid)
    payload["training_granted"] = True
    update_session(conn, sid, payload)
    assert client.get(f"{url}/ai-dataset/download").status_code == 403
    put_entity(conn, "decision", "dec_quality:1", sid, {
        "record_id": "dec_quality", "revision": 1, "task_id": "software demo",
        "observed_action_description": "opened settings",
        "expert_original_statement": "I changed the field for this reason",
        "expert_original_language": "en", "decision_interval_start_ms": 100,
        "decision_interval_end_ms": 900,
        "observed_action_evidence": [{"asset_id": "ast_quality", "revision": 1,
            "locator": {"kind": "time_range", "clock_id": "recording_elapsed",
                        "start_ms": 500, "end_ms": 500}}],
        "review": {"state": "approved", "reviewer_id": "reviewer"},
    })
    assert client.get(f"{url}/ai-dataset/download").status_code == 403
    report = client.get(f"{url}/dataset/quality").json()
    assert "rights declaration" in " ".join(report["gates"]["reviewed_sft"]["reasons"])
    assert client.post(f"{url}/source-rights", json={
        "origin": "my own desktop work", "attribution": "session owner",
        "training_rights_confirmed": True,
    }).status_code == 200
    assert client.get(f"{url}/ai-dataset/download").status_code == 409
    put_entity(conn, "observation", "obs_quality", sid, {
        "id": "obs_quality", "status": "proposed", "execution_mode": "live",
        "description": "opened settings",
        "evidence_refs": [{"asset_id": "ast_quality", "revision": 1,
            "locator": {"kind": "time_range", "clock_id": "recording_elapsed",
                        "start_ms": 500, "end_ms": 500}}]})
    put_entity(conn, "object_label", "lbl_quality", sid, {
        "id": "lbl_quality", "review_state": "unreviewed", "at_ms": 500})
    postprocess = client.post(f"{url}/postprocess/run").json()["postprocess"]
    assert postprocess["model_calls"] == 0
    assert postprocess["execution_mode"] == "deterministic_local"
    assert postprocess["review_queue"][0]["id"] == "lbl_quality"
    assert postprocess["approved_grounded_record_ids"] == ["dec_quality"]
    assert client.post(f"{url}/postprocess/run").json()["postprocess"]["source_digest"] == postprocess["source_digest"]
    exported = client.get(f"{url}/ai-dataset/download")
    assert exported.status_code == 200
    row = json.loads(exported.text.strip())
    assert row["split_group"] == sid
    assert row["source_observation_id"] == "obs_quality"
    assert "opened settings" in row["input_text"]
    assert row["target_decision_record"]["review"]["state"] == "approved"
    report = client.get(f"{url}/dataset/quality").json()
    assert report["source_rights"]["declared"] is True
    package = client.get(f"{url}/robot-dataset/download")
    with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
    assert manifest["source_type"] == "screen"
    assert manifest["chunk_hashes"][0]["sha256"] == hashlib.sha256(b"screen").hexdigest()
    assert manifest["chunk_timing"][0]["elapsed_end_ms"] == 1000
    assert manifest["robot_state"] is None and manifest["robot_action"] is None


def test_media_chunks_remux_to_seekable_duration(tmp_path):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("ffmpeg and ffprobe required for media integration")
    source = tmp_path / "synthetic.webm"
    made = subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=blue:s=320x180:r=10",
        "-t", "1", "-c:v", "libvpx-vp9", str(source),
    ], capture_output=True, timeout=30, check=False)
    if made.returncode:
        pytest.skip("local ffmpeg has no VP9 encoder")
    content = source.read_bytes()
    midpoint = len(content) // 2
    first, second = tmp_path / "0.bin", tmp_path / "1.bin"
    first.write_bytes(content[:midpoint])
    second.write_bytes(content[midpoint:])
    result = routers_library._derive_playback([
        (0, first, first.stat().st_size), (1, second, second.stat().st_size),
    ], "video/webm")
    assert result is not None
    locator, duration_ms = result
    assert Path(locator).is_file()
    assert 900 <= duration_ms <= 1200


def test_owned_library_finish_and_private_backup(tmp_path, monkeypatch):
    conn = connect(":memory:")
    sid, stream_id, token = "ses_unfinished", "str_unfinished", "phone-owner"
    insert_session(conn, sid, {"id": sid, "capture_granted": True,
                              "owner_cookie_hash": hashlib.sha256(token.encode()).hexdigest(),
                              "task_brief": "Protecting a fragile mug"})
    put_entity(conn, "stream", stream_id, sid, {"id": stream_id, "epoch_id": "e0",
                                                "codec": "video/webm", "source_type": "camera"})
    monkeypatch.setattr(routers_capture, "db", lambda: conn)
    monkeypatch.setattr(routers_library, "db", lambda: conn)
    monkeypatch.setattr(routers_capture, "storage_root", lambda: tmp_path)
    monkeypatch.setattr(routers_library, "storage_root", lambda: tmp_path)
    routers_capture.store_chunk(sid, stream_id, "e0", 0, b"first", None, 5)
    routers_capture.store_chunk(sid, stream_id, "e0", 1, b"second", None, 11)
    put_entity(conn, "model_call", "call_one", sid, {
        "id": "call_one", "kind": "observation", "provider": "Meta",
        "model": "test-model", "status": "completed", "started_at": "2026-01-01",
        "started_perf": 12.5, "prompt": "private prompt"})
    client = TestClient(app)
    assert client.get("/api/v1/library/recordings").json() == {"recordings": []}
    client.cookies.set("veytac_local_owner", token)
    entries = client.get("/api/v1/library/recordings").json()["recordings"]
    assert len(entries) == 1 and entries[0]["title"] == "Protecting a fragile mug"
    assert entries[0]["complete"] is False
    calls = client.get(f"/api/v1/sessions/{sid}/model-calls").json()["calls"]
    assert calls[0]["model"] == "test-model"
    assert "prompt" not in calls[0] and "started_perf" not in calls[0]
    assert client.post(f"/api/v1/sessions/{sid}/recording/complete", json={
        "stream_id": stream_id, "expected_chunks": 2}).status_code == 200
    assert client.get("/api/v1/library/recordings").json()["recordings"][0]["complete"] is True
    backup = client.get(f"/api/v1/sessions/{sid}/backup/download")
    assert backup.status_code == 200
    with zipfile.ZipFile(io.BytesIO(backup.content)) as archive:
        assert archive.read("recording.webm") == b"firstsecond"
        assert json.loads(archive.read("manifest.json"))["complete"] is True
        assert archive.read("object_label.json") == b"[]"
        assert b"private prompt" not in backup.content
    client.cookies.set("veytac_local_owner", "other-browser")
    assert client.get(f"/api/v1/sessions/{sid}/backup/download").status_code == 403
    assert client.get(f"/api/v1/sessions/{sid}/model-calls").status_code == 403


def test_private_video_import_requires_permission(tmp_path, monkeypatch):
    conn = connect(":memory:")
    monkeypatch.setattr(routers_library, "db", lambda: conn)
    monkeypatch.setattr(routers_library, "storage_root", lambda: tmp_path)
    client = TestClient(app)
    sample = b"\x1aE\xdf\xa3" + b"demo"
    files = {"file": ("home-demo.webm", sample, "video/webm")}
    assert client.post("/api/v1/library/import", files=files).status_code == 403
    result = client.post("/api/v1/library/import", files=files,
                         data={"capture_permission": "true"})
    assert result.status_code == 200, result.text
    sid = result.json()["recording"]["id"]
    assert client.get("/api/v1/library/recordings").json()["recordings"][0]["id"] == sid
    assert client.get(f"/api/v1/sessions/{sid}/recording").content == sample
    payload = get_session(conn, sid)
    assert payload["training_granted"] is False
    assert payload["processing_granted"] is False
    put_entity(conn, "object_label", "lbl_original", sid, {
        "id": "lbl_original", "session_id": sid, "label": "mug",
        "review_state": "approved", "at_ms": 50})
    put_entity(conn, "decision", "dec_original", sid, {
        "id": "dec_original", "session_id": sid,
        "review": {"state": "approved", "reviewer_id": "old-reviewer"}})
    backup = client.get(f"/api/v1/sessions/{sid}/backup/download")
    assert backup.status_code == 200
    imported = client.post("/api/v1/library/import-backup",
                           files={"file": ("my-work.zip", backup.content, "application/zip")},
                           data={"capture_permission": "true"})
    assert imported.status_code == 200, imported.text
    restored = imported.json()["recording"]["id"]
    assert restored != sid
    assert client.get(f"/api/v1/sessions/{restored}/recording").content == sample
    restored_payload = get_session(conn, restored)
    assert restored_payload["training_granted"] is False
    assert restored_payload["processing_granted"] is False
    labels = client.get(f"/api/v1/sessions/{restored}/object-labels").json()["labels"]
    assert labels[0]["label"] == "mug" and labels[0]["review_state"] == "unreviewed"
    decisions = list_entities(conn, "decision", restored)
    assert decisions[0]["review"]["state"] == "unreviewed"
    assert decisions[0]["id"] != "dec_original"
