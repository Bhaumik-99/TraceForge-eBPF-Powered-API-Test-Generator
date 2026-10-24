"""Local HTTP reverse proxy that stores redacted request/response fixtures."""
from __future__ import annotations
import os
from time import perf_counter
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from traceforge.recorder import FixtureRecorder

app = FastAPI(title="TraceForge Capture Proxy",
              description="HTTP-aware traffic capture for local API regression testing.")
UPSTREAM_URL = os.getenv("TRACEFORGE_UPSTREAM_URL", "http://127.0.0.1:9000").rstrip("/")
FIXTURE_DIR = os.getenv("TRACEFORGE_FIXTURE_DIR", "fixtures")
RECORDER = FixtureRecorder(FIXTURE_DIR)
HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
       "te", "trailer", "transfer-encoding", "upgrade", "host", "content-length"}
METHODS = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

async def _forward(request: Request) -> Response:
    body = await request.body()
    url = f"{UPSTREAM_URL}{request.url.path}"
    if request.url.query:
        url += f"?{request.url.query}"
    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP}
    started = perf_counter()
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=False) as client:
            upstream = await client.request(request.method, url, headers=headers, content=body)
    except httpx.HTTPError as exc:
        return JSONResponse(status_code=502, content={
            "error": "upstream_unavailable", "detail": str(exc), "upstream": UPSTREAM_URL})
    elapsed_ms = (perf_counter() - started) * 1000.0
    RECORDER.record(
        method=request.method, path=request.url.path, query=request.url.query,
        request_headers=dict(request.headers), request_body=body,
        request_content_type=request.headers.get("content-type"),
        status_code=upstream.status_code, response_headers=dict(upstream.headers),
        response_body=upstream.content,
        response_content_type=upstream.headers.get("content-type"), elapsed_ms=elapsed_ms)
    response_headers = {k: v for k, v in upstream.headers.items() if k.lower() not in HOP}
    return Response(content=upstream.content, status_code=upstream.status_code,
                    headers=response_headers)

@app.api_route("/", methods=METHODS)
async def proxy_root(request: Request):
    return await _forward(request)

@app.api_route("/{path:path}", methods=METHODS)
async def proxy_path(request: Request, path: str):
    return await _forward(request)
