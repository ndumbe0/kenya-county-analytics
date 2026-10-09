@echo off
REM Kenya County Analytics - Docker Launch Script
setlocal
cd /d "%~dp0\.."

echo ======================================================
echo   KENYA COUNTY ANALYTICS - DOCKER LAUNCH
echo ======================================================
echo.

echo [1/3] Refreshing download log...
python scripts\refresh_download_log.py

echo.
echo [2/3] Building containers (first run may take 5-10 min)...
docker-compose build

echo.
echo [3/3] Starting services...
docker-compose up -d

echo.
echo Waiting 15s for services to warm up...
timeout /t 15 /nobreak >nul

echo.
echo [Verification]
curl -fsS http://localhost:8000/health
echo.

echo ======================================================
echo   LIVE!
echo   - Dashboard: http://localhost:8501
echo   - API docs:  http://localhost:8000/docs
echo.
echo   To stop:   docker-compose down
echo   To logs:   docker-compose logs -f
echo ======================================================
pause
