#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test skrypt do weryfikacji zmian w oknie edycji detalu
- Automatyczne generowanie miniatur po wczytaniu pliku
- Osadzony podgląd 3D
"""

import os
import sys
import customtkinter as ctk
from pathlib import Path

# Dodaj ścieżkę do modułów
sys.path.insert(0, os.path.dirname(__file__))

# Import modułów
from part_edit_enhanced import EnhancedPartEditDialog

# Mock Database class for testing
class Database:
    def __init__(self):
        self.client = MockSupabaseClient()

    def update_part(self, part_id, updates):
        pass

class MockSupabaseClient:
    def table(self, name):
        return self

    def select(self, columns):
        return self

    def order(self, column):
        return self

    def execute(self):
        return MockResponse()

    def insert(self, data):
        return self

    def update(self, data):
        return self

class MockResponse:
    def __init__(self):
        self.data = []

def test_part_edit_dialog():
    """Test okna edycji detalu z nowymi funkcjami"""

    print("=" * 60)
    print("TEST ZMIAN W OKNIE EDYCJI DETALU")
    print("=" * 60)
    print()
    print("Wprowadzone zmiany:")
    print("1. Automatyczne generowanie miniatury po wczytaniu pliku")
    print("   - Przycisk 'Generuj miniatury' został usunięty")
    print("   - Miniatury generują się automatycznie po wczytaniu pliku")
    print()
    print("2. Osadzony podgląd 3D w oknie dialogowym")
    print("   - Podgląd 3D nie otwiera się w osobnym oknie Qt")
    print("   - Jest osadzony bezpośrednio w oknie Tkinter")
    print()
    print("-" * 60)
    print()

    # Utwórz główne okno
    root = ctk.CTk()
    root.title("Test - Okno główne")
    root.geometry("400x300")

    # Ukryj główne okno
    root.withdraw()

    try:
        # Utwórz połączenie z bazą danych
        db = Database()
        print("[OK] Połączono z bazą danych")

        # Otwórz dialog edycji detalu
        print("[OK] Otwieranie okna 'Nowy detal'...")
        dialog = EnhancedPartEditDialog(
            parent=root,
            db=db,
            parts_list=[],
            part_data=None,
            order_id=None
        )

        print()
        print("INSTRUKCJA TESTOWANIA:")
        print("-" * 40)
        print("1. W oknie 'Nowy detal V2' kliknij przycisk 'Wczytaj'")
        print("   w sekcji 'Plik 2D', 'Plik 3D' lub 'Grafika użytkownika'")
        print()
        print("2. Po wybraniu pliku:")
        print("   - Miniatura powinna wygenerować się AUTOMATYCZNIE")
        print("   - NIE MA już przycisku 'Generuj miniatury'")
        print()
        print("3. Kliknij 'Podgląd' dla pliku 3D:")
        print("   - Podgląd powinien otworzyć się w oknie Tkinter")
        print("   - NIE powinno otwierać się osobne okno Qt")
        print()
        print("4. Wypełnij pozostałe pola i kliknij 'Zapisz' lub 'Anuluj'")
        print()
        print("-" * 40)

        # Uruchom pętlę główną
        root.mainloop()

        print()
        print("[OK] Test zakończony")

    except Exception as e:
        print(f"[ERROR] Błąd podczas testu: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_part_edit_dialog()