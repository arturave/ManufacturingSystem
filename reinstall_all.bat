@echo off
REM ========================================
REM Reinstalacja wszystkich pakietów
REM ========================================
echo.
echo ========================================
echo REINSTALACJA WSZYSTKICH PAKIETÓW
echo ========================================
echo.

if not exist "env\Scripts\python.exe" (
    echo [ERROR] Nie znaleziono środowiska wirtualnego!
    pause
    exit /b 1
)

echo [1/4] Aktualizacja pip, setuptools, wheel...
env\Scripts\python.exe -m pip install --upgrade pip setuptools wheel

echo.
echo [2/4] Instalacja pakietów z requirements.txt...
env\Scripts\python.exe -m pip install -r requirements.txt --force-reinstall

echo.
echo [3/4] Instalacja dodatkowych pakietów dla viewera...
env\Scripts\python.exe -m pip install PySide6

echo.
echo [4/4] Instalacja pakietów do wizualizacji...
env\Scripts\python.exe -m pip install trimesh numpy-stl opencv-python

echo.
echo ========================================
echo WERYFIKACJA INSTALACJI
echo ========================================
echo.

env\Scripts\python.exe -c "import sys; print('Python:', sys.version)"
echo.

env\Scripts\python.exe -c "import customtkinter; print('[OK] customtkinter:', customtkinter.__version__)"
env\Scripts\python.exe -c "import supabase; print('[OK] supabase zainstalowane')"
env\Scripts\python.exe -c "import pandas; print('[OK] pandas:', pandas.__version__)"
env\Scripts\python.exe -c "import matplotlib; print('[OK] matplotlib:', matplotlib.__version__)"
env\Scripts\python.exe -c "import ezdxf; print('[OK] ezdxf:', ezdxf.__version__)"
env\Scripts\python.exe -c "import PySide6; print('[OK] PySide6:', PySide6.__version__)"
env\Scripts\python.exe -c "import cv2; print('[OK] OpenCV:', cv2.__version__)"
env\Scripts\python.exe -c "import trimesh; print('[OK] trimesh:', trimesh.__version__)"

echo.
echo ========================================
echo INSTALACJA ZAKOŃCZONA!
echo ========================================
echo.
echo Teraz wykonaj w Supabase SQL Editor:
echo   1. FIX_MISSING_VIEWS.sql
echo   2. FIX_VISUALIZATION_DATABASE_V2.sql
echo.
echo Następnie uruchom aplikację:
echo   env\Scripts\python.exe mfg_app.py
echo.
pause