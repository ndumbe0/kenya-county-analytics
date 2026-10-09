# Makueni County Statistical Abstract Analysis

Sample file: `C:\Users\ndumb\OneDrive\Desktop\2025-Statistical-Abstract-Makueni-County.pdf`

The extractor maps tables into four domains and stores CSV/JSON outputs under `data/processed/{county}/{domain}/`.

## Unified Schema

- `county_code`: official KNBS county code
- `county_name`: canonical county name
- `domain`: one of demographic_social, economic, environmental, governance
- `indicator`: normalized table row/metric name
- `sub_indicator`: optional table-specific category
- `unit`: count, percent, KES, index, ratio, etc.
- `period`: year or reporting period
- `value`: numeric value when parseable
- `value_raw`: original text value
- `source_page`: PDF page number
- `imputed`: true when missing value was filled downstream
- `source_file`: PDF path
