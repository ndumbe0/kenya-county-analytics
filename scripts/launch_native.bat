@echo off
REM Kenya County Analytics - Native Launch Script
REM Run this if Docker is not available or for development

setlocal
cd /d "%~dp0\.."

echo ======================================================
echo   KENYA COUNTY ANALYTICS PLATFORM - LAUNCHING
echo ======================================================
echo.

echo [1/3] Refreshing download log...
python scripts\refresh_download_log.py
if errorlevel 1 echo [WARN] Log refresh skipped

echo.
echo [2/3] Starting FastAPI on http://localhost:8000 ...
start "Kenya-API" cmd /k "set PYTHONPATH=%CD%&& python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000"

echo Waiting 5s for API warm-up...
timeout /t 5 /nobreak >nul

echo.
echo [3/3] Starting Streamlit on http://localhost:8501 ...
start "Kenya-Dashboard" cmd /k "set PYTHONPATH=%CD%&& set API_URL=http://localhost:8000&& python -m streamlit run src/dashboard/streamlit_app.py --server.port 8501 --server.headless false"

echo.
echo ======================================================
echo   LIVE!
echo   - Dashboard: http://localhost:8501
echo   - API docs:  http://localhost:8000/docs
echo   - API root:  http://localhost:8000
echo ======================================================
echo Press any key to exit launcher (services keep running)
pause >nul
