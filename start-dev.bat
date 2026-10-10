@echo off

echo ============================================================
echo   Occupational Health System - Dev Server
echo ============================================================
echo.
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.
echo   Press Ctrl+C to stop
echo ============================================================
echo.

:: Start backend in new window
echo Starting backend...
start "Backend API" cmd /k "cd backend && python -m uvicorn app.main:app --reload --port 8000"

:: Wait for backend
timeout /t 3 /nobreak >nul

:: Start frontend
echo Starting frontend...
cd my-nuxt-app
pnpm dev

pause
