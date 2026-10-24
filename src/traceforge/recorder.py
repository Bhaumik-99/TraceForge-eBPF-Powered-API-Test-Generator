"""Filesystem-backed redacted HTTP fixture recorder."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
from traceforge.redaction import sanitize_body, sanitize_headers, sanitize_path

def load_fixtures(fixtures_dir: Path) -> list[dict[str, Any]]:
    if not fixtures_dir.exists():
        return []
    fixtures = []
    for path in sorted(fixtures_dir.glob("*.json")):
        try:
            fixture = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Could not read fixture {path}: {exc}") from exc
        if not isinstance(fixture, dict) or not {"request", "response"} <= fixture.keys():
            raise ValueError(f"Invalid TraceForge fixture schema: {path}")
        fixture.setdefault("id", path.stem)
        fixtures.append(fixture)
    return fixtures

class FixtureRecorder:
    """Write one sanitized JSON file per request/response pair."""
    def __init__(self, directory: Path | str):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def record(self, *, method: str, path: str, query: str = "",
               request_headers: dict[str, str], request_body: bytes,
               request_content_type: str | None, status_code: int,
               response_headers: dict[str, str], response_body: bytes,
               response_content_type: str | None, elapsed_ms: float) -> Path:
        fixture_id = uuid4().hex
        data = {
            "schema_version": 1, "id": fixture_id,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_ms": round(max(0.0, elapsed_ms), 3),
            "request": {
                "method": method.upper(), "path": sanitize_path(path, query),
                "headers": sanitize_headers(request_headers),
                "body": sanitize_body(request_body, request_content_type),
            },
            "response": {
                "status_code": int(status_code),
                "headers": sanitize_headers(response_headers),
                "body": sanitize_body(response_body, response_content_type),
            },
        }
        final_path = self.directory / f"{fixture_id}.json"
        temp_path = self.directory / f".{fixture_id}.tmp"
        temp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
        temp_path.replace(final_path)
        return final_path
