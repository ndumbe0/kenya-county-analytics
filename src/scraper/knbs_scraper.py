"""KNBS Scraper - local data consumption & live verification sync.

Scans data/raw/ for existing PDFs and cross-references with KNBS live site.
"""
import os, json, time, random, requests, re, urllib3
from datetime import datetime, timezone
from pathlib import Path

urllib3.disable_warnings()

COUNTIES = [
    "Mombasa","Kwale","Kilifi","Tana River","Lamu","Taita-Taveta",
    "Garissa","Wajir","Mandera","Marsabit","Isiolo","Meru",
    "Tharaka-Nithi","Embu","Kitui","Machakos","Makueni","Nyandarua",
    "Nyeri","Kirinyaga","Murang'a","Kiambu","Turkana","West Pokot",
    "Samburu","Trans Nzoia","Uasin Gishu","Elgeyo-Marakwet","Nandi",
    "Baringo","Laikipia","Nakuru","Narok","Kajiado","Kericho",
    "Bomet","Kakamega","Vihiga","Bungoma","Busia","Siaya",
    "Kisumu","Homa Bay","Migori","Kisii","Nyamira","Nairobi"
]

COUNTY_CODES = {c: i+1 for i, c in enumerate(COUNTIES)}

BASE_URL = "https://www.knbs.or.ke/county-statistical-abstracts/"
RAW_DIR = Path("D:/personal projects/kenya-county-analytics/data/raw")
PROCESSED_DIR = Path("D:/personal projects/kenya-county-analytics/data/processed")
LOG_PATH = PROCESSED_DIR / "download_log.json"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
HEADERS = {"User-Agent": UA, "Accept": "text/html,*/*", "Accept-Language": "en-US,en;q=0.5"}

COUNTY_NAME_PATTERNS = {
    "Murang'a": ["muranga", "murang'a", "muranga"],
    "Taita-Taveta": ["taita-taveta", "taita", "taveta"],
    "Elgeyo-Marakwet": ["elgeyo-marakwet", "elgeyo", "marakwet"],
    "Tharaka-Nithi": ["tharaka-nithi", "tharaka", "nithi"],
    "Trans Nzoia": ["trans-nzoia", "trans nzoia", "transnzoia"],
    "Uasin Gishu": ["uasin-gishu", "uasin gishu", "uasin"],
    "West Pokot": ["west-pokot", "west pokot", "westpokot"],
    "Tana River": ["tana-river", "tana river", "tanariver"],
    "Homa Bay": ["homa-bay", "homa bay", "homabay"],
}

def get_county_from_text(text):
    text_lower = text.lower().replace("county", "").strip()
    for county in COUNTIES:
        patterns = COUNTY_NAME_PATTERNS.get(county, [county.lower().replace("'", "").replace(" ", "-")])
        for p in patterns:
            if p in text_lower:
                return county
        slug = county.lower().replace("'", "").replace(" ", "_")
        if slug.replace("_", "") in text_lower.replace(" ", "").replace("-", ""):
            return county
    return None

def scan_local_raw():
    entries = {}
    if not RAW_DIR.exists():
        return entries
    for pdf_path in sorted(RAW_DIR.glob("**/*.pdf")):
        parts = pdf_path.relative_to(RAW_DIR).parts
        county = None
        year = None
        if len(parts) == 1:
            name_match = re.search(r'County_Abstract_(\d+)', pdf_path.stem)
            if name_match:
                idx = int(name_match.group(1))
                county = COUNTIES[idx - 1] if 1 <= idx <= 47 else None
            if not county:
                county = get_county_from_text(pdf_path.stem)
        elif len(parts) >= 2:
            county = parts[0]
            for c in COUNTIES:
                if c.lower().replace("'", "") == county.lower().replace("'", "").replace("_", " "):
                    county = c
                    break
            if len(parts) >= 3:
                try:
                    year = int(parts[1])
                except ValueError:
                    pass
        if not county:
            continue
        if not year:
            ym = re.search(r'(20\d{2})', pdf_path.name)
            if ym:
                year = int(ym.group(1))
        sz = os.path.getsize(pdf_path) if pdf_path.exists() else 0
        key = f"{county}_{year or 'unknown'}"
        if key not in entries:
            entries[key] = {
                "county_name": county,
                "file_status": "AVAILABLE",
                "local_path": str(pdf_path),
                "file_size_bytes": sz,
                "abstract_year": year,
                "last_verified_timestamp": datetime.now(timezone.utc).isoformat(),
                "live_knbs_url": None,
            }
    return entries

