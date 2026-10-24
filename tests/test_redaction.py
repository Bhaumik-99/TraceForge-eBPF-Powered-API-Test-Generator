import json
from traceforge.redaction import REDACTED, sanitize_body, sanitize_headers, sanitize_path

def test_json_body_redacts_nested_sensitive_keys():
    body = json.dumps({"username":"demo-user","password":"dont-store-me",
                       "profile":{"api_key":"secret-value","city":"Delhi"}}).encode()
    result = sanitize_body(body, "application/json")
    assert result["username"] == "demo-user"
    assert result["password"] == REDACTED
    assert result["profile"]["api_key"] == REDACTED
    assert result["profile"]["city"] == "Delhi"
    assert "dont-store-me" not in json.dumps(result)

def test_credential_headers_are_removed():
    result = sanitize_headers({"content-type":"application/json",
        "Authorization":"Bearer secret-token","Cookie":"session=private",
        "host":"localhost","content-length":"12"})
    assert result == {"content-type":"application/json"}

def test_sensitive_query_parameters_are_redacted():
    path = sanitize_path("/lookup", "q=keyboard&api_key=secret&limit=5")
    assert "secret" not in path
    assert "api_key=%5BREDACTED%5D" in path
    assert "q=keyboard" in path and "limit=5" in path

def test_large_body_is_omitted():
    result = sanitize_body(b"x" * 30, "text/plain", max_bytes=10)
    assert str(result).startswith("[BODY OMITTED:")
