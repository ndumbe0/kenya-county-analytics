"""Structured ingestion pipeline for KNBS County Statistical Abstract PDFs.

Scans data/raw/, parses PDFs with pdfplumber, extracts 4 domain tables,
saves per-county/per-domain CSVs, and builds data/processed/master_dataset.json.
"""
import json, re, os, sys
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

def get_county_from_path(path):
    parts = path.relative_to(RAW_DIR).parts
    if len(parts) >= 2:
        folder_name = parts[0].replace("_", " ").replace("-", " ")
        for c in COUNTIES:
            if c.lower().replace("'", "").replace(" ", "") == folder_name.lower().replace("'", "").replace(" ", ""):
                return c
    stem = path.stem.lower()
    for c in COUNTIES:
        pattern = c.lower().replace("'", "").replace(" ", "").replace("-", "")
        if pattern in stem.replace("_", "").replace("-", "").replace(" ", ""):
            return c
    return None

def get_year_from_path(path):
    parts = path.relative_to(RAW_DIR).parts
    for p in parts:
        m = re.search(r'(20\d{2})', p)
        if m:
            return int(m.group(1))
    m = re.search(r'(20\d{2})', path.name)
    return int(m.group(1)) if m else None

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

def extract_tables(pdf_path):
    tables = []
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
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
                                "raw_rows": len(table),
                            })
    except Exception as e:
        print(f"  Error parsing {pdf_path.name}: {e}")
    return tables

def table_to_dataframe(tables, domain):
    all_rows = []
    for table in tables:
        if table["domain"] != domain:
            continue
        headers = [h.replace("\n", " ") if h else f"col_{i}" for i, h in enumerate(table["headers"])]
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

def save_domain_csv(df, county, domain, metadata):
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
        print(f"  Skipping {pdf_path.name}: could not identify county")
        return None, None, None
    print(f"  Processing {county} ({year or 'N/A'})...")
    tables = extract_tables(pdf_path)
    results = {}
    domain_counts = defaultdict(int)
    for table in tables:
        domain_counts[table["domain"]] += 1
    for domain in DOMAIN_KEYWORDS:
        df = table_to_dataframe(tables, domain)
        if not df.empty:
            path = save_domain_csv(df, county, domain, {})
            results[domain] = {"rows": len(df), "path": str(path)}
        else:
            results[domain] = {"rows": 0, "path": None}
    return county, year, results

def build_master_dataset(all_results):
    master = []
    for county in COUNTIES:
        county_dir = PROCESSED_DIR / county
        entry = {
            "county_name": county,
            "domains": {},
            "total_tables_extracted": 0,
        }
        for domain in DOMAIN_KEYWORDS:
            domain_dir = county_dir / domain
            csv_file = domain_dir / f"{domain}_data.csv"
            json_file = domain_dir / f"{domain}_data.json"
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
    print(f"\nMaster dataset written: {master_path}")
    return master

def main():
    print("=" * 60)
    print("KNBS County Statistical Abstract - PDF Extraction Pipeline")
    print("=" * 60)
    pdfs = sorted(RAW_DIR.glob("**/*.pdf"))
    print(f"Found {len(pdfs)} PDFs in data/raw/\n")
    all_results = {}
    processed_count = 0
    for pdf_path in pdfs:
        county, year, results = process_pdf(pdf_path)
        if county:
            all_results[f"{county}_{year}"] = {
                "county": county, "year": year, "results": results
            }
            processed_count += 1
    print(f"\nProcessed {processed_count} PDFs")
    extraction_log = {
        "timestamp": datetime.now().isoformat(),
        "total_pdfs_found": len(pdfs),
        "total_processed": processed_count,
        "results": all_results,
    }
    with open(PROCESSED_DIR / "extraction_log.json", "w") as f:
        json.dump(extraction_log, f, indent=2, default=str)
    master = build_master_dataset(all_results)
    summary = {"counties_with_data": sum(1 for c in master if c["total_tables_extracted"] > 0)}
    if summary["counties_with_data"] > 0:
        print(f"Counties with extracted data: {summary['counties_with_data']}/47")
    else:
        print("No tables were extractable from the current PDFs. The master_dataset.json structure is ready for when structured PDFs are ingested.")
    return master

if __name__ == "__main__":
    main()
