@echo off
setlocal

:: Resolve paths from this script, not the caller's working directory.
cd /d "%~dp0"
if errorlevel 1 goto startup_failed

:: Explorer's PATH may select Python 3.9. Use the verified local runtime.
:: An alternative Python 3.10+ environment can be supplied explicitly.
if not defined OCC_HEALTH_PYTHON (
    if exist "%~dp0backend\.venv-prediction\Scripts\python.exe" (
        set "OCC_HEALTH_PYTHON=%~dp0backend\.venv-prediction\Scripts\python.exe"
    ) else (
        set "OCC_HEALTH_PYTHON=D:\Anaconda3\python.exe"
    )
)
if not defined NHANES_MODEL_ROOT set "NHANES_MODEL_ROOT=%~dp0models\nhanes_v5"

:: Experience profile: reuse installed Ollama; do not start/pull a model here.
:: Keep explicitly supplied provider/model settings for other deployments.
if not defined RAG_LLM_PROVIDER set "RAG_LLM_PROVIDER=ollama"
if /i "%RAG_LLM_PROVIDER%"=="ollama" (
    if not defined RAG_LLM_BASE_URL set "RAG_LLM_BASE_URL=http://127.0.0.1:11434"
    if not defined RAG_LLM_MODEL set "RAG_LLM_MODEL=llama3.1:8b"
    if not defined RAG_LLM_MAX_TOKENS set "RAG_LLM_MAX_TOKENS=512"
    if not defined RAG_LLM_CONTEXT_CHARS set "RAG_LLM_CONTEXT_CHARS=3500"
    if not defined RAG_TOP_K set "RAG_TOP_K=2"
    if not defined RAG_CANDIDATE_K set "RAG_CANDIDATE_K=8"
)
if not defined RAG_RETRIEVAL_MODE set "RAG_RETRIEVAL_MODE=hybrid"
:: Missing dense runtime is visibly reported as BM25 degradation, not dual-route success.
if not defined RAG_ALLOW_DEGRADED_RETRIEVAL set "RAG_ALLOW_DEGRADED_RETRIEVAL=true"
if not defined RAG_ALLOW_GENERAL_KNOWLEDGE_FALLBACK set "RAG_ALLOW_GENERAL_KNOWLEDGE_FALLBACK=true"
if not defined RAG_MAX_CONCURRENT_GENERATIONS set "RAG_MAX_CONCURRENT_GENERATIONS=1"
if /i "%~1"=="--backend" goto run_backend

if not exist "%OCC_HEALTH_PYTHON%" (
    echo ERROR: Python not found at "%OCC_HEALTH_PYTHON%".
    echo Set OCC_HEALTH_PYTHON to a Python 3.10+ environment with backend dependencies.
    goto startup_failed
)

echo Checking backend Python...
"%OCC_HEALTH_PYTHON%" -c "import sys; print(sys.executable); print(sys.version.split()[0]); sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
    echo ERROR: The backend requires Python 3.10 or newer.
    goto startup_failed
)

pushd "%~dp0backend"
if errorlevel 1 goto startup_failed
"%OCC_HEALTH_PYTHON%" -c "from app.main import app; print('Backend imports OK')"
set "OCC_HEALTH_IMPORT_STATUS=%errorlevel%"
popd
if not "%OCC_HEALTH_IMPORT_STATUS%"=="0" (
    echo ERROR: Backend dependency or configuration check failed. See the traceback above.
    goto startup_failed
)

where pnpm.cmd >nul 2>nul
if errorlevel 1 (
    echo ERROR: pnpm.cmd was not found. The frontend was not started.
    goto startup_failed
)

:: Local development uses separate frontend and backend ports.
set "NUXT_PUBLIC_API_BASE=http://127.0.0.1:8000"
if /i "%~1"=="--check" (
    echo Startup checks passed. No servers were started.
    echo Frontend API: %NUXT_PUBLIC_API_BASE%
    echo RAG provider: %RAG_LLM_PROVIDER%
    echo RAG model: %RAG_LLM_MODEL%
    echo RAG retrieval: %RAG_RETRIEVAL_MODE% ^(explicit degraded retrieval: %RAG_ALLOW_DEGRADED_RETRIEVAL% ^)
    echo General-knowledge fallback: %RAG_ALLOW_GENERAL_KNOWLEDGE_FALLBACK%
    echo NHANES model assets: %NHANES_MODEL_ROOT%
    exit /b 0
)

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
start "Backend API" "%ComSpec%" /d /k call "%~f0" --backend

:: Wait for backend
timeout /t 3 /nobreak >nul

:: Start frontend
echo Starting frontend...
cd /d "%~dp0my-nuxt-app"
call pnpm.cmd dev
set "OCC_HEALTH_FRONTEND_STATUS=%errorlevel%"

pause
exit /b %OCC_HEALTH_FRONTEND_STATUS%

:run_backend
cd /d "%~dp0backend"
if errorlevel 1 exit /b 1
echo Backend Python: "%OCC_HEALTH_PYTHON%"
"%OCC_HEALTH_PYTHON%" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
exit /b %errorlevel%

:startup_failed
if /i not "%~1"=="--check" pause
exit /b 1
