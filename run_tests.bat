@echo off
REM =====================================================
REM Test Runner for Manufacturing System
REM =====================================================

echo ==========================================
echo   URUCHAMIANIE TESTOW JEDNOSTKOWYCH
echo ==========================================
echo.

REM Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "env\Scripts\activate.bat" (
    call env\Scripts\activate.bat
) else (
    echo [!] Srodowisko wirtualne nie istnieje
    echo [*] Utworz srodowisko uzywajac: python -m venv .venv
    pause
    exit /b 1
)

REM Check if pytest is installed
python -c "import pytest" 2>NUL
if errorlevel 1 (
    echo [!] pytest nie jest zainstalowany
    echo [*] Instalowanie pytest...
    pip install pytest pytest-cov
)

REM Run tests with coverage
echo [*] Uruchamianie testow z pokryciem kodu...
echo.
python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

REM Check if tests passed
if errorlevel 1 (
    echo.
    echo ==========================================
    echo   [!] TESTY NIE POWIODLY SIE
    echo ==========================================
    echo.
) else (
    echo.
    echo ==========================================
    echo   [OK] WSZYSTKIE TESTY PRZESZLY
    echo ==========================================
    echo.
    echo Raport pokrycia kodu: htmlcov\index.html
    echo.
    
    REM Ask if user wants to open coverage report
    set /p open_report="Otworzyc raport pokrycia w przegladarce? (T/N): "
    if /i "%open_report%"=="T" (
        start htmlcov\index.html
    )
)

deactivate
pause
