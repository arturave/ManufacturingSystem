# INSTRUKCJA NAPRAWY PROBLEMU Z EDYCJĄ PRODUKTÓW

## Problem
Nie można zapisać edytowanych produktów w katalogu. Błąd: `record "old" has no field "cad_2d_file"`

## Przyczyna
W bazie danych istnieje trigger, który odwołuje się do pola `cad_2d_file`, które nie istnieje w tabeli `products_catalog`.

## Rozwiązanie

### KROK 1: Wykonaj skrypt naprawczy w Supabase

1. Otwórz Supabase Dashboard
2. Przejdź do **SQL Editor**
3. Skopiuj i wklej zawartość pliku: **`FIND_AND_FIX_ALL_TRIGGERS.sql`**
4. Kliknij **Run** aby wykonać skrypt

Skrypt automatycznie:
- Znajdzie i usunie problematyczne triggery
- Doda brakujące kolumny do tabeli
- Utworzy tylko niezbędny trigger dla `updated_at`

### KROK 2: Weryfikacja

Po wykonaniu skryptu SQL, uruchom test:
```bash
cd ManufacturingSystem
python ../test_product_update_simple.py
```

Powinieneś zobaczyć:
```
[SUCCESS] UPDATE VERIFIED SUCCESSFULLY!
```

### KROK 3: Test w aplikacji

1. Uruchom aplikację główną
2. Przejdź do **Katalog produktów**
3. Wybierz dowolny produkt i kliknij **Edytuj**
4. Zmień jakąś wartość (np. opis)
5. Zapisz zmiany

Teraz edycja powinna działać poprawnie!

## Pliki pomocnicze

### Pliki SQL do naprawy:
- **`FIND_AND_FIX_ALL_TRIGGERS.sql`** - główny skrypt naprawczy (WYKONAJ TEN!)
- `FIX_TRIGGER_CAD_FIELDS.sql` - alternatywny skrypt naprawczy
- `CHECK_TABLE_STRUCTURE.sql` - skrypt diagnostyczny

### Pliki testowe:
- `test_product_update_simple.py` - prosty test weryfikujący działanie update
- `product_update_debug.log` - plik z debugiem (tworzony automatycznie)

### Zmodyfikowane pliki aplikacji:
- `products_module_enhanced.py` - dodany szczegółowy debug i alternatywne metody update

## Co zostało dodane w kodzie:

1. **Szczegółowy debug** - każdy krok update jest logowany do pliku `product_update_debug.log`
2. **Alternatywny update** - jeśli pełny update się nie uda, próbuje zapisać tylko podstawowe pola
3. **Obsługa błędów** - lepsza obsługa i raportowanie błędów

## Jeśli problem nadal występuje:

1. Sprawdź logi w pliku `product_update_debug.log`
2. Wykonaj skrypt `CHECK_TABLE_STRUCTURE.sql` aby zobaczyć strukturę tabeli
3. Upewnij się że wszystkie triggery zostały usunięte wykonując:
   ```sql
   SELECT * FROM pg_trigger WHERE tgrelid = 'products_catalog'::regclass;
   ```

## Kontakt w razie problemów:
Jeśli problem nadal występuje, sprawdź:
- Czy masz uprawnienia do modyfikacji triggerów w bazie
- Czy skrypt SQL wykonał się bez błędów
- Logi w pliku `product_update_debug.log`