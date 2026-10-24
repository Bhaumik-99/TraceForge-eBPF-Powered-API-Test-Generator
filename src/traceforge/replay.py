"""Replay recorded HTTP fixtures against a target service."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import httpx
from traceforge.comparison import json_matches
from traceforge.recorder import load_fixtures

def _response_body(response: httpx.Response) -> Any:
    if "json" in response.headers.get("content-type", "").lower():
        try:
            return response.json()
        except ValueError:
            pass
    return response.text if response.content else None

def replay_fixtures(fixtures_dir: Path | str, base_url: str,
                    timeout: float = 10.0) -> list[dict[str, Any]]:
    fixtures = load_fixtures(Path(fixtures_dir))
    if not fixtures:
        raise ValueError(f"No valid JSON fixtures found in {fixtures_dir}")
    base_url = base_url.rstrip("/")
    results = []
    for fixture in fixtures:
        req, expected = fixture["request"], fixture["response"]
        path, body = req.get("path", "/"), req.get("body")
        item = {"id": fixture.get("id", "fixture"), "method": req.get("method", "GET"), "path": path}
        if isinstance(body, str) and body.startswith("[BODY OMITTED:"):
            results.append({**item, "status": "skipped", "reason": "request body was omitted"})
            continue
        if not path.startswith("/") or path.startswith("//"):
            results.append({**item, "status": "failed", "reason": "unsafe fixture path"})
            continue
        kwargs = {"headers": req.get("headers") or {}, "timeout": timeout, "follow_redirects": False}
        if isinstance(body, (dict, list)):
            kwargs["json"] = body
        elif body is not None:
            kwargs["content"] = body.encode("utf-8") if isinstance(body, str) else str(body)
        try:
            response = httpx.request(req.get("method", "GET"), base_url + path, **kwargs)
            actual_body = _response_body(response)
            passed = response.status_code == expected.get("status_code") and json_matches(expected.get("body"), actual_body)
            results.append({**item, "status": "passed" if passed else "failed",
                            "expected_status": expected.get("status_code"),
                            "actual_status": response.status_code,
                            **({"reason": "response status or body differs"} if not passed else {})})
        except httpx.HTTPError as exc:
            results.append({**item, "status": "failed", "reason": str(exc)})
    return results
