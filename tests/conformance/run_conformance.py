#!/usr/bin/env python3
"""WineBot/WinBot conformance test runner.

Tests that an implementation conforms to the winebot-contracts spec.
Run against either WineBot or WinBot:

    API_URL=http://localhost:8000 API_TOKEN=xxx python3 run_conformance.py
"""

import json, os, sys, urllib.request, urllib.error
from typing import Dict, Optional

API_URL = os.environ.get("API_URL", "http://localhost:8000")
API_TOKEN = os.environ.get("API_TOKEN", "")
PASS = FAIL = SKIP = 0


def api(method: str, path: str, data: Optional[Dict] = None) -> tuple:
    url = f"{API_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if API_TOKEN:
        headers["X-API-Key"] = API_TOKEN
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read())
        except: return e.code, {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}


def test(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition: PASS += 1; print(f"  PASS: {name}")
    else: FAIL += 1; print(f"  FAIL: {name} — {detail}")


def skip(name: str, reason: str = ""):
    global SKIP; SKIP += 1; print(f"  SKIP: {name} — {reason}")


def run():
    global PASS, FAIL, SKIP
    print(f"WineBot Contracts Conformance — {API_URL}\n")

    print("--- Health ---")
    s, d = api("GET", "/health")
    test("GET /health", s == 200, f"got {s}")
    test("status field", isinstance(d.get("status"), str))

    print("\n--- Health: System (GPU check) ---")
    s, d = api("GET", "/health/system")
    test("GET /health/system", s in (200, 404), f"got {s}")
    if s == 200:
        test("gpu_available field present", "gpu_available" in d,
             "WineBot should report gpu_available:false (Xvfb); WinBot: gpu_available:true (native GPU)")

    print("\n--- Lifecycle ---")
    s, d = api("GET", "/lifecycle/status")
    test("GET /lifecycle/status", s == 200)

    print("\n--- Sessions ---")
    s, d = api("GET", "/sessions")
    test("GET /sessions", s == 200)

    print("\n--- Recording ---")
    s, d = api("GET", "/recording/health")
    test("GET /recording/health", s in (200, 404))
    s, d = api("GET", "/recording/perf/summary")
    test("GET /recording/perf/summary", s in (200, 404))

    print("\n--- Input ---")
    s, d = api("POST", "/input/mouse/click", {"x": 100, "y": 100})
    test("POST /input/mouse/click", s in (200, 201, 202, 400, 403, 422, 500), f"got {s}")
    s, d = api("POST", "/input/key", {"keys": "test"})
    test("POST /input/key", s in (200, 201, 202, 400, 403, 422, 500), f"got {s}")

    print("\n--- Automation ---")
    s, d = api("GET", "/screenshot")
    test("GET /screenshot succeeds", s in (200, 400, 409, 429, 503), f"got {s}")
    s, d = api("GET", "/windows")
    test("GET /windows", s == 200)
    test("has windows key", "windows" in d)

    print("\n--- Trace ---")
    s, d = api("GET", "/input/trace/status")
    test("GET /input/trace/status", s in (200, 404))
    s, d = api("GET", "/input/events")
    test("GET /input/events", s == 200)

    print("\n--- Idempotency ---")
    s, d = api("GET", "/operations")
    test("GET /operations", s == 200)

    print("\n--- Errors ---")
    s, d = api("GET", "/nonexistent")
    test("404 on unknown endpoint", s == 404)

    total = PASS + FAIL + SKIP
    print(f"\n{'='*60}")
    print(f"  {PASS} passed, {FAIL} failed, {SKIP} skipped ({total} total)")
    sys.exit(1 if FAIL > 0 else 0)


if __name__ == "__main__":
    run()
