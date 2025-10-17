@echo off
REM =====================================================
REM Instalacja bibliotek do renderowania 3D
REM ManufacturingSystem - 3D CAD Support
REM =====================================================

echo ========================================
echo   Instalacja bibliotek renderowania 3D
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python nie jest zainstalowany lub niedostepny
    echo     Zainstaluj Python 3.8+ i dodaj do PATH
    pause
    exit /b 1
)

echo [*] Sprawdzanie wersji Python...
python --version

REM Check if conda is available
conda --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [!] Anaconda/Miniconda nie jest zainstalowane
    echo.
    echo Aby zainstalowac pythonocc-core, potrzebujesz Anaconda lub Miniconda:
    echo 1. Pobierz z: https://www.anaconda.com/products/individual
    echo 2. Zainstaluj i dodaj do PATH
    echo 3. Uruchom ponownie ten skrypt
    echo.
    echo Alternatywnie mozesz zainstalowac tylko podstawowe biblioteki:
    echo.

    choice /C YN /M "Czy zainstalowac tylko podstawowe biblioteki (bez pythonocc-core)?"
    if errorlevel 2 goto :END
    if errorlevel 1 goto :INSTALL_BASIC
) else (
    echo [OK] Conda znalezione
    conda --version
    echo.
    goto :INSTALL_FULL
)

:INSTALL_FULL
echo ========================================
echo   PELNA INSTALACJA (z pythonocc-core)
echo ========================================
echo.

REM Install pythonocc-core via conda
echo [*] Instalowanie pythonocc-core...
conda install -c conda-forge pythonocc-core -y
if errorlevel 1 (
    echo [!] Blad instalacji pythonocc-core
    echo     Probuje alternatywna metode...
    conda install -c dlr-sc pythonocc-core -y
)

REM Install other requirements via pip
echo.
echo [*] Instalowanie pozostalych bibliotek...
pip install pillow supabase python-dotenv ezdxf pymupdf

REM Optional: PyQt5 for display backend
echo.
echo [*] Instalowanie PyQt5 (opcjonalne, dla backendu wyswietlania)...
pip install PyQt5

goto :SUCCESS

:INSTALL_BASIC
echo ========================================
echo   PODSTAWOWA INSTALACJA (bez 3D)
echo ========================================
echo.

echo [*] Instalowanie podstawowych bibliotek...
pip install pillow supabase python-dotenv ezdxf pymupdf

echo.
echo [!] UWAGA: Bez pythonocc-core renderowanie 3D nie bedzie dostepne
echo     Beda generowane tylko obrazy informacyjne z wymiarami

goto :SUCCESS

:SUCCESS
echo.
echo ========================================
echo   INSTALACJA ZAKONCZONA
echo ========================================
echo.
echo Zainstalowane biblioteki:
python -c "import PIL; print(f'  [OK] Pillow {PIL.__version__}')" 2>nul || echo   [!] Pillow - brak
python -c "import ezdxf; print(f'  [OK] ezdxf {ezdxf.__version__}')" 2>nul || echo   [!] ezdxf - brak
python -c "import pymupdf; print(f'  [OK] PyMuPDF {pymupdf.__version__}')" 2>nul || echo   [!] PyMuPDF - brak
python -c "import supabase; print('  [OK] supabase')" 2>nul || echo   [!] supabase - brak
python -c "from OCC.Core.STEPControl import STEPControl_Reader; print('  [OK] pythonocc-core')" 2>nul || echo   [!] pythonocc-core - brak

echo.
echo Aby przetestowac renderowanie 3D, uruchom:
echo   python test_3d_rendering.py
echo.

:END
pause