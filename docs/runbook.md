# Runbook

## Bootstrap

```powershell
cd "D:\personal projects\kenya-county-analytics"
python scripts/bootstrap_data.py
```

## Scrape KNBS PDFs

```powershell
python -m src.scraper.knbs_scraper
```

## Extract PDFs

```powershell
python -m src.extractor.pdf_parser --analyze-sample
python -m src.extractor.pdf_parser
```

## Native services

```powershell
uvicorn src.api.main:app --reload --port 8000
streamlit run src/dashboard/streamlit_app.py --server.port 8501
```

## Docker services

```powershell
docker-compose up --build -d
```
