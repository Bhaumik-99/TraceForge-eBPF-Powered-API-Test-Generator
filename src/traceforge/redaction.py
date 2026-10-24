"""Redaction helpers applied before captured data is persisted."""
from __future__ import annotations
import json
import re
from collections.abc import Mapping
from urllib.parse import parse_qsl, urlencode

MAX_RECORDED_BODY_BYTES = 1_048_576
REDACTED = "[REDACTED]"
BODY_OMITTED_PREFIX = "[BODY OMITTED:"
SENSITIVE_KEY_RE = re.compile(
    r"(authorization|proxy-authorization|cookie|set-cookie|password|passwd|"
    r"secret|token|api[_-]?key|access[_-]?key|client[_-]?secret|"
    r"refresh[_-]?token|session[_-]?id)", re.IGNORECASE
)
TEXT_SECRET_RE = re.compile(
    r"""(?i)\b(password|passwd|secret|token|api[_-]?key|access[_-]?key)\b"""
    r"""(\s*[:=]\s*)(["']?)([^"'\s,;&}]+)"""
)

def is_sensitive_key(key: str) -> bool:
    return bool(SENSITIVE_KEY_RE.search(key))

def sanitize_headers(headers: Mapping[str, str]) -> dict[str, str]:
    hop = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
           "te", "trailer", "transfer-encoding", "upgrade", "host", "content-length"}
    return {k: v for k, v in headers.items()
            if k.lower() not in hop and not is_sensitive_key(k.lower())}

def sanitize_path(path: str, query: str = "") -> str:
    if not query:
        return path
    pairs = parse_qsl(query, keep_blank_values=True)
    safe = [(k, REDACTED if is_sensitive_key(k) else v) for k, v in pairs]
    return f"{path}?{urlencode(safe, doseq=True)}"

def _redact_json(value: object) -> object:
    if isinstance(value, dict):
        return {str(k): REDACTED if is_sensitive_key(str(k)) else _redact_json(v)
                for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_json(v) for v in value]
    if isinstance(value, str):
        return TEXT_SECRET_RE.sub(
            lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}{REDACTED}", value)
    return value

def sanitize_body(body: bytes, content_type: str | None = None,
                  max_bytes: int = MAX_RECORDED_BODY_BYTES) -> object:
    """Return safe JSON/text content or an omission marker; never raw binary."""
    if not body:
        return None
    if len(body) > max_bytes:
        return f"{BODY_OMITTED_PREFIX} exceeds {max_bytes} bytes]"
    ctype = (content_type or "").lower()
    if "application/octet-stream" in ctype or "multipart/" in ctype:
        return "[BODY OMITTED: binary or multipart body]"
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return "[BODY OMITTED: non-UTF-8 body]"
    if "json" in ctype or text.lstrip().startswith(("{", "[")):
        try:
            return _redact_json(json.loads(text))
        except json.JSONDecodeError:
            pass
    return TEXT_SECRET_RE.sub(
        lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}{REDACTED}", text)
