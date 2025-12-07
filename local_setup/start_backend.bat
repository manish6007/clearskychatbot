@echo off
echo Starting ClearSky Text-to-SQL Backend...
echo.

set USE_LOCAL_CONFIG=true
cd /d %~dp0..\backend

echo Environment:
echo   USE_LOCAL_CONFIG=true
echo   AWS_REGION=%AWS_REGION%
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
