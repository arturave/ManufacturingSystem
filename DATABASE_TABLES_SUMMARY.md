# Podsumowanie Tabel Bazy Danych
## Manufacturing System - Stan na 2025-11-11

## ✅ TABELE DO ZACHOWANIA (12 tabel)

### 1. **customers**
- **Cel**: Dane klientów
- **Używana w**: Cała aplikacja
- **Ważne pola**: id, name, short_name, nip, email, customer_type

### 2. **materials_dict**
- **Cel**: Słownik dostępnych materiałów
- **Używana w**: Produkty, części
- **Ważne pola**: id, name, category, density

### 3. **products_catalog**
- **Cel**: Katalog produktów (szablony)
- **Używana w**: Moduł produktów
- **Ważne pola**: id, idx_code, name, material_id, pliki binarne (cad_2d_binary, etc.)

### 4. **parts**
- **Cel**: Części w zamówieniach (instancje produktów)
- **Używana w**: Zamówienia
- **Ważne pola**: id, order_id, name, qty, koszty

### 5. **orders**
- **Cel**: Zamówienia produkcyjne
- **Używana w**: Główny moduł aplikacji
- **Ważne pola**: id, process_no, customer_id, status, title

### 6. **order_items**
- **Cel**: Pozycje w zamówieniach
- **Używana w**: Szczegóły zamówień
- **Ważne pola**: id, order_id, product_id, qty, ceny

### 7. **quotations**
- **Cel**: Oferty handlowe
- **Używana w**: Moduł ofertowania
- **Ważne pola**: id, quote_no, customer_id, status, total_price

### 8. **quotation_items**
- **Cel**: Pozycje w ofertach
- **Używana w**: Szczegóły ofert
- **Ważne pola**: id, quotation_id, description, quantity, unit_price

### 9. **delivery_notes**
- **Cel**: Dokumenty WZ
- **Używana w**: Generowanie WZ
- **Ważne pola**: id, wz_number, order_id, issue_date, items (JSONB)

### 10. **order_status_history**
- **Cel**: Historia zmian statusów zamówień
- **Używana w**: Śledzenie procesu
- **Ważne pola**: id, order_id, old_status, new_status, changed_at

### 11. **process_counters**
- **Cel**: Liczniki dla numeracji zamówień
- **Używana w**: Automatyczna numeracja
- **Ważne pola**: year, last_no

### 12. **quote_counters**
- **Cel**: Liczniki dla numeracji ofert
- **Używana w**: Automatyczna numeracja ofert
- **Ważne pola**: year, last_no

## ❌ TABELE DO USUNIĘCIA

1. **parts_backup_2025_11_03** - Stary backup
2. Inne tabele backup (jeśli istnieją)

## 🔍 WIDOKI (VIEWS) - DO DECYZJI

1. **v_parts_full** - Widok części z joinami
   - Sprawdź czy używany w kodzie

2. **v_all_products** - Widok wszystkich produktów
   - Utworzony w skrypcie 06_FIX_PRODUCTS_CATALOG.sql
   - Może być przydatny do raportów

## 📝 WAŻNE UWAGI

### Przed czyszczeniem:
1. **WYKONAJ BACKUP** całej bazy danych!
2. Zapisz dane klientów i materiałów (jeśli chcesz je zachować)
3. Eksportuj ważne dane do Excel/CSV

### Kolejność czyszczenia (ważna!):
1. Najpierw tabele zależne (delivery_notes, order_items, etc.)
2. Potem tabele główne (orders, quotations)
3. Na końcu tabele słownikowe (opcjonalnie)

### Po wyczyszczeniu:
1. Zresetuj liczniki (process_counters, quote_counters)
2. Dodaj przykładowe materiały
3. Dodaj testowych klientów

## 🚀 JAK WYCZYŚCIĆ BAZĘ

### Opcja 1: Użyj przygotowanego skryptu
```sql
-- Wykonaj w Supabase SQL Editor:
-- CLEAN_DATABASE.sql
```

### Opcja 2: Ręczne czyszczenie
```sql
-- Najpierw wyłącz klucze obce
SET session_replication_role = 'replica';

-- Wyczyść tabele (w tej kolejności!)
TRUNCATE TABLE delivery_notes CASCADE;
TRUNCATE TABLE order_status_history CASCADE;
TRUNCATE TABLE order_items CASCADE;
TRUNCATE TABLE quotation_items CASCADE;
TRUNCATE TABLE parts CASCADE;
TRUNCATE TABLE orders CASCADE;
TRUNCATE TABLE quotations CASCADE;
TRUNCATE TABLE products_catalog CASCADE;

-- Opcjonalnie (zachowaj dane podstawowe)
-- TRUNCATE TABLE customers CASCADE;
-- TRUNCATE TABLE materials_dict CASCADE;

-- Zresetuj liczniki
TRUNCATE TABLE process_counters CASCADE;
TRUNCATE TABLE quote_counters CASCADE;
INSERT INTO process_counters (year, last_no) VALUES (2025, 0);
INSERT INTO quote_counters (year, last_no) VALUES (2025, 0);

-- Włącz klucze obce
SET session_replication_role = 'origin';
```

## 🔐 BEZPIECZEŃSTWO

- **NIE USUWAJ** struktury tabel, tylko dane
- **ZACHOWAJ** słowniki (materials_dict) - łatwiej je zostawić
- **ZAPISZ** dane klientów przed czyszczeniem (eksport)

## 📊 STATYSTYKI

Po wyczyszczeniu powinieneś mieć:
- 12 głównych tabel (puste lub z przykładowymi danymi)
- 2 liczniki zresetowane do 0
- 0 rekordów w tabelach transakcyjnych
- Opcjonalnie: przykładowe materiały i klienci