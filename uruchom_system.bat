@echo off
REM =====================================================
REM System Zarządzania Produkcją - Launcher
REM =====================================================

echo ========================================
echo   System Zarzadzania Produkcja
echo   Laser / Prasa Krawedzowa
echo   Wersja 1.1 Zintegrowana
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo [!] Srodowisko wirtualne nie istnieje
    echo [*] Tworzenie srodowiska wirtualnego...
    python -m venv .venv
    echo [OK] Srodowisko utworzone
    echo.
)

REM Activate virtual environment
echo [*] Aktywacja srodowiska wirtualnego...
call .venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import customtkinter" 2>NUL
if errorlevel 1 (
    echo [!] Brak zainstalowanych zaleznosci
    echo [*] Instalowanie pakietow...
    pip install --upgrade pip
    pip install -r requirements.txt
    echo [OK] Pakiety zainstalowane
    echo.
)

REM Check for .env file
if not exist ".env" (
    if exist ".env.example" (
        echo [!] Plik .env nie istnieje
        echo [*] Kopiowanie .env.example...
        copy .env.example .env
        echo.
        echo ==========================================
        echo  UWAGA: Uzupelnij plik .env danymi z Supabase
        echo  przed pierwszym uruchomieniem!
        echo ==========================================
        echo.
        pause
    )
)

REM Launch application
echo [*] Uruchamianie systemu...
echo.
python mfg_integrated.py

REM If application crashes, show error
if errorlevel 1 (
    echo.
    echo ==========================================
    echo  [!] Aplikacja zostala zamknieta z bledem
    echo ==========================================
    echo.
    echo Sprawdz:
    echo 1. Czy plik .env zawiera poprawne dane Supabase
    echo 2. Czy masz polaczenie z internetem
    echo 3. Logi w pliku outlook_agent.log
    echo.
    pause
)

deactivate
