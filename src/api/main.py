"""Kenya County Analytics API - FastAPI application.

Endpoint map:
  GET  /                              - banner
  GET  /health                        - liveness
  GET  /api/v1/counties/              - all 47 counties with status  (counties router)
  GET  /api/v1/counties/{code}        - one county deep-dive        (counties router)
  GET  /api/v1/counties/{code}/population/forecast  - 5y forecast    (counties router)
  GET  /api/v1/analytics/clustering   - K-Means tiers                (analytics router)
  GET  /api/v1/health/anomalies       - Isolation Forest alerts      (analytics router)
  GET  /api/v1/analytics/education    - employment + SHAP            (analytics router)
  GET  /api/v1/analytics/population   - all population forecasts     (analytics router)
  GET  /api/v1/analytics/all          - live in-memory ML run        (main, in-process)
  GET  /api/v1/data/download/{format} - CSV/JSON/Excel export        (analytics router)
  GET  /api/v1/geospatial/counties    - Kenya county GeoJSON         (main)
  GET  /api/v1/chat/agents            - list AI agents               (chat router)
  POST /api/v1/chat/query             - ask an agent                 (chat router)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request

from src.api.routers import analytics, chat, counties

app = FastAPI(
    title="Kenya County Analytics API",
    version="1.0.0",
    description="47-county statistical analytics platform for Kenya",
)

ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:8501,http://localhost:8502,http://127.0.0.1:8501,http://localhost:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=ROOT / "src" / "static"), name="static")


# ---------------- Rate limiter + security headers ----------------
from collections import defaultdict
from time import time as _now

_RATE_BUCKET: dict = defaultdict(list)
_RATE_LIMIT = int(os.environ.get("RATE_LIMIT_PER_MIN", "100"))
_RATE_WINDOW = 60


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    ip = (request.client.host if request.client else "unknown")
    now = _now()
    bucket = _RATE_BUCKET[ip]
    bucket[:] = [t for t in bucket if now - t < _RATE_WINDOW]
    if len(bucket) >= _RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": f"Rate limit exceeded. Max {_RATE_LIMIT} req/min."},
        )
    bucket.append(now)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ---------------- Routers ----------------
app.include_router(counties.router)
app.include_router(analytics.router)
app.include_router(chat.router)


# ---------------- Top-level endpoints ----------------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    html_path = ROOT / "src" / "templates" / "dashboard.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return FileResponse(html_path)


@app.get("/")
def root():
    return {
        "message": "Kenya County Analytics API",
        "version": "1.0.0",
        "counties": 47,
        "endpoints": {
            "dashboard": "/dashboard",
            "counties": "/api/v1/counties/",
            "analytics": "/api/v1/analytics/all",
            "chat": "/api/v1/chat/agents",
            "geospatial": "/api/v1/geospatial/counties",
            "docs": "/docs",
        },
    }


@app.get("/health")
def health_check():
    from datetime import datetime
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/v1/geospatial/counties")
def get_geojson():
    geo_path = ROOT / "data" / "geospatial" / "kenya-counties.geojson"
    if not geo_path.exists():
        raise HTTPException(404, "GeoJSON not found")
    with open(geo_path, encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/v1/analytics/all")
def get_all_analytics():
    """Run all ML models in-process and return combined results."""
    from src.ml.population_forecaster import run_all_models
    return run_all_models()


if __name__ == "__main__":
    import uvicorn
    import socket

    def find_open_port(default_port):
        for port in range(default_port, default_port + 10):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) != 0:
                    return port
        return default_port

    initial_port = int(os.environ.get("PORT", 8000))
    final_port = find_open_port(initial_port)
    if final_port != initial_port:
        print(f"Port {initial_port} in use, using port {final_port}")
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=final_port, reload=False)
