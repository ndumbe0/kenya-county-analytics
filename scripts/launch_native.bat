@echo off
REM Kenya County Analytics - Native Launch Script (Windows)
echo ==========================================
echo Kenya County Analytics Platform
echo ==========================================

cd /d "D:\personal projects\kenya-county-analytics"

REM Check for virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

REM Train ML models
echo Training ML models...
python -c "from src.ml.population_forecaster import run_all_models; run_all_models()"

REM Launch API
echo ==========================================
echo Starting API server on port 8000...
echo Dashboard: http://localhost:8000/dashboard
echo API Docs:  http://localhost:8000/docs
echo ==========================================
python src/api/main.py