"""Structured ingestion pipeline for KNBS County Statistical Abstract PDFs.

Scans data/raw/{county}/{year}/, parses PDFs, extracts 4 domain tables,
saves per-county/per-domain CSVs, and builds data/processed/master_dataset.json.
"""
import json, re, os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import pandas as pd

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

DOMAIN_KEYWORDS = {
    "demographic_social": [
        "population", "labour", "employment", "education", "literacy",
        "health", "social protection", "housing", "culture", "demographic", "census"
    ],
    "economic": [
        "gdp", "gross county product", "business", "agriculture", "energy",
        "mining", "transport", "tourism", "prices", "economic", "revenue", "cooperative"
    ],
    "environmental": [
        "climate", "rainfall", "temperature", "water", "waste", "conservation",
        "environmental", "forest", "land"
    ],
    "governance": [
        "voter", "court", "crime", "prison", "governance", "police",
        "probation", "election", "justice", "security"
    ],
}

RAW_DIR = Path("D:/personal projects/kenya-county-analytics/data/raw")
PROCESSED_DIR = Path("D:/personal projects/kenya-county-analytics/data/processed")
MAX_PAGES = 30


def get_county_from_path(path):
    parts = path.relative_to(RAW_DIR).parts
    if len(parts) >= 1:
        folder = parts[0].replace("_", " ").replace("-", " ")
        for c in COUNTIES:
            if c.lower().replace("'", "").replace(" ", "") == folder.lower().replace("'", "").replace(" ", ""):
                return c
    return None


def get_year_from_path(path):
    parts = path.relative_to(RAW_DIR).parts
    for p in parts:
        m = re.search(r'(20\d{2})', p)
        if m:
            return int(m.group(1))
    return None


def classify_domain(text):
    lower = text.lower()
    max_score = 0
    best = "unclassified"
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(2 if kw in lower else 0 for kw in keywords)
        if score > max_score:
            max_score = score
            best = domain
    return best


def is_readable_text(text):
    if not text or len(text.strip()) < 20:
        return False
    cid_count = len(re.findall(r'\(cid:', text))
    return cid_count < len(text) * 0.3


def extract_tables_fast(pdf_path):
    tables = []
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            total_pages = len(pdf.pages)
            pages_to_check = min(total_pages, MAX_PAGES)
            for page_num in range(pages_to_check):
                page = pdf.pages[page_num]
                text = page.extract_text() or ""
                if not is_readable_text(text):
                    continue
                domain = classify_domain(text)
                tbls = page.extract_tables()
                if tbls:
                    for table in tbls:
                        if table and len(table) > 1:
                            tables.append({
                                "page": page_num + 1,
                                "domain": domain,
                                "headers": table[0] if table[0] else [],
                                "data": table[1:] if len(table) > 1 else [],
                            })
    except Exception as e:
        print(f"      Error: {e}")
    return tables


def table_to_dataframe(tables, domain):
    all_rows = []
    for table in tables:
        if table["domain"] != domain:
            continue
        headers = [h.replace("\n", " ").strip() if h else f"col_{i}" for i, h in enumerate(table["headers"])]
        for row in table["data"]:
            while len(row) < len(headers):
                row.append("")
            row_dict = dict(zip(headers, [r.replace("\n", " ").strip() if r else "" for r in row[:len(headers)]]))
            row_dict["page"] = table["page"]
            all_rows.append(row_dict)
    if all_rows:
        df = pd.DataFrame(all_rows)
        df = df.replace(r"^\s*$", pd.NA, regex=True)
        return df
    return pd.DataFrame()


def save_domain_data(df, county, domain):
    county_dir = PROCESSED_DIR / county / domain
    county_dir.mkdir(parents=True, exist_ok=True)
    csv_path = county_dir / f"{domain}_data.csv"
    df.to_csv(str(csv_path), index=False)
    json_path = county_dir / f"{domain}_data.json"
    df.to_json(str(json_path), orient="records", indent=2)
    return csv_path


def process_pdf(pdf_path):
    county = get_county_from_path(pdf_path)
    year = get_year_from_path(pdf_path)
    if not county:
        return None, None, {"error": "could not identify county"}

    sz_mb = pdf_path.stat().st_size / (1024 * 1024)
    print(f"    {county} ({year}) - {sz_mb:.0f}MB", end="", flush=True)
    tables = extract_tables_fast(pdf_path)
    print(f" - {len(tables)} tables", end="", flush=True)

    results = {}
    for domain in DOMAIN_KEYWORDS:
        df = table_to_dataframe(tables, domain)
        if not df.empty:
            path = save_domain_data(df, county, domain)
            results[domain] = {"rows": len(df), "path": str(path)}
        else:
            results[domain] = {"rows": 0, "path": None}

    total_rows = sum(v["rows"] for v in results.values() if v["rows"])
    print(f" - {total_rows} rows extracted")
    return county, year, results


def build_master_dataset():
    master = []
    for county in COUNTIES:
        entry = {
            "county_name": county,
            "domains": {},
            "total_tables_extracted": 0,
        }
        for domain in DOMAIN_KEYWORDS:
            csv_file = PROCESSED_DIR / county / domain / f"{domain}_data.csv"
            if csv_file.exists():
                try:
                    df = pd.read_csv(str(csv_file))
                    entry["domains"][domain] = {"rows": len(df), "file": str(csv_file)}
                    entry["total_tables_extracted"] += len(df)
                except Exception:
                    entry["domains"][domain] = {"rows": 0, "file": str(csv_file)}
            else:
                entry["domains"][domain] = {"rows": 0, "file": None}
        master.append(entry)
    master_path = PROCESSED_DIR / "master_dataset.json"
    with open(master_path, "w") as f:
        json.dump(master, f, indent=2, default=str)
    print(f"Master dataset written: {master_path}")
    return master


def main():
    print("=" * 60)
    print("KNBS County Statistical Abstract - PDF Extraction Pipeline")
    print("=" * 60)
    print(f"Max pages per PDF: {MAX_PAGES}")
    pdfs = sorted(RAW_DIR.glob("**/*.pdf"))
    print(f"Found {len(pdfs)} PDFs in data/raw/\n")
    all_results = {}
    processed_count = 0
    for pdf_path in pdfs:
        county, year, results = process_pdf(pdf_path)
        if county:
            key = f"{county}_{year}"
            all_results[key] = {"county": county, "year": year, "results": results}
            processed_count += 1

    print(f"\nProcessed {processed_count} PDFs")
    extraction_log = {
        "timestamp": datetime.now().isoformat(),
        "total_pdfs_found": len(pdfs),
        "total_processed": processed_count,
        "results": all_results,
    }
    (PROCESSED_DIR / "extraction_log.json").write_text(
        json.dumps(extraction_log, indent=2, default=str), encoding="utf-8"
    )
    master = build_master_dataset()
    summary = {"counties_with_data": sum(1 for c in master if c["total_tables_extracted"] > 0)}
    print(f"Counties with extracted data: {summary['counties_with_data']}/47")
    return master


if __name__ == "__main__":
    main()
