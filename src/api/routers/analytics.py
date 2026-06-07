import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
import pandas as pd
import io

router = APIRouter(prefix="/api/v1", tags=["Analytics"])
ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = ROOT / "data" / "processed"
DOWNLOAD_LOG = ROOT / "data" / "processed" / "download_log.json"
METRICS_CSV = PROCESSED_DIR / "county_metrics.csv"


def load_json(path):
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return None
    return None


@router.get("/analytics/clustering")
def get_clustering():
    clusters = load_json(PROCESSED_DIR / "ml" / "economic_clusters.json")
    if not clusters:
        raise HTTPException(status_code=404, detail="No clustering data available")
    return clusters


@router.get("/health/anomalies")
def get_health_anomalies():
    health = load_json(PROCESSED_DIR / "ml" / "health_anomalies.json")
    if not health:
        raise HTTPException(status_code=404, detail="No health data available")
    return health


@router.get("/analytics/education")
def get_education():
    edu = load_json(PROCESSED_DIR / "ml" / "education_employment.json")
    if not edu:
        raise HTTPException(status_code=404, detail="No education data available")
    return edu


@router.get("/analytics/population")
def get_population():
    pop = load_json(PROCESSED_DIR / "ml" / "population_forecast.json")
    if not pop:
        raise HTTPException(status_code=404, detail="No population data available")
    return pop


@router.get("/data/download/{format}")
def download_data(format: str):
    if format not in ("csv", "json", "excel"):
        raise HTTPException(status_code=400, detail="Format must be csv, json, or excel")

    ml_dir = PROCESSED_DIR / "ml"
    clusters = load_json(ml_dir / "economic_clusters.json") or {}
    health = load_json(ml_dir / "health_anomalies.json") or {}
    employment = load_json(ml_dir / "education_employment.json") or {}
    population = load_json(ml_dir / "population_forecast.json") or {}
    metrics_df = pd.read_csv(METRICS_CSV, dtype={"county_code": str}) if METRICS_CSV.exists() else pd.DataFrame()
    if not metrics_df.empty:
        metrics_df["county_code"] = metrics_df["county_code"].str.zfill(3)
        metrics_by_name = {row["county_name"]: row.to_dict() for _, row in metrics_df.iterrows()}
    else:
        metrics_by_name = {}
    raw_log = load_json(DOWNLOAD_LOG) or []
    log_by_name = {}
    if isinstance(raw_log, list):
        for entry in raw_log:
            if isinstance(entry, dict) and entry.get("county_name"):
                log_by_name[entry["county_name"]] = entry
    elif isinstance(raw_log, dict):
        log_by_name = raw_log

    county_clusters = clusters.get("clusters", {})
    health_results = health.get("county_results", {})
    edu_results = employment.get("county_results", {})
    all_names = set(metrics_by_name) | set(county_clusters) | set(health_results) | set(edu_results) | set(population)
    rows = []
    for county in sorted(all_names):
        m = metrics_by_name.get(county, {})
        c = county_clusters.get(county, {})
        h = health_results.get(county, {})
        e = edu_results.get(county, {})
        p = population.get(county, {})
        le = log_by_name.get(county, {})
        rows.append({
            "county": county,
            "county_code": m.get("county_code", ""),
            "population": m.get("population"),
            "population_growth_pct": m.get("population_growth_pct"),
            "gdp_contribution_pct": m.get("gdp_contribution_pct"),
            "health_score": m.get("health_score") or h.get("health_score"),
            "education_rating": m.get("education_rating"),
            "employment_rate": m.get("employment_rate"),
            "unemployment_rate": m.get("unemployment_rate"),
            "development_score": m.get("development_score"),
            "development_tier": m.get("development_tier") or c.get("tier"),
            "tier_label": c.get("tier_label"),
            "is_health_anomaly": h.get("is_anomaly"),
            "anomaly_score": h.get("anomaly_score"),
            "predicted_employment_rate": e.get("predicted_employment_rate"),
            "employment_residuals": e.get("residuals"),
            "population_2025_forecast": p.get("forecast", {}).get("2025"),
            "population_2030_forecast": p.get("forecast", {}).get("2030"),
            "data_status": le.get("file_status") or le.get("status", "DATA_UNAVAILABLE"),
            "source_year": le.get("abstract_year") or le.get("year"),
        })

    df = pd.DataFrame(rows)

    if format == "json":
        content = df.to_json(orient="records", indent=2)
        return StreamingResponse(iter([content]), media_type="application/json",
                                 headers={"Content-Disposition": "attachment; filename=kenya_county_data.json"})
    elif format == "csv":
        content = df.to_csv(index=False)
        return StreamingResponse(iter([content]), media_type="text/csv",
                                 headers={"Content-Disposition": "attachment; filename=kenya_county_data.csv"})
    else:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="County Data")
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers={"Content-Disposition": "attachment; filename=kenya_county_data.xlsx"})
