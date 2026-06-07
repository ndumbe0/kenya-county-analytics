"""Scan Project data folder and rebuild download_log.json to reflect actual files."""
import json
import os
import re
from datetime import datetime
from pathlib import Path

COUNTIES = [
    "Mombasa", "Kwale", "Kilifi", "Tana River", "Lamu", "Taita-Taveta",
    "Garissa", "Wajir", "Mandera", "Marsabit", "Isiolo", "Meru",
    "Tharaka-Nithi", "Embu", "Kitui", "Machakos", "Makueni", "Nyandarua",
    "Nyeri", "Kirinyaga", "Murang'a", "Kiambu", "Turkana", "West Pokot",
    "Samburu", "Trans Nzoia", "Uasin Gishu", "Elgeyo-Marakwet", "Nandi",
    "Baringo", "Laikipia", "Nakuru", "Narok", "Kajiado", "Kericho",
    "Bomet", "Kakamega", "Vihiga", "Bungoma", "Busia", "Siaya",
    "Kisumu", "Homa Bay", "Migori", "Kisii", "Nyamira", "Nairobi"
]
COUNTY_CODES = {c: i + 1 for i, c in enumerate(COUNTIES)}
PROJECT_DATA = Path("D:/personal projects/Project data")
ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "data" / "processed" / "download_log.json"


def year_from(filename):
    m = re.search(r'(20\d{2})', filename)
    return int(m.group(1)) if m else None


def main():
    log = {}
    for county in COUNTIES:
        d = PROJECT_DATA / county
        pdfs = sorted(d.glob("*.pdf"), key=lambda p: p.name) if d.exists() else []
        if pdfs:
            latest = max(pdfs, key=lambda p: year_from(p.name) or 0)
            log[county] = {
                "county_name": county,
                "county_code": COUNTY_CODES[county],
                "status": "AVAILABLE",
                "file_path": str(latest).replace("\\", "/"),
                "size": os.path.getsize(latest),
                "year": year_from(latest.name),
                "all_files": [str(p).replace("\\", "/") for p in pdfs],
                "file_count": len(pdfs),
                "timestamp": datetime.fromtimestamp(os.path.getmtime(latest)).isoformat(),
            }
        else:
            log[county] = {
                "county_name": county,
                "county_code": COUNTY_CODES[county],
                "status": "DATA_UNAVAILABLE",
                "file_path": "",
                "size": 0,
                "year": None,
                "all_files": [],
                "file_count": 0,
                "timestamp": datetime.now().isoformat(),
            }
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "w") as f:
        json.dump(log, f, indent=2)
    avail = sum(1 for v in log.values() if v["status"] == "AVAILABLE")
    print(f"Refreshed log: {avail}/47 counties have data")
    return log


if __name__ == "__main__":
    main()