def fetch_live_pdfs():
    all_county_pdfs = {}
    for page_num in range(1, 20):
        url = f"{BASE_URL}page/{page_num}/" if page_num > 1 else BASE_URL
        try:
            resp = requests.get(url, headers=HEADERS, verify=False, timeout=30)
            html = resp.text
        except Exception:
            break
        if not html or "County Statistical Abstract" not in html:
            if page_num > 1:
                break
            continue
        pdf_urls = set(re.findall(r'https://www\.knbs\.or\.ke/wp-content/uploads/\d{4}/\d{2}/[^"\'<> ]+\.pdf', html))
        for url in pdf_urls:
            url_lower = url.lower()
            for county in COUNTIES:
                patterns = COUNTY_NAME_PATTERNS.get(county, [county.lower().replace("'", "").replace(" ", "-")])
                for p in patterns:
                    if p in url_lower:
                        if county not in all_county_pdfs:
                            all_county_pdfs[county] = url
                        break
        time.sleep(1.5)
    return all_county_pdfs

def cross_reference(local_entries, live_pdfs):
    merged = {}
    for key, entry in local_entries.items():
        county = entry["county_name"]
        merged[key] = entry
        if county in live_pdfs:
            merged[key]["live_knbs_url"] = live_pdfs[county]
    for county, pdf_url in live_pdfs.items():
        found = any(v["county_name"] == county for v in merged.values())
        if not found:
            ym = re.search(r'/(20\d{2})/', pdf_url)
            year = int(ym.group(1)) if ym else None
            key = f"{county}_{year or 'unknown'}_live"
            merged[key] = {
                "county_name": county,
                "file_status": "LIVE_SOURCE_REMOVED_RETAINED" if county in [v["county_name"] for v in local_entries.values()] else "AVAILABLE_ONLINE",
                "local_path": "",
                "file_size_bytes": 0,
                "abstract_year": year,
                "last_verified_timestamp": datetime.now(timezone.utc).isoformat(),
                "live_knbs_url": pdf_url,
            }
    return list(merged.values())

def write_log(entries):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "w") as f:
        json.dump(entries, f, indent=2, default=str)

def main():
    print("=" * 60)
    print("KNBS Local Scraper & Live Sync v2")
    print("=" * 60)
    print("\nScanning local data/raw/ directory...")
    local = scan_local_raw()
    print(f"  Found {len(local)} local PDF entries")

    print("\nFetching live KNBS county-statistical-abstracts pages...")
    live = fetch_live_pdfs()
    print(f"  Found {len(live)} live PDF references")

    print("\nCross-referencing local vs live...")
    merged = cross_reference(local, live)
    write_log(merged)
    available = sum(1 for e in merged if e.get("file_status") == "AVAILABLE")
    live_only = sum(1 for e in merged if e.get("file_status") == "AVAILABLE_ONLINE")
    retained = sum(1 for e in merged if e.get("file_status") == "LIVE_SOURCE_REMOVED_RETAINED")
    print(f"  AVAILABLE (local): {available}")
    print(f"  AVAILABLE_ONLINE:  {live_only}")
    print(f"  LIVE_SOURCE_REMOVED_RETAINED: {retained}")
    print(f"\nLog written to: {LOG_PATH}")
    return merged

if __name__ == "__main__":
    main()
