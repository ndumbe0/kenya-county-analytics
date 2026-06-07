# Kenya County Statistical Abstracts - Analytics Platform

Full-stack analytics platform covering Kenya's 47 counties. Combines KNBS PDF ingestion, table extraction, county geospatial data, machine learning insights, a FastAPI backend, an interactive Streamlit dashboard with an animated county map, and three AI chatbot agents.

## Quick Start

### Native (recommended for dev)
```powershell
cd "D:\personal projects\kenya-county-analytics"
scripts\launch_native.bat
```

### Docker (recommended for production)
```powershell
cd "D:\personal projects\kenya-county-analytics"
scripts\launch_docker.bat
```

After launch open:
- Dashboard:    http://localhost:8501
- API docs:     http://localhost:8000/docs
- API root:     http://localhost:8000
- n8n (local):  http://localhost:5678

## Architecture

```
data/raw            - Downloaded PDFs from KNBS (mirrored from D:/personal projects/Project data)
data/processed      - Extracted tables (CSV/JSON) per county and domain
data/geospatial     - Kenya county boundary GeoJSON
src/scraper         - KNBS website scraper (knbs_scraper.py)
src/extractor       - PDF table parser (pdf_parser.py - camelot/pdfplumber/tabula)
src/ml              - Population forecast, K-Means clustering, health anomalies, employment
src/api             - FastAPI backend with chat router
src/chatbots        - 3 AI agents: DataExplorer, Prediction, Guide
src/dashboard       - Streamlit dashboard with animated choropleth map
n8n_workflows       - Exported n8n automation pipeline JSON
visualizations      - Power BI and Tableau data extracts + build guides
```

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Service banner |
| GET | `/health` | Liveness check |
| GET | `/api/v1/counties/` | All 47 counties + status |
| GET | `/api/v1/counties/{code}` | Single county details |
| GET | `/api/v1/counties/{code}/population/forecast` | 5-year population forecast |
| GET | `/api/v1/analytics/clustering` | Development tiers |
| GET | `/api/v1/health/anomalies` | Health anomaly detection |
| GET | `/api/v1/analytics/all` | Run all ML models |
| GET | `/api/v1/geospatial/counties` | County boundary GeoJSON |
| GET | `/api/v1/data/download/{csv,json,excel}` | Bulk export |
| GET | `/api/v1/chat/agents` | List AI agents |
| POST | `/api/v1/chat/query` | Ask any agent |

## Streamlit Dashboard Pages
- **Home** - Animated full-Kenya choropleth map (hover counties for stats)
- **County Detail** - Population, health, economy, education per county
- **Analytics** - ML forecasts, clusters, anomalies
- **Compare** - Side-by-side county comparison
- **AI Assistants** - Three chat agents in tabs
- **Data** - Download CSV / JSON / Excel
- **BI Dashboards** - Power BI + Tableau guides

## AI Chat Agents
1. **Data Explorer Bot** - Current/historical county statistics
2. **Prediction Bot** - ML forecasts (Prophet, K-Means, SHAP)
3. **Guide Bot** - Platform navigation help

## Manual Steps Required (GUI tools)
The platform pre-computes all data and provides CSV extracts. Final dashboard authoring still needs your input:

1. **Power BI** - Open Power BI Desktop, import `visualizations/powerbi/county_development_index_extract.csv` and follow `visualizations/powerbi/README.md` to build the .pbix file.
2. **Tableau** - Open Tableau Desktop, connect to `visualizations/tableau/kenya_county_overview_extract.csv` and follow `visualizations/tableau/README.md`.
3. **n8n** - Open http://localhost:5678, click "Add workflow > Import from File" and select `n8n_workflows/data_pipeline.json`.

## Verification
```powershell
python scripts/smoke_test.py
```
Runs 19 end-to-end checks against all API endpoints.

## Data Pipeline
```powershell
# 1. Refresh download log from existing files
python scripts/refresh_download_log.py
# 2. Scrape new KNBS PDFs
python -m src.scraper.knbs_scraper
# 3. Extract tables from PDFs
python -m src.extractor.pdf_parser
# 4. Retrain ML models
python -m src.ml.population_forecaster
```

## Security
- CORS restricted to localhost dashboards (configurable via `ALLOWED_ORIGINS`)
- Rate limit: 100 requests/min/IP
- Security headers (X-Frame-Options, X-XSS-Protection, X-Content-Type-Options)
- Input validation on all POST endpoints (empty + length limits)
- No hardcoded secrets

## Counties Coverage
Currently 16/47 counties have ingested PDFs in `data/raw/`. Other counties fall back to 2019 Census baselines and display "Data not yet uploaded" in the dashboard.
