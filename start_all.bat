@echo off
echo ===================================================
echo   SANJEEVANI — Smart Contracts for Smarter Care
echo   Starting Backend (8000), GIS (8001), Frontend (5173)
echo ===================================================

echo [1/3] Starting FastAPI Backend on port 8000...
start "SANJEEVANI Backend (8000)" cmd /k ".\.venv\Scripts\activate && python -m uvicorn app.main:app --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo [2/3] Starting GIS Engine on port 8001...
start "SANJEEVANI GIS (8001)" cmd /k ".\.venv\Scripts\activate && python -m uvicorn GIS_engine.main:app --port 8001"

timeout /t 2 /nobreak >nul

echo [3/3] Starting Vite Frontend on port 5173...
start "SANJEEVANI Frontend (5173)" cmd /k "cd frontend\artifacts\sanjeevani && pnpm dev"

timeout /t 3 /nobreak >nul

echo Opening browser at http://localhost:5173...
start http://localhost:5173/

echo ===================================================
echo   All services launched!
echo   Frontend: http://localhost:5173
echo   Backend:  http://127.0.0.1:8000/docs
echo   GIS:      http://127.0.0.1:8001/docs
echo ===================================================
