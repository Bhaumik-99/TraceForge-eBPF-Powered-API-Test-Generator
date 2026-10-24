# TraceForge — API Test Generation Prototype

TraceForge is a prototype for recording HTTP traffic through a local reverse proxy, redacting sensitive values, storing portable request/response fixtures, generating pytest regression tests, and replaying those fixtures against a newer API version. An optional bpftrace program observes Linux connection syscalls.

> **Architecture note:** HTTP bodies are recorded by the HTTP-aware proxy, not by eBPF. The optional eBPF/bpftrace probe logs connect() syscall metadata only. It does not inspect TLS or HTTP payloads and is not yet correlated with individual fixtures.

## Features
- HTTP proxy captures common methods, response status, elapsed time, and redacted request/response content.
- Credential headers are excluded; sensitive JSON keys, matching text secrets, and sensitive query values are redacted.
- Large, binary, and multipart bodies are omitted before storage.
- JSON fixture per request, written atomically.
- Generate a standalone pytest module from recorded fixtures.
- Replay fixtures against a target and compare status, JSON keys, values, and list lengths. Redacted values are treated as wildcards.
- Optional Linux bpftrace connection telemetry.
- Unit tests and GitHub Actions CI workflow.

## Quick start

Requires Python 3.10+. eBPF sample additionally requires Linux, bpftrace, and suitable privileges.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

PowerShell: `.venv\Scripts\Activate.ps1`.

### 1. Run the demo API (terminal 1)

```bash
traceforge demo --host 127.0.0.1 --port 9000
```

Endpoints: `/health`, `/products`, `/products/{product_id}`, `/orders`.

### 2. Run the recording proxy (terminal 2)

```bash
traceforge proxy --upstream http://127.0.0.1:9000 --host 127.0.0.1 --port 8000 --fixtures-dir fixtures
```

### 3. Generate traffic (terminal 3)

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/products
curl http://127.0.0.1:8000/products/1
curl -X POST http://127.0.0.1:8000/orders -H "Content-Type: application/json" -d '{"product_id":1,"quantity":2}'
```

Inspect the JSON fixtures under `fixtures/`. Only sanitized content is persisted.

### 4. Generate and run tests

```bash
traceforge generate --fixtures-dir fixtures --output generated/test_regression.py
TRACEFORGE_TARGET_URL=http://127.0.0.1:9000 pytest -q generated/test_regression.py
```

PowerShell:

```powershell
$env:TRACEFORGE_TARGET_URL = "http://127.0.0.1:9000"
pytest -q generated/test_regression.py
```

### 5. Replay against a candidate version

```bash
traceforge replay --fixtures-dir fixtures --base-url http://127.0.0.1:9000
```

Replay prints pass/fail/skip outcomes and returns non-zero if any case fails. Requests whose body was omitted cannot be faithfully replayed and are skipped.

## Optional Linux eBPF telemetry

```bash
sudo bpftrace ebpf/connect.bt
```

The probe reports process name, PID, file descriptor, return value, and connect() syscall execution duration. This duration is **not** the full TCP handshake time. TLS payloads are not inspected. Run only on systems you are authorized to observe.

## Security and limitations
- Redaction is a defensive baseline, not a guarantee against every secret format. Review fixtures before sharing.
- Fixtures may still contain sensitive business or personal data; treat them as sensitive.
- Credential headers are removed, so some authenticated routes require a safe test-only auth setup.
- The proxy buffers full bodies and is for local/prototype workloads, not streaming or production throughput.
- Binary and multipart bodies are omitted; fixtures exceeding 1 MiB are not replayable.
- eBPF emits standalone network telemetry; correlation with HTTP fixtures is future work.
- No performance or coverage benchmark claims are made by this prototype.

## Development
```bash
python -m pip install -e ".[dev]"
pytest -q
```

## License
MIT
