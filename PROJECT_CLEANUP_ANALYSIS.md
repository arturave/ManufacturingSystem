# PROJECT CLEANUP ANALYSIS
## Manufacturing System - Stan na 2025-11-15

## 1. ANALIZA PLIKÓW

### A. PLIKI GŁÓWNE (DO ZACHOWANIA)
```
APLIKACJA:
- mfg_integrated.py         # Główna aplikacja
- products_module_enhanced.py  # Moduł produktów (aktualny)
- part_edit_enhanced_v4.py    # Edytor części (aktualny)
- customer_module_enhanced.py  # Moduł klientów
- materials_dict_module.py    # Słownik materiałów
- quotations_module.py        # Moduł wycen
- wz_dialog.py               # Dialog WZ
- wz_generator.py            # Generator WZ
- image_processing.py        # Przetwarzanie obrazów
- cad_to_image_converter.py  # Konwersja CAD->obraz

NARZĘDZIA:
- integrated_viewer_v2.py    # Podgląd plików
- setup.py                   # Konfiguracja
```

### B. PLIKI DO USUNIĘCIA
```
STARE WERSJE:
- products_module.py         # Stara wersja
- part_edit_enhanced.py     # Stara wersja
- integrated_viewer.py      # Stara wersja
- mfg_app.py                # Stara aplikacja

PLIKI TESTOWE (30+ plików):
- test_*.py                 # Wszystkie pliki testowe
- save_thumbnail_test.py
- verify_thumbnail_display.py

PLIKI NAPRAWCZE SQL (15+ plików):
- FIX_*.sql
- FORCE_FIX_*.sql
- DEBUG_*.sql
- SIMPLE_FIX.sql
- CHECK_TABLE_STRUCTURE.sql
- FIND_AND_FIX_ALL_TRIGGERS.sql
- MIGRATE_TO_BLOB_STORAGE*.sql
- OPTYMALIZACJA_*.sql

DOKUMENTACJA TYMCZASOWA:
- ANALIZA_POL_TABELI.md
- BINARY_DATA_*.md
- DEBUG_*.md
- DOUBLE_ENCODING_FIX.md
- INSTRUKCJA_NAPRAWY.md
- JAK_DZIALA_GENEROWANIE_MINIATUR.md
```

### C. NIEUŻYWANE MODUŁY
```
- attachments_gui_widgets.py  # Niewykorzystany
- attachments_manager.py      # Niewykorzystany
- outlook_agent.py           # Niewykorzystany
- products_selector_dialog.py # Niewykorzystany?
- cad_processing.py          # Zduplikowany z cad_to_image_converter
```

## 2. STRUKTURA BAZY DANYCH

### A. TABELE AKTYWNE
```sql
GŁÓWNE:
- customers              # Klienci
- products_catalog       # Katalog produktów
- materials_dict        # Słownik materiałów
- orders               # Zamówienia
- order_parts          # Części zamówień
- quotes               # Wyceny
- quote_parts          # Części wycen

WIDOKI:
- v_orders_full        # Pełne dane zamówień
- v_orders_status_counts # Liczniki statusów
```

### B. POLA DO USUNIĘCIA Z products_catalog
```sql
ZDUPLIKOWANE/NIEUŻYWANE:
- graphic_high_res      # Nieużywane (mamy preview_4k)
- graphic_low_res       # Nieużywane (mamy thumbnail_100)
- documentation_path    # Nieużywane (mamy binary)
- material_cost        # Zduplikowane z material_laser_cost
- laser_cost           # Zduplikowane z material_laser_cost
- tags                 # Nieużywane
- usage_count          # Nieużywane
- last_used_at         # Nieużywane
- created_by           # Nieużywane
- updated_by           # Nieużywane
- *_mimetype           # Wszystkie pola mimetype (nieużywane)
- subcategory          # Nieużywane
- width_mm, height_mm, length_mm  # Nieużywane
- weight_kg            # Nieużywane
- surface_area_m2      # Nieużywane
- production_time_minutes # Nieużywane
- machine_type         # Nieużywane
```

### C. TABELE DO USUNIĘCIA
```sql
- order_attachments    # Nieużywana
- v_orders_sla        # Nieistniejąca (błędy w logach)
```

## 3. KOD DO OPTYMALIZACJI

### A. PROBLEMY W KODZIE
```python
1. Podwójne kodowanie thumbnail (HEX->BASE64->PNG)
   - Niepotrzebna złożoność
   - Zwiększone zużycie miejsca

2. Brak cache'owania danych
   - Wielokrotne zapytania do bazy

3. Nieoptymalne ładowanie list
   - Brak paginacji
   - Ładowanie wszystkich kolumn

4. Mieszane style kodowania
   - Różne konwencje nazewnictwa
   - Duplikacja kodu między modułami
```

