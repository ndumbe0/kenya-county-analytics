from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXTERNAL_DATA_DIR = Path(r"D:\personal projects\Project data")

COUNTIES: list[dict[str, str]] = [
    {"code": "001", "name": "Mombasa"},
    {"code": "002", "name": "Kwale"},
    {"code": "003", "name": "Kilifi"},
    {"code": "004", "name": "Tana River"},
    {"code": "005", "name": "Lamu"},
    {"code": "006", "name": "Taita-Taveta"},
    {"code": "007", "name": "Garissa"},
    {"code": "008", "name": "Wajir"},
    {"code": "009", "name": "Mandera"},
    {"code": "010", "name": "Marsabit"},
    {"code": "011", "name": "Isiolo"},
    {"code": "012", "name": "Meru"},
    {"code": "013", "name": "Tharaka-Nithi"},
    {"code": "014", "name": "Embu"},
    {"code": "015", "name": "Kitui"},
    {"code": "016", "name": "Machakos"},
    {"code": "017", "name": "Makueni"},
    {"code": "018", "name": "Nyandarua"},
    {"code": "019", "name": "Nyeri"},
    {"code": "020", "name": "Kirinyaga"},
    {"code": "021", "name": "Murang'a"},
    {"code": "022", "name": "Kiambu"},
    {"code": "023", "name": "Turkana"},
    {"code": "024", "name": "West Pokot"},
    {"code": "025", "name": "Samburu"},
    {"code": "026", "name": "Trans Nzoia"},
    {"code": "027", "name": "Uasin Gishu"},
    {"code": "028", "name": "Elgeyo-Marakwet"},
    {"code": "029", "name": "Nandi"},
    {"code": "030", "name": "Baringo"},
    {"code": "031", "name": "Laikipia"},
    {"code": "032", "name": "Nakuru"},
    {"code": "033", "name": "Narok"},
    {"code": "034", "name": "Kajiado"},
    {"code": "035", "name": "Kericho"},
    {"code": "036", "name": "Bomet"},
    {"code": "037", "name": "Kakamega"},
    {"code": "038", "name": "Vihiga"},
    {"code": "039", "name": "Bungoma"},
    {"code": "040", "name": "Busia"},
    {"code": "041", "name": "Siaya"},
    {"code": "042", "name": "Kisumu"},
    {"code": "043", "name": "Homa Bay"},
    {"code": "044", "name": "Migori"},
    {"code": "045", "name": "Kisii"},
    {"code": "046", "name": "Nyamira"},
    {"code": "047", "name": "Nairobi"},
]

DOMAIN_KEYWORDS = {
    "demographic_social": [
        "population",
        "labour",
        "education",
        "health",
        "social protection",
        "housing",
        "culture",
    ],
    "economic": [
        "gdp",
        "gross county product",
        "business",
        "agriculture",
        "energy",
        "mining",
        "transport",
        "tourism",
        "prices",
    ],
    "environmental": ["climate", "water", "waste", "conservation", "environment"],
    "governance": ["voters", "courts", "crime", "prison", "governance"],
}


def slugify(value: str) -> str:
    value = value.lower().replace("&", "and")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


COUNTY_BY_SLUG = {slugify(c["name"]): c for c in COUNTIES}
COUNTY_BY_CODE = {c["code"]: c for c in COUNTIES}


def normalize_county_name(value: str | None) -> str | None:
    if not value:
        return None
    clean = value.strip()
    slug = slugify(clean.replace("county", ""))
    aliases = {
        "taita_taveta": "taita_taveta",
        "taita_taveta_county": "taita_taveta",
        "elgeyo_marakwet": "elgeyo_marakwet",
        "trans_nzoia": "trans_nzoia",
        "tharaka_nithi": "tharaka_nithi",
        "muranga": "murang_a",
        "makueni_county": "makueni",
    }
    slug = aliases.get(slug, slug)
    county = COUNTY_BY_SLUG.get(slug)
    return county["name"] if county else None


def county_slug(name_or_code: str) -> str:
    county = COUNTY_BY_CODE.get(name_or_code) or COUNTY_BY_SLUG.get(slugify(name_or_code))
    if not county:
        normalized = normalize_county_name(name_or_code)
        if normalized:
            return slugify(normalized)
        raise KeyError(f"Unknown county: {name_or_code}")
    return slugify(county["name"])


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def baseline_county_metrics() -> list[dict[str, Any]]:
    """Deterministic seed metrics used until extracted KNBS tables are available."""
    rows: list[dict[str, Any]] = []
    for idx, county in enumerate(COUNTIES, start=1):
        urban_weight = 1.9 if county["name"] in {"Nairobi", "Mombasa", "Kiambu", "Nakuru", "Kisumu"} else 1.0
        population = int((380_000 + idx * 41_500) * urban_weight)
        gdp = round((2.4 + idx * 0.17) * urban_weight, 2)
        health = min(96, round(47 + (idx % 17) * 2.4 + urban_weight * 3, 1))
        education = min(5, round(2.3 + (idx % 11) * 0.21 + (0.4 if urban_weight > 1 else 0), 1))
        unemployment = max(5.0, round(22 - (education * 2.1) + (idx % 5), 1))
        growth = round(1.2 + (idx % 9) * 0.18, 2)
        development_score = round(gdp * 3.4 + health * 0.36 + education * 8 - unemployment * 0.8, 2)
        if development_score >= 64:
            tier = 1
        elif development_score >= 56:
            tier = 2
        elif development_score >= 48:
            tier = 3
        elif development_score >= 40:
            tier = 4
        else:
            tier = 5
        rows.append(
            {
                "county_code": county["code"],
                "county_name": county["name"],
                "slug": slugify(county["name"]),
                "availability_status": "BASELINE_PENDING_KNBS",
                "latest_year": 2025,
                "population": population,
                "population_growth_pct": growth,
                "gdp_contribution_pct": gdp,
                "health_score": health,
                "education_rating": education,
                "employment_rate": round(100 - unemployment, 1),
                "unemployment_rate": unemployment,
                "development_score": development_score,
                "development_tier": tier,
                "source": "deterministic_baseline",
            }
        )
    return rows


def load_county_metrics() -> list[dict[str, Any]]:
    csv_path = PROJECT_ROOT / "data" / "processed" / "county_metrics.csv"
    if csv_path.exists():
        import pandas as pd

        df = pd.read_csv(csv_path, dtype={"county_code": str})
        df["county_code"] = df["county_code"].str.zfill(3)
        return df.to_dict(orient="records")
    return baseline_county_metrics()


def classify_domain(text: str) -> str:
    lower = text.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            return domain
    return "unclassified"
