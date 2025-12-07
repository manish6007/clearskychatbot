@echo off
echo ============================================
echo ClearSky Text-to-SQL Local Setup
echo ============================================
echo.

echo Step 1: Installing local_setup dependencies...
cd /d %~dp0
pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo Step 2: Building FAISS vector store...
python build_vector_store.py
if errorlevel 1 goto :error

echo.
echo Step 3: Installing backend dependencies...
cd /d %~dp0..\backend
pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo ============================================
echo Setup complete!
echo ============================================
echo.
echo To start the application:
echo.
echo 1. Open a terminal and run:
echo    set USE_LOCAL_CONFIG=true
echo    cd backend
echo    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
echo.
echo 2. Open another terminal and run:
echo    cd frontend
echo    npm install
echo    npm run dev
echo.
echo 3. Open http://localhost:5173 in your browser
echo.
goto :end

:error
echo.
echo ERROR: Setup failed. Please check the error messages above.
exit /b 1

:end