## 4. MIGRACJA BAZY DANYCH

### A. OPCJE MIGRACJI NA MySQL (seohost.pl)

**ZALETY:**
- Pełna kontrola nad backupami
- Brak limitów Supabase (500MB)
- Tańsze w dłuższej perspektywie
- Możliwość optymalizacji

**WADY:**
- Konieczność przepisania połączeń
- Brak wbudowanego API REST
- Konieczność zarządzania serwerem

### B. STRATEGIA MIGRACJI
```python
1. Eksport danych z Supabase (JSON/CSV)
2. Stworzenie struktury MySQL
3. Import danych
4. Przepisanie warstwy dostępu do danych
5. Testy integracyjne
```

## 5. REKOMENDACJE

### FAZA 1: ARCHIWIZACJA (WYKONANE ✓)
- Backup całego rozwiązania

### FAZA 2: CZYSZCZENIE
```bash
# Usunięcie plików testowych
rm test_*.py

# Usunięcie plików SQL naprawczych
rm FIX_*.sql FORCE_FIX*.sql DEBUG_*.sql

# Usunięcie starej dokumentacji
rm BINARY_DATA_*.md DEBUG_*.md INSTRUKCJA_NAPRAWY.md

# Usunięcie starych wersji
rm products_module.py part_edit_enhanced.py integrated_viewer.py
```

### FAZA 3: REORGANIZACJA
```
ManufacturingSystem/
├── src/
│   ├── main.py (dawniej mfg_integrated.py)
│   ├── modules/
│   │   ├── products.py
│   │   ├── customers.py
│   │   ├── materials.py
│   │   ├── quotes.py
│   │   └── documents.py
│   ├── dialogs/
│   │   ├── part_edit.py
│   │   └── wz_dialog.py
│   └── utils/
│       ├── image_processing.py
│       └── cad_converter.py
├── database/
│   ├── schema.sql
│   └── migration/
├── docs/
│   └── TECHNICAL_DOC.md
└── requirements.txt
```

### FAZA 4: OPTYMALIZACJA BAZY
```sql
-- Usunięcie zbędnych pól
ALTER TABLE products_catalog
DROP COLUMN graphic_high_res,
DROP COLUMN graphic_low_res,
DROP COLUMN documentation_path,
DROP COLUMN material_cost,
DROP COLUMN laser_cost,
DROP COLUMN tags,
DROP COLUMN usage_count,
DROP COLUMN last_used_at,
DROP COLUMN created_by,
DROP COLUMN updated_by;

-- Dodanie indeksów
CREATE INDEX idx_products_active ON products_catalog(is_active);
CREATE INDEX idx_products_customer ON products_catalog(customer_id);
CREATE INDEX idx_products_material ON products_catalog(material_id);
```

### FAZA 5: MIGRACJA NA MySQL
1. Eksport danych z Supabase
2. Przygotowanie schematu MySQL
3. Stworzenie warstwy abstrakcji DB
4. Stopniowa migracja modułów
5. Testy i walidacja

## 6. DOKUMENTACJA TECHNICZNA (KOMPAKTOWA)

### UŻYWANE KOMPONENTY:
```yaml
BAZA DANYCH:
  Tabele: 7 aktywnych
  Widoki: 2 aktywne
  Relacje: customer->products, material->products, order->parts

MODUŁY PYTHON:
  Główne: 10 plików
  Zależności: customtkinter, supabase, PIL, ezdxf, reportlab

API:
  Supabase REST API
  Autentykacja: API Key

FUNKCJONALNOŚCI:
  - Zarządzanie produktami (CRUD)
  - Zarządzanie klientami
  - Słownik materiałów
  - Generowanie WZ
  - Podgląd CAD (DXF/DWG)
  - Generowanie miniatur
```

## 7. PRIORYTETY

1. **NATYCHMIAST**: Backup bazy danych
2. **TYDZIEŃ 1**: Czyszczenie plików
3. **TYDZIEŃ 2**: Optymalizacja bazy
4. **TYDZIEŃ 3**: Reorganizacja kodu
5. **MIESIĄC 2**: Rozważenie migracji na MySQL

## 8. ESTYMACJA OSZCZĘDNOŚCI

- **Miejsce na dysku**: ~40% redukcja (usunięcie testów i fixów)
- **Baza danych**: ~30% redukcja rozmiaru (usunięcie zbędnych pól)
- **Wydajność**: ~25% szybsze ładowanie list
- **Maintenance**: 50% mniej plików do zarządzania