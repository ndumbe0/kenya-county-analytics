"""Fast structured ingestion pipeline for KNBS County Statistical Abstract PDFs."""
import json, re
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

DOMAINS = ["demographic_social", "economic", "environmental", "governance"]

DOMAIN_KEYWORDS = {
    "demographic_social": ["population","labour","employment","education","literacy","health","housing","demographic","census"],
    "economic": ["gdp","gross county","business","agriculture","energy","mining","transport","tourism","prices","revenue"],
    "environmental": ["climate","rainfall","temperature","water","waste","conservation","forest","land"],
    "governance": ["voter","court","crime","prison","police","probation","election","justice","security"],
}

RAW = Path("D:/personal projects/kenya-county-analytics/data/raw")
PROCESSED = Path("D:/personal projects/kenya-county-analytics/data/processed")
MAX_PAGES = 10


def classify(text):
    lower = text.lower()
    best, best_score = "unclassified", 0
    for d, kws in DOMAIN_KEYWORDS.items():
        score = sum(2 if kw in lower else 0 for kw in kws)
        if score > best_score:
            best_score, best = score, d
    return best


def fast_parse(pdf_path):
    tables = []
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            for i, page in enumerate(pdf.pages):
                if i >= MAX_PAGES:
                    break
                text = page.extract_text() or ""
                if len(text.strip()) < 30:
                    continue
                domain = classify(text)
                tbls = page.extract_tables()
                for t in (tbls or []):
                    if t and len(t) > 1:
                        tables.append({"page": i+1, "domain": domain, "headers": t[0] or [], "data": t[1:]})
    except Exception:
        pass
    return tables


def to_df(tables, domain):
    rows = []
    for t in tables:
        if t["domain"] != domain:
            continue
        headers = [h.replace("\n", " ").strip() if h else f"c{i}" for i, h in enumerate(t["headers"])]
        for row in t["data"]:
            while len(row) < len(headers):
                row.append("")
            d = dict(zip(headers, [r.replace("\n", " ").strip() if r else "" for r in row[:len(headers)]]))
            d["page"] = t["page"]
            rows.append(d)
    return pd.DataFrame(rows).replace(r"^\s*$", pd.NA, regex=True) if rows else pd.DataFrame()


def save(df, county, domain):
    d = PROCESSED / county / domain
    d.mkdir(parents=True, exist_ok=True)
    df.to_csv(str(d / f"{domain}_data.csv"), index=False)
    df.to_json(str(d / f"{domain}_data.json"), orient="records", indent=2)


def run():
    print("=" * 60)
    print("KNBS PDF Extraction Pipeline (fast mode)")
    print(f"Max pages per PDF: {MAX_PAGES}")
    print("=" * 60)

    pdfs = sorted(RAW.glob("**/*.pdf"))
    print(f"Found {len(pdfs)} PDFs\n")

    extraction = {}
    for pdf in pdfs:
        rel = pdf.relative_to(RAW)
        county = rel.parts[0].replace("_", " ").replace("-", " ")
        for c in COUNTIES:
            if c.lower().replace("'","") == county.lower().replace("'","").replace(" ",""):
                county = c
                break
        else:
            continue
        yr = None
        for p in rel.parts:
            m = re.search(r'(20\d{2})', p)
            if m: yr = int(m.group(1)); break
        if not yr:
            m = re.search(r'(20\d{2})', pdf.name)
            if m: yr = int(m.group(1))

        sz_mb = pdf.stat().st_size / (1024*1024)
        print(f"  {county:<18} {yr}  {sz_mb:5.0f}MB", end=" ", flush=True)
        tables = fast_parse(pdf)
        results = {}
        for d in DOMAINS:
            df = to_df(tables, d)
            if not df.empty:
                save(df, county, d)
                results[d] = int(len(df))
            else:
                results[d] = 0
        total = sum(results.values())
        print(f"  {len(tables):2} tables  {total:3} rows")
        extraction[f"{county}_{yr}"] = {"county": county, "year": yr, "results": results}

    (PROCESSED / "extraction_log.json").write_text(
        json.dumps({"timestamp": datetime.now().isoformat(), "results": extraction}, indent=2, default=str),
        encoding="utf-8")

    # Build master dataset
    master = []
    for county in COUNTIES:
        entry = {"county_name": county, "domains": {}, "total_tables_extracted": 0}
        for d in DOMAINS:
            csv = PROCESSED / county / d / f"{d}_data.csv"
            if csv.exists():
                try:
                    df = pd.read_csv(str(csv))
                    entry["domains"][d] = {"rows": len(df), "file": str(csv)}
                    entry["total_tables_extracted"] += len(df)
                except Exception:
                    entry["domains"][d] = {"rows": 0}
            else:
                entry["domains"][d] = {"rows": 0}
        master.append(entry)

    (PROCESSED / "master_dataset.json").write_text(json.dumps(master, indent=2), encoding="utf-8")
    n = sum(1 for c in master if c["total_tables_extracted"] > 0)
    print(f"\nDone. {n}/47 counties have extracted data.")

if __name__ == "__main__":
    run()
