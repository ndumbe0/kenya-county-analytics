from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.common import (
    COUNTIES,
    DEFAULT_EXTERNAL_DATA_DIR,
    PROJECT_ROOT,
    baseline_county_metrics,
    ensure_dir,
    slugify,
    utc_now_iso,
    write_json,
)

GEOJSON_API = "https://api.github.com/repos/Mondieki/kenya-counties-subcounties/contents/geojson"


def _bbox_feature(county: dict[str, str], idx: int) -> dict[str, Any]:
    col = (idx - 1) % 8
    row = (idx - 1) // 8
    lon = 33.8 + col * 0.95
    lat = 4.4 - row * 0.95
    width = 0.72
    height = 0.62
    ring = [
        [lon, lat],
        [lon + width, lat],
        [lon + width, lat - height],
        [lon, lat - height],
        [lon, lat],
    ]
    return {
        "type": "Feature",
        "properties": {
            "county_code": county["code"],
            "county_name": county["name"],
            "name": county["name"],
            "boundary_source": "generated_fallback",
        },
        "geometry": {"type": "Polygon", "coordinates": [ring]},
    }


def _normalize_downloaded_feature(payload: dict[str, Any], county: dict[str, str]) -> dict[str, Any] | None:
    if payload.get("type") == "FeatureCollection":
        features = payload.get("features") or []
        if not features:
            return None
        feature = features[0]
    elif payload.get("type") == "Feature":
        feature = payload
    else:
        feature = {"type": "Feature", "properties": {}, "geometry": payload}
    feature.setdefault("properties", {})
    feature["properties"].update(
        {
            "county_code": county["code"],
            "county_name": county["name"],
            "name": county["name"],
            "boundary_source": "Mondieki/kenya-counties-subcounties",
        }
    )
    return feature


def download_county_geojson() -> dict[str, Any]:
    features: list[dict[str, Any]] = []
    try:
        listing = requests.get(GEOJSON_API, timeout=45).json()
        files = {
            slugify(Path(item["name"]).stem): item["download_url"]
            for item in listing
            if item.get("download_url")
        }
        for county in COUNTIES:
            url = files.get(slugify(county["name"]))
            if not url:
                features.append(_bbox_feature(county, int(county["code"])))
                continue
            payload = requests.get(url, timeout=45).json()
            feature = _normalize_downloaded_feature(payload, county)
            features.append(feature or _bbox_feature(county, int(county["code"])))
    except Exception:
        features = [_bbox_feature(county, int(county["code"])) for county in COUNTIES]

    geojson = {
        "type": "FeatureCollection",
        "name": "kenya_counties",
        "metadata": {
            "generated_at": utc_now_iso(),
            "source": "https://github.com/Mondieki/kenya-counties-subcounties with generated fallback",
        },
        "features": features,
    }
    path = ensure_dir(PROJECT_ROOT / "data" / "geospatial") / "kenya-counties.geojson"
    write_json(path, geojson)
    return geojson


def write_processed_metrics() -> pd.DataFrame:
    df = pd.DataFrame(baseline_county_metrics())
    processed = ensure_dir(PROJECT_ROOT / "data" / "processed")
    df.to_csv(processed / "county_metrics.csv", index=False)
    df.to_json(processed / "county_metrics.json", orient="records", indent=2)

    for row in df.to_dict(orient="records"):
        county_dir = ensure_dir(processed / row["slug"])
        pd.DataFrame(
            [
                {
                    "county_code": row["county_code"],
                    "county_name": row["county_name"],
                    "domain": "demographic_social",
                    "indicator": "Population",
                    "period": row["latest_year"],
                    "value": row["population"],
                    "unit": "persons",
                    "imputed": False,
                    "source": row["source"],
                },
                {
                    "county_code": row["county_code"],
                    "county_name": row["county_name"],
                    "domain": "economic",
                    "indicator": "GDP contribution",
                    "period": row["latest_year"],
                    "value": row["gdp_contribution_pct"],
                    "unit": "percent",
                    "imputed": False,
                    "source": row["source"],
                },
                {
                    "county_code": row["county_code"],
                    "county_name": row["county_name"],
                    "domain": "demographic_social",
                    "indicator": "Health score",
                    "period": row["latest_year"],
                    "value": row["health_score"],
                    "unit": "index",
                    "imputed": False,
                    "source": row["source"],
                },
            ]
        ).to_csv(county_dir / "unified_indicators.csv", index=False)
    return df


def write_download_log() -> None:
    entries = []
    for county in COUNTIES:
        county_dir = ensure_dir(DEFAULT_EXTERNAL_DATA_DIR / county["name"])
        entries.append(
            {
                "county_name": county["name"],
                "status": "DATA_UNAVAILABLE",
                "file_path": None,
                "size": 0,
                "year": None,
                "timestamp": utc_now_iso(),
                "note": f"Directory prepared at {county_dir}",
            }
        )
    write_json(PROJECT_ROOT / "data" / "raw" / "download_log.json", entries)


def write_visualization_exports(df: pd.DataFrame) -> None:
    tableau_dir = ensure_dir(PROJECT_ROOT / "visualizations" / "tableau")
    powerbi_dir = ensure_dir(PROJECT_ROOT / "visualizations" / "powerbi")
    df.to_csv(tableau_dir / "kenya_county_overview_extract.csv", index=False)
    df.to_csv(powerbi_dir / "county_development_index_extract.csv", index=False)
    (tableau_dir / "README.md").write_text(
        "# Tableau Dashboard Export\n\n"
        "Use `kenya_county_overview_extract.csv` and `data/geospatial/kenya-counties.geojson` "
        "to build the Population Map, Economic Trends, Health Indicators, and Education Analysis sheets. "
        "Save the packaged workbook here as `kenya_county_overview.twbx`.\n",
        encoding="utf-8",
    )
    (powerbi_dir / "README.md").write_text(
        "# Power BI Report Export\n\n"
        "Import `county_development_index_extract.csv` or the API endpoint "
        "`http://localhost:8000/api/v1/counties/`. Create Executive Summary, Detailed Metrics, "
        "Predictions, and Comparisons pages, then save `county_development_index.pbix` here.\n",
        encoding="utf-8",
    )


def main() -> None:
    df = write_processed_metrics()
    geojson = download_county_geojson()
    write_download_log()
    write_visualization_exports(df)
    print(
        json.dumps(
            {
                "metrics_rows": len(df),
                "geojson_features": len(geojson.get("features", [])),
                "processed": str(PROJECT_ROOT / "data" / "processed" / "county_metrics.csv"),
                "geojson": str(PROJECT_ROOT / "data" / "geospatial" / "kenya-counties.geojson"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
