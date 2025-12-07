@echo off
echo Starting ClearSky Text-to-SQL Frontend...
echo.

cd /d %~dp0..\frontend

if not exist node_modules (
    echo Installing dependencies...
    npm install
)

npm run dev
