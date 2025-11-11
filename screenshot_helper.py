#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Screenshot Helper - Ułatwia zapisywanie i organizację screenshots
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import subprocess
import time

# Ścieżka do folderu screenshots
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

def get_next_screenshot_path():
    """Generuje nazwę dla kolejnego screenshot'a"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"screen_{timestamp}"

    # Znajdź wolny numer jeśli plik już istnieje
    counter = 1
    while True:
        if counter == 1:
            filename = f"{base_name}.png"
        else:
            filename = f"{base_name}_{counter}.png"

        filepath = SCREENSHOTS_DIR / filename
        if not filepath.exists():
            return filepath
        counter += 1

def open_screenshots_folder():
    """Otwiera folder ze screenshots w eksploratorze"""
    os.startfile(str(SCREENSHOTS_DIR))

def clean_old_screenshots(days=7):
    """Usuwa screenshots starsze niż X dni"""
    import time
    current_time = time.time()

    for file_path in SCREENSHOTS_DIR.glob("*.png"):
        file_age = current_time - file_path.stat().st_mtime
        if file_age > (days * 24 * 60 * 60):
            file_path.unlink()
            print(f"Usunięto stary screenshot: {file_path.name}")

def list_screenshots():
    """Listuje ostatnie screenshots"""
    files = sorted(SCREENSHOTS_DIR.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)

    print("\n📸 Ostatnie screenshots:")
    print("-" * 60)

    for i, file_path in enumerate(files[:10], 1):
        size_kb = file_path.stat().st_size / 1024
        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"{i}. {file_path.name} ({size_kb:.1f} KB) - {mod_time}")

    if not files:
        print("Brak screenshots w folderze")

    print("-" * 60)
    print(f"📁 Folder: {SCREENSHOTS_DIR}")
    return files[:10] if files else []

def show_usage():
    """Pokazuje instrukcję użycia"""
    next_path = get_next_screenshot_path()

    print("""
================================================================
                   SCREENSHOT HELPER
================================================================

  JAK PRZESLAC SCREENSHOT DO CLAUDE:

  1. Zrob screenshot (Win + Shift + S)

  2. Zapisz jako:
     %s

  3. W terminalu napisz:
     "Zobacz screenshot: %s"

  Claude automatycznie go zobaczy i przeanalizuje!

================================================================
  KOMENDY:
  * python screenshot_helper.py          - ta instrukcja
  * python screenshot_helper.py list     - lista plikow
  * python screenshot_helper.py open     - otworz folder
  * python screenshot_helper.py clean    - usun stare
================================================================

Folder screenshots: %s
Nastepny screenshot zapisz jako: %s
    """ % (next_path, next_path.name, SCREENSHOTS_DIR, next_path.name))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "list":
            list_screenshots()
        elif command == "open":
            open_screenshots_folder()
            print(f"✅ Otwarto folder: {SCREENSHOTS_DIR}")
        elif command == "clean":
            clean_old_screenshots()
            print("✅ Wyczyszczono stare screenshots")
        else:
            show_usage()
    else:
        show_usage()