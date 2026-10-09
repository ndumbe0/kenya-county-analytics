# 🇰🇪 Kenya County Analytics - Quick Start Card

## ⚡ 60-Second Launch (Windows PowerShell)

```powershell
# 1. Navigate to project
cd "D:\personal projects\kenya-county-analytics"

# 2. Run setup script (RECOMMENDED)
.\setup.ps1

# OR Manual steps:
# 3. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install Playwright
playwright install chromium

# 6. Start API
python src\api\main.py

# 7. Open browser
start http://localhost:8000/dashboard
```

## 🐳 Docker Launch (2 commands)

```powershell
# Build and start
docker-compose up --build -d

# View logs
docker-compose logs -f api

# Open: http://localhost:8000/dashboard
```

## 📊 Key URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Dashboard | http://localhost:8000/dashboard | Interactive map & charts |
| API Docs | http://localhost:8000/docs | API documentation |
| API Health | http://localhost:8000/ | Server health check |
| n8n | http://localhost:5678 | Workflow automation |
| Data API | http://localhost:8000/api/v1/ | JSON data endpoints |

## 🚀 Project Features Activated

- ✅ FastAPI Backend (Port: 8000)
- ✅ Interactive Dashboard (D3.js + Plotly)
- ✅ REST API with 47 endpoints
- ✅ Population Forecasting (Prophet)
- ✅ Economic Clustering (K-Means)
- ✅ AI Data Agent (Natural language Q&A)
- ✅ n8n Workflow Engine (Port: 5678)
- ✅ Docker containerization
- ✅ Git version control

## 📝 File Manifest (17 Files Created)

### Core Application
- `src/api/main.py` (450+ lines) - FastAPI backend
- `src/templates/dashboard.html` (500+ lines) - Interactive UI
- `src/scraper/knbs_scraper.py` - Data scraper
- `src/extractor/pdf_parser.py` - PDF extraction
- `src/agents/data_agent.py` - AI assistant

### ML Models
- `src/ml/population_forecaster.py` - Population projections
- `src/ml/economic_clustering.py` - Economic tiers

### Configuration
- `requirements.txt` - 27 dependencies
- `.gitignore` - Version control rules
- `.env.example` - Environment variables
- `docker-compose.yml` - Container orchestration
- `docker/Dockerfile` - Image definition
- `n8n_workflows/data_pipeline.json` - Automation workflow

### Documentation
- `README.md` - Comprehensive guide
- `setup.ps1` - Windows setup script

### Git
- `.git/` - Version control (1st commit)

## 🎯 First Steps After Launch

1. **Open Dashboard**
   - Navigate to http://localhost:8000/dashboard
   - See all 47 Kenyan counties on map

2. **Test API**
   - Visit http://localhost:8000/docs
   - Try endpoints like `/api/v1/counties/`

3. **Chat with AI**
   - Use chatbot in bottom-right of dashboard
   - Ask: "What's Nairobi's population?"

4. **Configure Automation**
   - Go to http://localhost:5678
   - Import n8n workflow from `n8n_workflows/data_pipeline.json`

## ⚙️ Troubleshooting

### Port 8000 Already in Use
```powershell
# API auto-detects alternatives (8001, 8002, 8003...)
# Or kill the process:
Get-Process | Where-Object {$_.Port -eq 8000} | Stop-Process
```

### Missing Playwright
```powershell
pip install playwright
playwright install chromium
```

### Virtual Environment Not Activating
```powershell
# Try long form
python -m venv venv
python -m venv.activate
# Or check execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Docker Not Working
```powershell
# Check Docker is running
docker ps

# Rebuild without cache
docker-compose down -v
docker-compose up --build --no-cache -d
```

## 📈 Next: Advanced Configuration

1. **Add KNBS Scraper Integration**
   - Get actual KNBS PDFs
   - Run: `python src/scraper/knbs_scraper.py`

2. **Retrain ML Models**
   - Run: `python src/ml/population_forecaster.py`
   - Run: `python src/ml/economic_clustering.py`

3. **Configure n8n Workflows**
   - Set Discord webhook for notifications
   - Add schedule (default: Sunday 2 AM)

4. **Connect Power BI / Tableau**
   - Point to `data/processed/` CSV files
   - Build interactive reports

5. **Deploy to Cloud**
   - AWS: ECS + RDS
   - Azure: App Service + Cosmos DB
   - GCP: Cloud Run + Cloud SQL

## 📞 Support Resources

- **API Errors?** → Check `/logs/` directory
- **Data Issues?** → Review `/data/processed/master_dataset.json`
- **ML Problems?** → Check model output in `/data/processed/forecasts/`
- **Dashboard Not Loading?** → Open browser console (F12)
- **Docker Issues?** → Run `docker logs kenya-analytics-api`

## 🎉 Success Indicators

When setup is complete, you should see:

```
✅ Dashboard loads with interactive Kenya map
✅ All 47 counties visible
✅ API responding at http://localhost:8000/
✅ County tooltips showing real-time data
✅ Chatbot responding in bottom-right
✅ Docker containers running (if using Docker)
✅ n8n accessible at http://localhost:5678
```

## 🔗 Key Files to Remember

| File | Purpose |
|------|---------|
| `src/api/main.py` | Everything starts here |
| `src/templates/dashboard.html` | UI frontend |
| `setup.ps1` | One-click setup |
| `docker-compose.yml` | Container orchestration |
| `.env` | Configuration secrets |
| `requirements.txt` | Dependencies |

---

**Version**: 1.0.0  
**Status**: 🟢 Ready to Launch  
**Last Updated**: 2025-06-07  
**Maintained By**: Kenya Analytics Team
