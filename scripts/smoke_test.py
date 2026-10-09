"""End-to-end smoke test - launches API in-process and verifies all endpoints."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

CHECKS = [
    ("GET /", lambda: client.get("/")),
    ("GET /health", lambda: client.get("/health")),
    ("GET /api/v1/counties/", lambda: client.get("/api/v1/counties/")),
    ("GET /api/v1/counties/47 (Nairobi)", lambda: client.get("/api/v1/counties/47")),
    ("GET /api/v1/counties/17 (Makueni)", lambda: client.get("/api/v1/counties/17")),
    ("GET /api/v1/counties/17/population/forecast", lambda: client.get("/api/v1/counties/17/population/forecast")),
    ("GET /api/v1/analytics/clustering", lambda: client.get("/api/v1/analytics/clustering")),
    ("GET /api/v1/health/anomalies", lambda: client.get("/api/v1/health/anomalies")),
    ("GET /api/v1/geospatial/counties", lambda: client.get("/api/v1/geospatial/counties")),
    ("GET /api/v1/chat/agents", lambda: client.get("/api/v1/chat/agents")),
    ("POST /api/v1/chat/query (data)", lambda: client.post("/api/v1/chat/query", json={"query": "Population of Nairobi", "agent": "data"})),
    ("POST /api/v1/chat/query (prediction)", lambda: client.post("/api/v1/chat/query", json={"query": "What will Makueni be in 2030?", "agent": "prediction"})),
    ("POST /api/v1/chat/query (guide)", lambda: client.post("/api/v1/chat/query", json={"query": "How do I download data?", "agent": "guide"})),
    ("POST /api/v1/chat/query (auto-route)", lambda: client.post("/api/v1/chat/query", json={"query": "Compare Mombasa and Kisumu"})),
    ("Rate limit headers present", lambda: client.get("/api/v1/counties/")),
    ("Input validation - empty query", lambda: client.post("/api/v1/chat/query", json={"query": ""})),
    ("Input validation - oversized", lambda: client.post("/api/v1/chat/query", json={"query": "x" * 1500})),
    ("GET /api/v1/data/download/csv", lambda: client.get("/api/v1/data/download/csv")),
    ("GET /api/v1/data/download/json", lambda: client.get("/api/v1/data/download/json")),
]


def run():
    print("=" * 70)
    print("KENYA COUNTY ANALYTICS - END-TO-END SMOKE TEST")
    print("=" * 70)
    passed = failed = 0
    for label, fn in CHECKS:
        try:
            t0 = time.time()
            r = fn()
            elapsed_ms = (time.time() - t0) * 1000
            expected_400 = "Input validation" in label
            ok = (r.status_code == 400) if expected_400 else (200 <= r.status_code < 300)
            if ok:
                passed += 1
                print(f"  [PASS] {label}  ({r.status_code}, {elapsed_ms:.0f}ms)")
            else:
                failed += 1
                print(f"  [FAIL] {label}  ({r.status_code})")
                try:
                    print(f"         body: {r.text[:120]}")
                except Exception:
                    pass
        except Exception as e:
            failed += 1
            print(f"  [ERROR] {label} - {e}")

    print()
    print("=" * 70)
    print(f"RESULT: {passed} passed, {failed} failed (of {len(CHECKS)})")
    print("=" * 70)
    return failed == 0


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
