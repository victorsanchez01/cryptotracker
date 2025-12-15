@echo off
REM
REM  run_tests.bat
REM  CryptoTracker
REM
REM  Created by Cascade on Dec 14, 2025.
REM  Copyright © 2025 CryptoTracker. All rights reserved.
REM

setlocal enabledelayedexpansion
set "ROOT_DIR=%~dp0"
set "VENV_PATH=%ROOT_DIR%\.venv"
set "REQUIREMENTS_FILE=%ROOT_DIR%\requirements.txt"
set "COVERAGE_HTML_DIR=%ROOT_DIR%\htmlcov"

if not exist "%VENV_PATH%\Scripts\activate.bat" (
    echo Creando entorno virtual...
    py -3 -m venv "%VENV_PATH%"
)

call "%VENV_PATH%\Scripts\activate.bat"

python -m pip install --upgrade pip >nul
python -m pip install -r "%REQUIREMENTS_FILE%"

where playwright >nul 2>&1
if %errorlevel%==0 (
    playwright install >nul
)

pytest --maxfail=1 --disable-warnings --cov=app --cov=tests --cov-report=term-missing --cov-report=html %*
if errorlevel 1 (
    exit /b %errorlevel%
)

echo.
echo Cobertura HTML disponible en: %COVERAGE_HTML_DIR%\index.html
