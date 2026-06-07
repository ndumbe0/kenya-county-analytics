# Kenya County Analytics - System Architecture

## Overview

The Kenya County Analytics Platform is a comprehensive, multi-layered system designed to aggregate, process, analyze, and visualize demographic and economic data for Kenya's 47 counties.

## Architecture Layers

### 1. **Data Ingestion Layer**
- KNBS Scraper (Playwright)
- Implements retry logic and rate limiting
- Maintains scraping logs

### 2. **Data Processing Layer**
- PDF Extractor (Camelot + pdfplumber)
- Table extraction and cleaning
- Converts to structured JSON/CSV

### 3. **Analytics Layer**
- Population Forecaster (Prophet)
- Economic Clusterer (K-Means)
- Health Anomaly Detector (Isolation Forest)
- Education-Employment Analyzer (Linear Regression)

### 4. **API Layer**
- FastAPI backend
- 20+ RESTful endpoints
- Rate limiting and CORS

### 5. **Frontend Layer**
- D3.js map visualization
- GSAP animations
- Plotly charts
- Interactive dashboard

### 6. **Automation Layer**
- n8n workflow orchestration
- GitHub Actions CI/CD

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|----------|
| Scraping | Playwright | Browser automation |
| Extraction | Camelot, pdfplumber | PDF processing |
| ML | Prophet, scikit-learn | Forecasting & clustering |
| Backend | FastAPI | REST API |
| Frontend | D3.js, GSAP, Plotly | Interactive UI |
| Automation | n8n, GitHub Actions | Orchestration |
| Containerization | Docker | Environment consistency |

## Deployment Options

### Local Development
```bash
bash setup.sh
python src/api/main.py
```

### Docker
```bash
docker-compose up -d
```

### Cloud Deployment
- Kubernetes for API scaling
- Managed database (RDS/PostgreSQL)
- Object storage (S3)
- CDN (CloudFront)
