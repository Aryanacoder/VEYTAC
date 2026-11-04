"""SAM provider tests: prompt grammar, output parsing, failure behavior.

Fixtures mirror the Meta SAM docs exactly (truck box-prompt example,
button-image output shape with synthetic payloads — the payload alphabet
never contains `|` or `;`, so synthetic payloads parse identically).
No network, no key, no mask-decoder lib needed here.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from veytac.providers.sam import (  # noqa: E402
    MockSamClient,
    SamError,
    build_box_prompt,
    build_concept_text,
    parse_output_line,
    try_decode_masks,
)


def test_concept_prompt_single_noun_phrase():
    assert build_concept_text("  red hat ") == "red hat"


def test_concept_list_refused_unpaid():
    with pytest.raises(SamError):
        build_concept_text("bus, bicycle")
    with pytest.raises(SamError):
        build_concept_text("cup and plate")


def test_box_prompt_matches_documented_truck_example():
    text = build_box_prompt(
        (1800, 1200),
        [{"id": 1, "x1": 444, "y1": 626, "x2": 675, "y2": 849}],
    )
    assert text == "<0f>1<|box;x1=444;y1=626;x2=675;y2=849;w=1800;h=1200|>"


def test_box_prompt_rejects_bad_input():
    with pytest.raises(SamError):
        build_box_prompt((1800, 1200), [])
    with pytest.raises(SamError):  # outside frame
        build_box_prompt((100, 100), [{"id": 1, "x1": 0, "y1": 0, "x2": 200, "y2": 10}])
    with pytest.raises(SamError):  # duplicate id
        build_box_prompt((100, 100), [
            {"id": 1, "x1": 0, "y1": 0, "x2": 10, "y2": 10},
            {"id": 1, "x1": 20, "y1": 20, "x2": 30, "y2": 30},
        ])
    with pytest.raises(SamError):  # non-integer id
        build_box_prompt((100, 100), [{"id": "a", "x1": 0, "y1": 0, "x2": 10, "y2": 10}])


def test_parse_documented_image_line():
    line = (
        "<0f>0<|box;x1=353;y1=382;x2=453;y2=427;w=537;h=561|>"
        "<|mask;x=0;y=0;data=46,101,~QUJD|>,"
        "1<|box;x1=260;y1=382;x2=340;y2=427;w=537;h=561|>"
        "<|mask;x=0;y=0;data=46,81,~REVG|>"
    )
    recs = parse_output_line(line)
    assert [r["id"] for r in recs] == [0, 1]
    assert recs[0]["frame"] == 0
    assert recs[0]["box"]["x1"] == 353
    assert recs[0]["box"]["x2"] == 453
    assert recs[0]["mask"] == {"x": 0, "y": 0, "h": 46, "w": 101,
                               "enc": "~", "payload": "QUJD", "c": None}
    assert recs[1]["mask"]["w"] == 81


def test_parse_confidence_and_sparse_ids():
    line = ("<2f>0<|box;x1=1;y1=2;x2=3;y2=4;w=9;h=9;c=0.9|>"
            "<|mask;x=0;y=0;c=0.9;data=2,2,~QQ|>,"
            "2<|box;x1=5;y1=5;x2=6;y2=6;w=9;h=9;c=0.5|>"
            "<|mask;x=0;y=0;c=0.5;data=2,2,~Qk|>")
    recs = parse_output_line(line)
    assert [r["id"] for r in recs] == [0, 2]  # sparse ids keyed by id
    assert recs[0]["c"] == 0.9
    assert recs[1]["mask"]["c"] == 0.5


def test_parse_rejects_garbage():
    with pytest.raises(SamError):
        parse_output_line("not a segmentation line")
    with pytest.raises(SamError):  # box without mask
        parse_output_line("<0f>0<|box;x1=1;y1=1;x2=2;y2=2;w=9;h=9|>")


def test_decode_falls_back_opaque_without_lib():
    recs = [{"frame": 0, "id": 0, "box": {}, "mask": {
        "x": 0, "y": 0, "h": 8, "w": 8, "enc": "~", "payload": "AAAA", "c": None}}]
    out = try_decode_masks(recs)
    assert out[0]["decoded"] is False
    assert out[0]["mask"]["payload"] == "AAAA"  # retained, not dropped


def test_mock_client_shape():
    out = MockSamClient().segment_image(image_url="x", prompt_text="cup")
    assert out["execution_mode"] == "mock"
    assert out["records"][0]["id"] == 0
    assert out["records"][0]["decoded"] is False


def test_live_request_places_confidence_in_metadata_without_network(monkeypatch):
    from veytac.providers.sam import SamClient, SamConfig

    monkeypatch.setattr(SamConfig, "require_ready", lambda _self: None)
    sent = {}

    class Rejected:
        status_code = 400

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"fixture rejection"

    class FakeHttp:
        def stream(self, method, path, *, json):
            sent.update({"method": method, "path": path, "body": json})
            return Rejected()

    client = SamClient()
    client._http = FakeHttp()
    with pytest.raises(SamError):
        client.segment_image(image_url="data:image/jpeg;base64,AAAA", prompt_text="person")
    assert sent["body"]["metadata"] == {
        "mask_encoding": "one_bit", "include_confidence": "true"}
    assert "include_confidence" not in sent["body"]
