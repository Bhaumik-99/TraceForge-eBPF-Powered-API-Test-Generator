import json
from traceforge.recorder import FixtureRecorder, load_fixtures

def test_recorder_persists_redacted_fixture(tmp_path):
    recorder = FixtureRecorder(tmp_path / "fixtures")
    saved = recorder.record(
        method="POST", path="/orders", query="token=should-not-persist",
        request_headers={"content-type":"application/json",
                         "authorization":"Bearer should-not-persist"},
        request_body=b'{"product_id":1,"password":"should-not-persist"}',
        request_content_type="application/json", status_code=201,
        response_headers={"content-type":"application/json","set-cookie":"session=private"},
        response_body=b'{"order_id":"order-1","status":"created"}',
        response_content_type="application/json", elapsed_ms=1.25)
    raw = saved.read_text(encoding="utf-8")
    assert "should-not-persist" not in raw and "session=private" not in raw
    fixture = json.loads(raw)
    assert fixture["request"]["body"]["password"] == "[REDACTED]"
    assert "authorization" not in {k.lower() for k in fixture["request"]["headers"]}
    assert "token=%5BREDACTED%5D" in fixture["request"]["path"]
    loaded = load_fixtures(tmp_path / "fixtures")
    assert len(loaded) == 1 and loaded[0]["response"]["status_code"] == 201
