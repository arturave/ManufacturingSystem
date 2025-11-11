# Moduł Produktów - Instrukcja Użytkowania
## Wersja: 2.0 (2025-11-11)

## 📋 Opis modułu

Moduł produktów służy do zarządzania katalogiem produktów w systemie Manufacturing. Umożliwia:
- Zarządzanie katalogiem produktów (szablonów)
- Edycję i podgląd produktów
- Przechowywanie plików CAD i dokumentacji
- Wyszukiwanie i filtrowanie produktów
- Kopiowanie produktów do zamówień

## 🔑 Kluczowe pliki

| Plik | Opis | Użycie |
|------|------|--------|
| `products_module_enhanced.py` | Główne okno zarządzania produktami | Wyświetlanie listy produktów |
| `part_edit_enhanced_v4.py` | Formularz edycji produktu | Dodawanie/edycja produktów |
| `products_selector_dialog.py` | Dialog wyboru produktów | Wybór produktów do zamówienia |

## 🗂️ Struktura bazy danych

### Tabela: `products_catalog`
Główna tabela katalogu produktów (szablony):
- **id** - Unikalny identyfikator
- **idx_code** - Kod indeksowy produktu
- **name** - Nazwa produktu
- **material_id** - ID materiału
- **customer_id** - ID klienta (opcjonalne)
- **cad_2d_binary** - Plik CAD 2D (binarne)
- **cad_3d_binary** - Plik CAD 3D (binarne)
- **user_image_binary** - Obraz użytkownika (binarne)
- **additional_documentation** - Dokumentacja ZIP/7Z (binarne)
- **thumbnail_100** - Miniatura 100x100
- **Koszty**: material_cost, laser_cost, bending_cost, additional_costs

### Tabela: `parts`
Części w zamówieniach (instancje produktów):
- Struktura podobna do products_catalog
- **order_id** - Powiązanie z zamówieniem
- **qty** - Ilość

## 🚀 Jak używać

### 1. Otwieranie modułu produktów
```python
from products_module_enhanced import EnhancedProductsWindow

# W głównej aplikacji
window = EnhancedProductsWindow(parent, db)
```

### 2. Dodawanie nowego produktu
1. Kliknij przycisk **"➕ Dodaj produkt"**
2. Wypełnij formularz:
   - Nazwa (wymagane)
   - Materiał (wymagane)
   - Grubość (wymagane)
   - Koszty
   - Pliki CAD (opcjonalne)
3. Wybierz główne źródło grafiki
4. Kliknij **"✓ Zapisz"**

### 3. Edycja produktu
1. Wybierz produkt z listy (kliknięcie)
2. Kliknij **"✏️ Edytuj"** lub użyj menu kontekstowego (prawy przycisk)
3. Zmodyfikuj dane
4. Zapisz zmiany

### 4. Podgląd produktu
- **Dwuklik** na produkt - otworzy szczegóły w trybie podglądu
- **Menu kontekstowe** → "🔍 Szczegóły"

### 5. Filtrowanie i wyszukiwanie
- **Pole wyszukiwania** - szuka w nazwie, indeksie, kliencie
- **Filtr materiału** - wybierz konkretny materiał
- **Filtr klienta** - wybierz konkretnego klienta

## 🎯 Funkcje specjalne

### Przechowywanie plików binarnych
Wszystkie pliki są przechowywane w bazie jako dane binarne:
```python
# Automatyczna konwersja przy zapisie
with open(file_path, 'rb') as f:
    binary_data = f.read()
```

### Tryby pracy edytora

#### Tryb katalogu
```python
dialog = EnhancedPartEditDialogV4(
    parent, db, [],
    catalog_mode=True  # Tryb katalogu
)
```

#### Tryb podglądu
```python
dialog = EnhancedPartEditDialogV4(
    parent, db, [],
    part_data=product,
    view_only=True  # Tylko podgląd
)
```

### Generowanie miniatur
Miniatury są generowane automatycznie z wybranego źródła grafiki:
- 100x100 - miniatura w liście
- 800x800 - podgląd średni
- 4K - podgląd wysokiej jakości

## 🔧 Konfiguracja

### Obsługiwane formaty plików

| Typ | Formaty |
|-----|---------|
| CAD 2D | .dxf, .dwg |
| CAD 3D | .step, .stp, .iges, .igs, .stl |
| Grafika | .jpg, .jpeg, .png, .bmp, .gif |
| Dokumentacja | .zip, .7z |

## ⚠️ Ważne uwagi

1. **Nie modyfikuj** plików wrapper: `products_module.py`, `part_edit_enhanced.py`
2. **Używaj** najnowszych wersji: `*_enhanced.py`, `*_v4.py`
3. **Pliki binarne** - wszystkie pliki są przechowywane w bazie, nie na dysku
4. **Backup** - regularnie wykonuj kopie zapasowe bazy danych

## 🐛 Rozwiązywanie problemów

### Problem: Brak miniatur
**Rozwiązanie**: Sprawdź czy wybrane jest źródło grafiki (2D/3D/USER)

### Problem: Nie można załadować pliku CAD
**Rozwiązanie**: Upewnij się, że plik ma prawidłowy format i nie jest uszkodzony

### Problem: Błąd zapisu do bazy
**Rozwiązanie**: Sprawdź połączenie z bazą danych i uprawnienia

## 📊 Migracja danych

Jeśli masz dane ze starszej wersji ze ścieżkami do plików:
1. Wykonaj skrypt `06_FIX_PRODUCTS_CATALOG.sql`
2. Użyj skryptu migracji (do napisania) lub ręcznie przenieś pliki

## 🔄 Aktualizacje (2025-11-11)

### Co nowego:
- ✅ Wyróżnienie wybranego wiersza
- ✅ Menu kontekstowe
- ✅ Przycisk "Edytuj"
- ✅ Usunięte zbędne kolumny
- ✅ Kolumna "Cena" z sumą kosztów
- ✅ Miniatury w liście
- ✅ Binarne przechowywanie plików
- ✅ Obsługa dokumentacji ZIP/7Z
- ✅ Tryb podglądu

### Planowane:
- [ ] Eksport do Excel/PDF
- [ ] Import masowy produktów
- [ ] Historia zmian produktu
- [ ] Wersjonowanie produktów