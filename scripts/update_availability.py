from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.common import PROJECT_ROOT, read_json


def main() -> None:
    metrics_path = PROJECT_ROOT / "data" / "processed" / "county_metrics.csv"
    json_path = PROJECT_ROOT / "data" / "processed" / "county_metrics.json"
    log_path = PROJECT_ROOT / "data" / "raw" / "download_log.json"
    df = pd.read_csv(metrics_path, dtype={"county_code": str})
    df["county_code"] = df["county_code"].str.zfill(3)
    log = {row["county_name"]: row for row in read_json(log_path, [])}
    df["availability_status"] = df["county_name"].map(
        lambda name: log.get(name, {}).get("status", "BASELINE_PENDING_KNBS")
    )
    df["source_file"] = df["county_name"].map(lambda name: log.get(name, {}).get("file_path"))
    df["latest_year"] = df.apply(
        lambda row: int(log.get(row["county_name"], {}).get("year") or row["latest_year"]),
        axis=1,
    )
    df.to_csv(metrics_path, index=False)
    df.to_json(json_path, orient="records", indent=2)
    print(df["availability_status"].value_counts().to_string())


if __name__ == "__main__":
    main()
