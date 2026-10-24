"""Command line interface for TraceForge."""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="traceforge", description="Capture HTTP fixtures and generate API regression tests.")
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="run the sample store API")
    demo.add_argument("--host", default="127.0.0.1")
    demo.add_argument("--port", type=int, default=9000)
    proxy = commands.add_parser("proxy", help="run the HTTP capture proxy")
    proxy.add_argument("--upstream", required=True)
    proxy.add_argument("--host", default="127.0.0.1")
    proxy.add_argument("--port", type=int, default=8000)
    proxy.add_argument("--fixtures-dir", default="fixtures")
    gen = commands.add_parser("generate", help="generate pytest tests")
    gen.add_argument("--fixtures-dir", default="fixtures")
    gen.add_argument("--output", default="generated/test_regression.py")
    replay = commands.add_parser("replay", help="replay fixtures against a target API")
    replay.add_argument("--fixtures-dir", default="fixtures")
    replay.add_argument("--base-url", required=True)
    replay.add_argument("--timeout", type=float, default=10.0)
    return parser

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        import uvicorn
        uvicorn.run("traceforge.demo_api:app", host=args.host, port=args.port)
        return 0
    if args.command == "proxy":
        import uvicorn
        os.environ["TRACEFORGE_UPSTREAM_URL"] = args.upstream
        os.environ["TRACEFORGE_FIXTURE_DIR"] = args.fixtures_dir
        uvicorn.run("traceforge.proxy:app", host=args.host, port=args.port)
        return 0
    if args.command == "generate":
        from traceforge.generator import generate_tests
        try:
            output = generate_tests(Path(args.fixtures_dir), Path(args.output))
        except ValueError as exc:
            print(f"TraceForge: {exc}", file=sys.stderr)
            return 2
        print(f"Generated regression tests: {output}")
        print("Set TRACEFORGE_TARGET_URL=http://host:port and run pytest on that file.")
        return 0
    if args.command == "replay":
        from traceforge.replay import replay_fixtures
        try:
            results = replay_fixtures(Path(args.fixtures_dir), args.base_url, args.timeout)
        except ValueError as exc:
            print(f"TraceForge: {exc}", file=sys.stderr)
            return 2
        for result in results:
            detail = result.get("reason", "")
            if "actual_status" in result:
                detail = f"expected HTTP {result['expected_status']}, got HTTP {result['actual_status']}"
            print(f"{result['status'].upper():7} {result.get('method')} {result.get('path')} {detail}".rstrip())
        passed = sum(x["status"] == "passed" for x in results)
        failed = sum(x["status"] == "failed" for x in results)
        skipped = sum(x["status"] == "skipped" for x in results)
        print(f"\\nReplay summary: {passed} passed, {failed} failed, {skipped} skipped")
        return 1 if failed else 0
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
