import os
import json
import re
import csv
from pathlib import Path
from datetime import datetime
import pandas as pd

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

DOMAINS = {
    "demographic": "Domain One - Demographic and Social Statistics",
    "economic": "Domain Two - Economic Statistics",
    "environmental": "Domain Three - Environmental Statistics",
    "governance": "Domain Four - Governance Statistics",
}

PROCESSED_DIR = Path("data/processed")
PROJECT_DATA_DIR = Path("D:/personal projects/Project data")


def extract_table_from_page(text):
    lines = text.strip().split("\n")
    rows = []
    for line in lines:
        parts = re.split(r"\s{2,}", line.strip())
        if len(parts) >= 2:
            rows.append(parts)
    return rows


def parse_pdf_with_pdfplumber(pdf_path):
    try:
        import pdfplumber
    except ImportError:
        print("pdfplumber not installed")
        return []

    tables = []
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
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
                                "raw_rows": len(table),
                            })
    except Exception as e:
        print(f"Error parsing {pdf_path}: {e}")
    return tables


def classify_domain(text):
    text_lower = text.lower()
    if any(word in text_lower for word in ["population", "labour", "education", "health", "demographic", "social protection", "housing", "culture"]):
        return "demographic"
    if any(word in text_lower for word in ["gdp", "economic", "business", "agriculture", "energy", "mining", "transport", "tourism", "prices", "macroeconomic", "revenue", "cooperative"]):
        return "economic"
    if any(word in text_lower for word in ["climate", "rainfall", "temperature", "water", "waste", "conservation", "environmental"]):
        return "environmental"
    if any(word in text_lower for word in ["voter", "court", "crime", "prison", "governance", "police", "probation", "election"]):
        return "governance"
    return "unknown"


def tables_to_dataframe(tables, domain):
    all_rows = []
    for table in tables:
        if table["domain"] != domain:
            continue
        headers = table["headers"]
        headers = [h.replace("\n", " ") if h else f"col_{i}" for i, h in enumerate(headers)]
        for row in table["data"]:
            while len(row) < len(headers):
                row.append("")
            row_dict = dict(zip(headers, row[: len(headers)]))
            row_dict["page"] = table["page"]
            all_rows.append(row_dict)

    if all_rows:
        df = pd.DataFrame(all_rows)
        df = df.replace(r"^\s*$", pd.NA, regex=True)
        return df
    return pd.DataFrame()


def save_domain_data(df, county_name, domain, sub_dir=""):
    county_name_clean = county_name.replace("'", "").replace(" ", "_")
    save_dir = PROCESSED_DIR / county_name_clean / domain
    if sub_dir:
        save_dir = save_dir / sub_dir
    save_dir.mkdir(parents=True, exist_ok=True)

    csv_path = save_dir / f"{domain}_data.csv"
    json_path = save_dir / f"{domain}_data.json"
    df.to_csv(str(csv_path), index=False)
    df.to_json(str(json_path), orient="records", indent=2)
    return csv_path


def process_county_pdf(county_name, pdf_path):
    print(f"Processing {county_name}...")
    tables = parse_pdf_with_pdfplumber(pdf_path)
    results = {}
    for domain in DOMAINS:
        df = tables_to_dataframe(tables, domain)
        if not df.empty:
            path = save_domain_data(df, county_name, domain)
            results[domain] = {"rows": len(df), "path": str(path)}
        else:
            results[domain] = {"rows": 0, "path": None}
    return results


def extract_county_name_from_pdf(pdf_path):
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            if pdf.pages:
                text = pdf.pages[0].extract_text() or pdf.pages[1].extract_text() or ""
                for county in COUNTIES:
                    if county.lower().replace("'", "") in text.lower().replace("'", ""):
                        return county
                match = re.search(r"(\w+)\s+County\s+Statistical\s+Abstract", text, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    for county in COUNTIES:
                        if county.lower().replace("'", "") == name.lower().replace("'", ""):
                            return county
    except:
        pass
    return None


def load_download_log():
    log_path = Path("data/download_log.json")
    if log_path.exists():
        with open(str(log_path)) as f:
            return json.load(f)
    return {}


def extract_all_counties():
    log = load_download_log()
    results = {}
    for county, info in log.items():
        if info.get("status") == "AVAILABLE":
            file_path = info.get("file_path", "")
            if file_path and os.path.exists(file_path):
                result = process_county_pdf(county, file_path)
                results[county] = result
    return results


def main():
    print("=" * 60)
    print("KNBS County Statistical Abstract - PDF Extraction Pipeline")
    print("=" * 60)

    log = load_download_log()
    available = {k: v for k, v in log.items() if v.get("status") == "AVAILABLE"}
    print(f"Found {len(available)} counties with available data")

    all_results = {}
    for county, info in available.items():
        file_path = info.get("file_path", "")
        if file_path and os.path.exists(file_path):
            result = process_county_pdf(county, file_path)
            all_results[county] = result
        else:
            print(f"  File not found for {county}: {file_path}")

    summary_path = PROCESSED_DIR / "_extraction_summary.json"
    with open(str(summary_path), "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nExtraction complete. Summary saved to {summary_path}")

    return all_results


if __name__ == "__main__":
    main()
