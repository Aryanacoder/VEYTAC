"""Frame trigger lineage: the reason a frame was sent is preserved.

Event-driven capture only pays for frames that tracking flagged; the
trigger string on the stored observation proves why the model saw it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services"))

import os  # noqa: E402

os.environ["VEYTAC_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["VEYTAC_STORAGE_ROOT"] = "./artifacts/test-storage"

from api import main as routes  # noqa: E402
from api.routers_capture import FrameBody, ingest_frame  # noqa: E402
from fastapi import Request, Response  # noqa: E402


def _create_session(body):
    return routes.create_session(body, Request({"type": "http", "headers": []}), Response())


def test_trigger_preserved_on_observation():
    sid = _create_session(
        routes.CreateSessionBody(task_id="trigger-demo")
    )["session"]["id"]
    routes.consent(sid, routes.ConsentBody(actor_id="u", purpose="capture", grant=True))
    obs = ingest_frame(
        sid, FrameBody(at_ms=4000, trigger="held_object_new:cup"))["observation"]
    assert obs["trigger"] == "held_object_new:cup"
    assert obs["execution_mode"] == "mock"

    plain = ingest_frame(sid, FrameBody(at_ms=5000))["observation"]
    assert plain["trigger"] == ""  # timed poll carries no trigger


def test_mock_sam_masks_stored_as_derived_evidence():
    from api.deps import db  # noqa: E402
    from api.routers_capture import list_entities  # noqa: E402

    sid = _create_session(
        routes.CreateSessionBody(task_id="sam-demo")
    )["session"]["id"]
    routes.consent(sid, routes.ConsentBody(actor_id="u", purpose="capture", grant=True))
    routes.consent(sid, routes.ConsentBody(actor_id="u", purpose="external_inference", grant=True))
    body = FrameBody(
        at_ms=6000, jpeg_b64="data:image/jpeg;base64,AAA", trigger="object_new:cup",
        frame_w=320, frame_h=240,
        prompts=[{"id": 3, "label": "cup", "x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}],
    )
    res = ingest_frame(sid, body)
    assert res["sam_error"] is None
    assert len(res["masks"]) == 1
    mask = res["masks"][0]
    assert mask["execution_mode"] == "mock"
    assert mask["decoded"] is False  # no decoder lib in this env; payload retained
    assert mask["mask"]["payload"] == "AAAA"
    assert mask["frame_at_ms"] == 6000
    assert mask["frame_w"] == 320 and mask["frame_h"] == 240
    stored = list_entities(db(), "mask", sid)
    assert any(m["id"] == mask["id"] for m in stored)

    # No prompts, no jpeg, or no dims: no masks, no error, observation intact.
    bare = ingest_frame(sid, FrameBody(at_ms=7000))
    assert bare["masks"] == [] and bare["sam_error"] is None
    assert bare["observation"]["status"] == "proposed"
