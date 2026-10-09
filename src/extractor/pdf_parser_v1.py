import camelot
import pdfplumber
import pandas as pd
from pathlib import Path

RAW_DIR = Path("D:/personal projects/kenya-county-analytics/data/raw")
PROCESSED_DIR = Path("D:/personal projects/kenya-county-analytics/data/processed")

def extract_all():
    for pdf_path in RAW_DIR.glob("**/*.pdf"):
        county = pdf_path.parent.name
        year = pdf_path.parent.parent.name
        out_dir = PROCESSED_DIR / county / "tables"
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            tables = camelot.read_pdf(str(pdf_path), pages="1-end", flavor="lattice")
            for i, table in enumerate(tables):
                df = table.df
                df.to_csv(out_dir / f"table_{i}.csv", index=False)
            with pdfplumber.open(pdf_path) as pdf:
                text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                (out_dir / "full_text.txt").write_text(text, encoding="utf-8")
            print(f"Extracted {county} {year}")
        except Exception as e:
            print(f"Failed {pdf_path}: {e}")

if __name__ == "__main__":
    extract_all()
