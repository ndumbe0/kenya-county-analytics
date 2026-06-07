import json
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/counties", tags=["Counties"])

ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = ROOT / "data" / "processed"
DOWNLOAD_LOG = ROOT / "data" / "raw" / "download_log.json"

COUNTY_CODES = {
    "Mombasa": 1, "Kwale": 2, "Kilifi": 3, "Tana River": 4, "Lamu": 5,
    "Taita-Taveta": 6, "Garissa": 7, "Wajir": 8, "Mandera": 9, "Marsabit": 10,
    "Isiolo": 11, "Meru": 12, "Tharaka-Nithi": 13, "Embu": 14, "Kitui": 15,
    "Machakos": 16, "Makueni": 17, "Nyandarua": 18, "Nyeri": 19, "Kirinyaga": 20,
    "Murang'a": 21, "Kiambu": 22, "Turkana": 23, "West Pokot": 24, "Samburu": 25,
    "Trans Nzoia": 26, "Uasin Gishu": 27, "Elgeyo-Marakwet": 28, "Nandi": 29,
    "Baringo": 30, "Laikipia": 31, "Nakuru": 32, "Narok": 33, "Kajiado": 34,
    "Kericho": 35, "Bomet": 36, "Kakamega": 37, "Vihiga": 38, "Bungoma": 39,
    "Busia": 40, "Siaya": 41, "Kisumu": 42, "Homa Bay": 43, "Migori": 44,
    "Kisii": 45, "Nyamira": 46, "Nairobi": 47,
}
CODE_TO_COUNTY = {v: k for k, v in COUNTY_CODES.items()}


def load_json(path: Path) -> Optional[dict]:
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            return None
    return None


def load_ml_data() -> dict:
    ml_dir = PROCESSED_DIR / "ml"
    return {
        "population": load_json(ml_dir / "population_forecast.json") or {},
        "clusters": load_json(ml_dir / "economic_clusters.json") or {},
        "health": load_json(ml_dir / "health_anomalies.json") or {},
        "education": load_json(ml_dir / "education_employment.json") or {},
    }


@router.get("/")
def list_counties():
    ml_data = load_ml_data()
    clusters = ml_data.get("clusters", {}).get("clusters", {})

    log = load_json(DOWNLOAD_LOG) or {}
    metrics_csv = PROCESSED_DIR / "county_metrics.csv"
    metrics_by_name: dict = {}
    if metrics_csv.exists():
        import pandas as pd
        df = pd.read_csv(metrics_csv, dtype={"county_code": str})
        df["county_code"] = df["county_code"].str.zfill(3)
        metrics_by_name = {row["county_name"]: row.to_dict() for _, row in df.iterrows()}

    out = []
    for name, code in sorted(COUNTY_CODES.items(), key=lambda x: x[1]):
        county_data_path = PROCESSED_DIR / name
        has_extracted = county_data_path.exists() and any(county_data_path.iterdir())
        log_entry = log.get(name, {})
        available = has_extracted or log_entry.get("status") == "AVAILABLE"
        m = metrics_by_name.get(name, {})
        out.append({
            "code": code,
            "name": name,
            "data_available": available,
            "data_status": "AVAILABLE" if available else "DATA_UNAVAILABLE",
            "latest_year": log_entry.get("year") or m.get("latest_year"),
            "source_file": log_entry.get("file_path"),
            "population": int(m.get("population", 0)) if m else 0,
            "development_tier": m.get("development_tier", 5),
            "tier_label": clusters.get(name, {}).get("tier_label"),
            "development_score": m.get("development_score"),
        })
    return {"count": len(out), "counties": out}


@router.get("/{code}")
def get_county(code: int):
    county_name = CODE_TO_COUNTY.get(code)
    if not county_name:
        raise HTTPException(status_code=404, detail="County not found")

    ml_data = load_ml_data()

    population = ml_data.get("population", {}).get(county_name, {})
    cluster = ml_data.get("clusters", {}).get("county_clusters", {}).get(county_name, {})
    health = ml_data.get("health", {}).get("county_results", {}).get(county_name, {})
    education = ml_data.get("education", {}).get("county_results", {}).get(county_name, {})

    county_dir = PROCESSED_DIR / county_name
    domains = {}
    if county_dir.exists():
        for domain_dir in sorted(county_dir.iterdir()):
            if domain_dir.is_dir():
                combined = domain_dir / f"{domain_dir.name}_combined.json"
                if combined.exists():
                    dom_data = load_json(combined)
                    domains[domain_dir.name] = {
                        "tables_count": len(dom_data) if isinstance(dom_data, list) else 1,
                        "data_preview": (dom_data or [])[:3],
                    }
                else:
                    csv_files = list(domain_dir.glob("*.csv"))
                    domains[domain_dir.name] = {"tables_count": len(csv_files), "data_preview": []}

    return {
        "code": code,
        "name": county_name,
        "domains": domains,
        "population_forecast": population,
        "development_cluster": cluster,
        "health_metrics": health,
        "education_employment": education,
    }


@router.get("/{code}/population/forecast")
def get_population_forecast(code: int):
    county_name = CODE_TO_COUNTY.get(code)
    if not county_name:
        raise HTTPException(status_code=404, detail="County not found")
    ml_data = load_ml_data()
    forecast = ml_data.get("population", {}).get(county_name, {})
    if not forecast:
        raise HTTPException(status_code=404, detail="No forecast data available")
    return forecast
