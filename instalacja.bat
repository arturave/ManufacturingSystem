@echo off
REM =====================================================
REM System Zarządzania Produkcją - Instalator
REM =====================================================

echo ==========================================
echo   INSTALATOR SYSTEMU PRODUKCYJNEGO
echo   Laser / Prasa Krawedzowa v1.1
echo ==========================================
echo.

REM Check Python installation
echo [*] Sprawdzanie instalacji Python...
python --version >NUL 2>&1
if errorlevel 1 (
    echo [!] Python nie jest zainstalowany lub nie jest w PATH
    echo.
    echo Pobierz Python 3.11+ z: https://www.python.org/downloads/
    echo Podczas instalacji zaznacz "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

python --version
echo.

REM Create virtual environment
echo [*] Tworzenie srodowiska wirtualnego...
if exist ".venv" (
    echo [!] Srodowisko juz istnieje. Usuwanie...
    rmdir /s /q .venv
)
python -m venv .venv
echo [OK] Srodowisko utworzone
echo.

REM Activate virtual environment
echo [*] Aktywacja srodowiska...
call .venv\Scripts\activate.bat
echo [OK] Srodowisko aktywne
echo.

REM Upgrade pip
echo [*] Aktualizacja pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo [*] Instalowanie zaleznosci (to moze potrwac kilka minut)...
echo.

pip install customtkinter
if errorlevel 1 goto :error

pip install Pillow
if errorlevel 1 goto :error

pip install supabase
if errorlevel 1 goto :error

pip install tkcalendar
if errorlevel 1 goto :error

pip install pandas
if errorlevel 1 goto :error

pip install openpyxl
if errorlevel 1 goto :error

pip install python-docx
if errorlevel 1 goto :error

pip install reportlab
if errorlevel 1 goto :error

pip install matplotlib
if errorlevel 1 goto :error

pip install python-dotenv
if errorlevel 1 goto :error

echo.
echo [OK] Wszystkie zaleznosci zainstalowane
echo.

REM Optional: Install pywin32 for Outlook Agent
echo ==========================================
echo   OPCJONALNE: Agent Outlook
echo ==========================================
echo.
echo Czy chcesz zainstalowac modul integracji z Outlook?
echo (Wymaga Windows i zainstalowanego Microsoft Outlook)
echo.
set /p install_outlook="Instalowac pywin32? (T/N): "

if /i "%install_outlook%"=="T" (
    echo.
    echo [*] Instalowanie pywin32...
    pip install pywin32
    
    REM Run post-install script
    echo [*] Konfigurowanie pywin32...
    python .venv\Scripts\pywin32_postinstall.py -install
    echo [OK] Agent Outlook zainstalowany
) else (
    echo [INFO] Pominieto instalacje agenta Outlook
)

echo.

REM Create .env file if not exists
if not exist ".env" (
    if exist ".env.example" (
        echo [*] Tworzenie pliku konfiguracyjnego...
        copy .env.example .env
        echo [OK] Plik .env utworzony
    ) else (
        echo [!] Brak pliku .env.example
    )
)

echo.
echo ==========================================
echo   INSTALACJA ZAKONCZONA POMYSLNIE!
echo ==========================================
echo.
echo NASTEPNE KROKI:
echo.
echo 1. Zaloz konto w Supabase.com (darmowe)
echo.
echo 2. Utworz nowy projekt w Supabase
echo.
echo 3. Wykonaj skrypt SQL z pliku 'setup_database.sql'
echo    w Supabase SQL Editor
echo.
echo 4. Utworz bucket 'attachments' w Storage
echo.
echo 5. Skopiuj URL i klucz API z Supabase
echo    do pliku .env
echo.
echo 6. Uruchom system uzywajac 'uruchom_system.bat'
echo.
echo ==========================================
echo.
pause
deactivate
exit /b 0

:error
echo.
echo ==========================================
echo   [!] BLAD PODCZAS INSTALACJI
echo ==========================================
echo.
echo Sprawdz polaczenie internetowe i sprobuj ponownie.
echo Jesli problem sie powtarza, zainstaluj recznie:
echo   pip install -r requirements.txt
echo.
pause
deactivate
exit /b 1
