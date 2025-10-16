# Moduł Zarządzania Produktami (Detalami)
## Rozbudowa Systemu Zarządzania Produkcją

---

## 📋 Spis treści

1. [Wprowadzenie](#wprowadzenie)
2. [Nowe funkcjonalności](#nowe-funkcjonalności)
3. [Instalacja](#instalacja)
4. [Migracja bazy danych](#migracja-bazy-danych)
5. [Struktura modułów](#struktura-modułów)
6. [Instrukcja użytkowania](#instrukcja-użytkowania)
7. [Rozwiązywanie problemów](#rozwiązywanie-problemów)

---

## 📌 Wprowadzenie

Moduł zarządzania produktami (detalami) to znaczące rozszerzenie systemu, które dodaje zaawansowane funkcje zarządzania katalogiem produktów, grafikami, plikami CAD oraz automatyczną detekcję duplikatów.

### Główne cele modułu:
- **Centralne zarządzanie produktami** - niezależne od zamówień i ofert
- **Automatyczne przetwarzanie grafiki** - z plików CAD (DXF, DWG, STEP, IGES)
- **Słownik materiałów** - ustandaryzowane dane materiałowe
- **Detekcja duplikatów** - zapobieganie powielaniu produktów
- **Rozbudowane koszty** - koszt gięcia, koszty dodatkowe
- **Historia zmian** - śledzenie modyfikacji produktów

---

## 🎯 Nowe funkcjonalności

### 1. Panel Produktów
- **Lista wszystkich produktów** z grafikami miniaturowymi
- **Zaawansowane filtry:**
  - Nazwa produktu
  - Materiał
  - Grubość (zakres)
  - Klient
  - Data utworzenia
  - Duplikaty
- **Wyświetlanie grafik** w liście i szczegółach
- **Historia zmian** każdego produktu

### 2. Słownik Materiałów
- **Zarządzanie materiałami:**
  - Nazwa (unikalna)
  - Kategoria (STAL, ALUMINIUM, itd.)
  - Gęstość [g/cm³]
  - Opis
  - Status aktywny/nieaktywny
- **Predefiniowane materiały:**
  - DC01, DC04, S235JR, S355J2 (stale)
  - 1.4301, 1.4404 (stale nierdzewne)
  - AW-5754, AW-6082 (aluminium)
  - CuZn37, CW024A (mosiądz, miedź)
  - Hardox 400, 500 (stale specjalne)

### 3. Przetwarzanie Grafiki
- **Automatyczne generowanie miniatur:**
  - High-res: max HD (1920x1080)
  - Low-res: 200x200 pikseli
- **Obsługa formatów:**
  - Grafika: PNG, JPG, BMP, GIF, TIFF
  - CAD 2D: DXF, DWG
  - CAD 3D: STEP, STP, IGS, IGES

### 4. Obsługa Plików CAD
- **DXF/DWG:**
  - Automatyczne renderowanie do obrazu
  - Ekstrakcja metadanych (warstwy, elementy)
  - Obliczanie gabarytu
- **STEP/IGES:**
  - Odczyt geometrii 3D
  - Wyświetlanie wymiarów gabarytu
  - Generowanie podglądu (jeśli zainstalowano pythonocc-core)

### 5. Wygodne Dodawanie Grafiki
- **Przeciągnij i upuść (Drag & Drop):**
  - Pliki graficzne
  - Pliki CAD
- **Wklejanie ze schowka (Ctrl+V):**
  - Automatyczne przetwarzanie na high/low-res

### 6. Detekcja Duplikatów
- **Inteligentne sprawdzanie:**
  - Podobna nazwa
  - Ten sam materiał
  - Ta sama grubość
- **Sugestie użycia istniejącego produktu**
- **Automatyczne oznaczanie duplikatów:**
  - Numer powtórzenia nazwy
  - Pole `duplicate_number`

### 7. Rozszerzone Pola Produktu
Nowe pola w bazie danych:
- `bending_cost` - koszt gięcia [PLN]
- `additional_costs` - koszty dodatkowe [PLN]
- `graphic_high_res` - ścieżka do grafiki HD
- `graphic_low_res` - ścieżka do miniatury
- `documentation_path` - ścieżka do pliku CAD
- `duplicate_number` - numer duplikatu
- `material_id` - relacja do słownika materiałów
- `change_history` - historia zmian (JSONB)

### 8. Automatyzacja
- **Automatyczne indeksy:** IDX-00001, IDX-00002, ...
- **Automatyczne duplikaty:** Przy dodaniu podobnego produktu
- **Historia zmian:** Każda modyfikacja jest logowana

---

## 🔧 Instalacja

### Krok 1: Aktualizacja zależności

```bash
# Aktywuj środowisko wirtualne
.\env\Scripts\activate

# Zainstaluj nowe zależności
pip install -r requirements.txt

# Opcjonalnie (dla pełnej obsługi 3D - wymaga conda):
# conda install -c conda-forge pythonocc-core
```

### Nowe zależności:
- `ezdxf>=1.1.0` - przetwarzanie DXF/DWG
- `Pillow>=10.0.0` - przetwarzanie grafiki (już zainstalowane)
- `tkinterdnd2` (opcjonalnie) - drag & drop

### Krok 2: Migracja bazy danych

**WAŻNE:** Wykonaj skrypt SQL w Supabase SQL Editor:

```sql
-- Plik: enhance_products_module.sql
-- Skopiuj i wklej całą zawartość pliku do SQL Editor w Supabase
```

Skrypt tworzy:
1. Tabelę `materials_dict`
2. Nowe kolumny w tabeli `parts`
3. Funkcje i triggery
4. Widoki i polityki RLS
5. Dane testowe materiałów

**Sprawdź, czy migracja się powiodła:**
```sql
SELECT * FROM materials_dict;
SELECT * FROM parts LIMIT 5;
```

### Krok 3: Restart aplikacji

```bash
python mfg_integrated.py
```

Po uruchomieniu powinien pojawić się nowy przycisk **📦 Produkty** w górnym menu.

---

## 🗄️ Migracja bazy danych

### Wykonanie migracji:

1. **Zaloguj się do Supabase Dashboard**
2. **Przejdź do SQL Editor**
3. **Utwórz nowe query**
4. **Skopiuj zawartość pliku `enhance_products_module.sql`**
5. **Wykonaj query (Run)**

### Sprawdzenie poprawności:

```sql
-- Sprawdź tabelę materials_dict
SELECT COUNT(*) FROM materials_dict;
-- Powinno zwrócić ~13 materiałów (dane testowe)

-- Sprawdź nowe kolumny w parts
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'parts'
AND column_name IN ('bending_cost', 'material_id', 'graphic_high_res');
-- Powinno zwrócić 3 wiersze

-- Sprawdź funkcję detekcji duplikatów
SELECT routine_name
FROM information_schema.routines
WHERE routine_name = 'check_duplicate_parts_fn';
-- Powinno zwrócić 1 wiersz
```

### Rollback (w razie problemów):

```sql
-- Usuń nowe kolumny
ALTER TABLE parts
  DROP COLUMN IF EXISTS bending_cost,
  DROP COLUMN IF EXISTS additional_costs,
  DROP COLUMN IF EXISTS graphic_high_res,
  DROP COLUMN IF EXISTS graphic_low_res,
  DROP COLUMN IF EXISTS documentation_path,
  DROP COLUMN IF EXISTS duplicate_number,
  DROP COLUMN IF EXISTS material_id,
  DROP COLUMN IF EXISTS change_history;

-- Usuń tabelę materiałów
DROP TABLE IF EXISTS materials_dict CASCADE;

-- Usuń funkcje
DROP FUNCTION IF EXISTS check_duplicate_parts_fn;
DROP FUNCTION IF EXISTS generate_part_index_fn;
DROP FUNCTION IF EXISTS set_duplicate_number_fn;
DROP FUNCTION IF EXISTS log_part_changes_fn;
DROP FUNCTION IF EXISTS search_parts_fn;
```

---

## 📦 Struktura modułów

### Nowe pliki:

```
ManufacturingSystem/
├── enhance_products_module.sql    # Migracja bazy danych
├── image_processing.py            # Przetwarzanie grafiki
├── cad_processing.py              # Przetwarzanie plików CAD
├── materials_dict_module.py       # Słownik materiałów UI
├── part_edit_enhanced.py          # Rozszerzony dialog edycji detalu
├── products_module.py             # Główne okno produktów
└── PRODUCTS_MODULE_README.md      # Ten plik
```

### Zmodyfikowane pliki:

- `mfg_integrated.py` - dodano przycisk Produkty
- `requirements.txt` - dodano ezdxf

### Architektura modułów:

```
┌─────────────────────────────────────┐
│   mfg_integrated.py (Main App)      │
│                                     │
│  [Zamówienia] [Oferty] [📦Produkty] │
└──────────────┬──────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│     products_module.py               │
│  ┌────────────────────────────────┐  │
│  │ ProductsWindow                 │  │
│  │  - Lista produktów             │  │
│  │  - Filtry                      │  │
│  │  - Grafiki miniaturowe         │  │
│  └────────────┬───────────────────┘  │
│               │                      │
│               ▼                      │
│  ┌────────────────────────────────┐  │
│  │ ProductDetailDialog            │  │
│  │  - Szczegóły produktu          │  │
│  │  - Grafika HD                  │  │
│  │  - Historia zmian              │  │
│  └────────────────────────────────┘  │
└───────────────┬──────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│   part_edit_enhanced.py               │
│  ┌─────────────────────────────────┐  │
│  │ EnhancedPartEditDialog          │  │
│  │  - Formularz edycji             │  │
│  │  - Upload grafiki               │  │
│  │  - Upload CAD                   │  │
│  │  - Drag & Drop                  │  │
│  │  - Ctrl+V paste                 │  │
│  │  - Detekcja duplikatów          │  │
│  └─────────┬───────────────────────┘  │
└────────────┼──────────────────────────┘
             │
     ┌───────┴────────┬──────────────┐
     ▼                ▼              ▼
┌─────────┐  ┌──────────────┐  ┌────────────┐
│ image_  │  │ cad_         │  │ materials_ │
│ proces  │  │ processing   │  │ dict_      │
│ sing.py │  │ .py          │  │ module.py  │
└─────────┘  └──────────────┘  └────────────┘
```

---

## 📖 Instrukcja użytkowania

### 1. Otwieranie modułu produktów

1. Uruchom aplikację: `python mfg_integrated.py`
2. Kliknij przycisk **📦 Produkty** w górnym menu
3. Otworzy się okno zarządzania produktami

### 2. Przeglądanie produktów

**Okno produktów pokazuje:**
- Miniaturę grafiki (jeśli dostępna)
- Indeks (IDX-XXXXX)
- Nazwę produktu
- Materiał i grubość
- Ilość
- Klienta i numer zamówienia
- Datę utworzenia

**Operacje:**
- **Kliknięcie** - zaznacza produkt
- **Dwukrotne kliknięcie** - otwiera szczegóły

### 3. Filtrowanie produktów

**Dostępne filtry:**

- **Nazwa** - wyszukiwanie po nazwie
- **Materiał** - wybór z listy materiałów
- **Grubość** - zakres od-do
- **Klient** - wybór klienta
- **Data** - zakres dat
- **Tylko duplikaty** - pokaż tylko duplikaty

**Użycie:**
1. Wypełnij wybrane filtry
2. Kliknij **🔍 Filtruj**
3. Kliknij **❌ Wyczyść** aby zresetować

### 4. Słownik materiałów

**Otwieranie:**
- Kliknij **📋 Słownik materiałów** w oknie produktów

**Operacje:**
- **➕ Dodaj** - dodaj nowy materiał
- **✏️ Edytuj** - edytuj wybrany materiał
- **🗑️ Usuń** - usuń materiał (jeśli nie używany)

**Dodawanie materiału:**
1. Kliknij **➕ Dodaj**
2. Wypełnij:
   - Nazwa (wymagana, unikalna)
   - Kategoria
   - Gęstość [g/cm³]
   - Opis
3. Kliknij **Zapisz**

### 5. Dodawanie/edycja produktu

**W oknie zamówienia lub oferty:**
1. Kliknij **➕ Dodaj część**
2. Wypełnij formularz:
   - **Nazwa** (wymagana)
   - **Materiał** (wybierz z listy)
   - **Grubość** (wymagana)
   - **Ilość**
   - **Koszt gięcia**
   - **Koszty dodatkowe**

### 6. Dodawanie grafiki

**Metoda 1: Wybór pliku**
1. Kliknij **📁 Wybierz grafikę**
2. Wybierz plik (PNG, JPG, BMP, GIF)
3. Grafika zostanie automatycznie przetworzona

**Metoda 2: Wklejanie (Ctrl+V)**
1. Skopiuj obraz do schowka (np. screenshot)
2. Kliknij **📋 Wklej (Ctrl+V)** lub naciśnij Ctrl+V
3. Obraz zostanie automatycznie przetworzony

**Metoda 3: Przeciągnij i upuść**
1. Przeciągnij plik graficzny lub CAD do okna
2. Upuść plik
3. Zostanie automatycznie przetworzony

### 7. Dodawanie pliku CAD

**DXF/DWG:**
1. Kliknij **📄 DXF/DWG**
2. Wybierz plik
3. System automatycznie:
   - Zapisze plik jako dokumentację
   - Wygeneruje podgląd graficzny
   - Wyświetli podgląd

**3D (STEP/IGES):**
1. Kliknij **📦 3D (STEP/IGS)**
2. Wybierz plik
3. System automatycznie:
   - Zapisze plik jako dokumentację
   - Odczyta wymiary gabarytu
   - Wygeneruje podgląd z wymiarami

### 8. Detekcja duplikatów

**Automatyczna detekcja:**
- Gdy wprowadzasz nazwę, materiał i grubość
- System sprawdza czy istnieje podobny produkt
- Jeśli znajdzie - wyświetla ostrzeżenie:

```
⚠️ Znaleziono podobny detal: IDX-00123 - Obudowa stalowa
Materiał: DC01, Grubość: 2.0mm
Czy chcesz użyć istniejącego detalu?
```

**Opcje:**
- **Tak** - użyj istniejącego produktu
- **Nie** - utwórz nowy (zostanie oznaczony jako duplikat)

### 9. Wyświetlanie szczegółów produktu

**Otwieranie:**
- Dwukrotne kliknięcie na produkcie w liście

**Wyświetlane informacje:**
- Grafika HD
- Wszystkie pola produktu
- Koszty
- Numer duplikatu (jeśli dotyczy)
- Dokumentacja CAD
- Historia zmian

---

## 🔍 Funkcje bazy danych

### Funkcje SQL dostępne z poziomu aplikacji:

#### 1. `check_duplicate_parts_fn`
Sprawdza duplikaty produktów.

```python
response = db.client.rpc(
    'check_duplicate_parts_fn',
    {
        'p_name': 'Obudowa',
        'p_thickness': 2.0,
        'p_material_id': 'uuid-materiału'
    }
).execute()
```

#### 2. `search_parts_fn`
Wyszukuje produkty z filtrami.

```python
response = db.client.rpc(
    'search_parts_fn',
    {
        'p_name': 'Obudowa',
        'p_thickness_from': 1.0,
        'p_thickness_to': 3.0
    }
).execute()
```

#### 3. `next_process_no_fn`
Generuje kolejny numer procesowy (już istniejąca).

### Widoki:

#### `v_parts_full`
Części z nazwami materiałów.

```sql
SELECT * FROM v_parts_full WHERE material_category = 'STAL';
```

#### `v_materials_usage_stats`
Statystyki użycia materiałów.

```sql
SELECT * FROM v_materials_usage_stats ORDER BY usage_count DESC;
```

---

## ⚠️ Rozwiązywanie problemów

### Problem 1: Brak przycisku "Produkty"

**Przyczyna:** Moduł nie został zaimportowany

**Rozwiązanie:**
```bash
# Sprawdź czy plik istnieje
ls products_module.py

# Sprawdź import w mfg_integrated.py
grep "ProductsWindow" mfg_integrated.py
```

### Problem 2: Błąd przy otwieraniu okna produktów

**Przyczyna:** Brak migracji bazy danych

**Rozwiązanie:**
1. Wykonaj `enhance_products_module.sql` w Supabase
2. Sprawdź czy tabela `materials_dict` istnieje:
   ```sql
   SELECT * FROM materials_dict LIMIT 1;
   ```

### Problem 3: Nie można wczytać grafiki z DXF

**Przyczyna:** Brak biblioteki ezdxf

**Rozwiązanie:**
```bash
pip install ezdxf
```

### Problem 4: Placeholder zamiast podglądu 3D

**Przyczyna:** Brak pythonocc-core (opcjonalna biblioteka)

**Rozwiązanie:**
```bash
# Instalacja przez conda (zalecane)
conda install -c conda-forge pythonocc-core

# Lub kontynuuj bez 3D - system będzie działał z placeholderami
```

### Problem 5: Drag & Drop nie działa

**Przyczyna:** Brak biblioteki tkinterdnd2

**Rozwiązanie:**
```bash
pip install tkinterdnd2
```

**Alternatywa:** Użyj przycisków upload lub Ctrl+V

### Problem 6: Duplikaty nie są wykrywane

**Przyczyna:** Brak rozszerzenia pg_trgm w PostgreSQL

**Rozwiązanie:**
```sql
-- Wykonaj w Supabase SQL Editor
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### Problem 7: Błąd uprawnień przy tworzeniu materiału

**Przyczyna:** Brak polityk RLS

**Rozwiązanie:**
Sprawdź czy polityki zostały utworzone:
```sql
SELECT * FROM pg_policies WHERE tablename = 'materials_dict';
```

Jeśli brak, wykonaj ponownie sekcję RLS z migracji.

---

## 📊 Statystyki i raporty

### Najpopularniejsze materiały:

```sql
SELECT
    m.name,
    COUNT(p.id) as usage_count
FROM materials_dict m
LEFT JOIN parts p ON p.material_id = m.id
GROUP BY m.id, m.name
ORDER BY usage_count DESC
LIMIT 10;
```

### Produkty z największą liczbą duplikatów:

```sql
SELECT
    name,
    MAX(duplicate_number) as max_duplicates
FROM parts
GROUP BY name
HAVING MAX(duplicate_number) > 0
ORDER BY max_duplicates DESC;
```

### Produkty bez grafiki:

```sql
SELECT
    idx_code,
    name,
    material_id
FROM parts
WHERE graphic_low_res IS NULL
ORDER BY created_at DESC;
```

---

## 🚀 Kolejne kroki i rozwój

### Planowane rozszerzenia:

1. **Kalkulator masy** - automatyczne obliczanie masy detalu
2. **Generowanie ofert** - z grafik produktów
3. **Import CSV** - masowe dodawanie produktów
4. **Eksport katalogu** - PDF z grafikami
5. **Wersjonowanie** - śledzenie wersji produktów
6. **Tagi i kategorie** - lepsze organizowanie produktów
7. **Powiązania** - produkty używane razem

### Możliwe integracje:

- **ERP** - synchronizacja z systemami ERP
- **CAD Online** - podgląd 3D w przeglądarce
- **AI** - automatyczne wykrywanie podobnych detali
- **OCR** - odczyt danych z rysunków technicznych

---

## 📞 Wsparcie

W razie problemów lub pytań:

1. Sprawdź sekcję [Rozwiązywanie problemów](#rozwiązywanie-problemów)
2. Przejrzyj logi aplikacji
3. Sprawdź logi Supabase
4. Skontaktuj się z działem IT

---

## 📝 Changelog

### Wersja 1.2 (2025-10-15)

#### Dodano:
- Moduł zarządzania produktami
- Słownik materiałów
- Przetwarzanie grafiki (high-res/low-res)
- Obsługa plików CAD (DXF, DWG, STEP, IGES)
- Detekcja duplikatów
- Drag & drop
- Ctrl+V paste
- Historia zmian produktów
- Rozszerzone pola kosztów

#### Zmodyfikowano:
- Dialog edycji detalu (rozszerzony)
- Baza danych (nowe tabele i kolumny)
- Główne okno aplikacji (przycisk Produkty)

#### Zależności:
- Dodano: ezdxf>=1.1.0
- Opcjonalnie: pythonocc-core, tkinterdnd2

---

**Dokument utworzony:** 2025-10-15
**Wersja dokumentu:** 1.0
**Autor:** System Zarządzania Produkcją - Development Team
