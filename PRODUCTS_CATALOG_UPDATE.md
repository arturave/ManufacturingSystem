# Aktualizacja Katalogu Produktów - Dokumentacja

## Podsumowanie zmian

Zaimplementowano niezależny katalog produktów, który pozwala na:
1. Tworzenie produktów bez przypisania do zamówienia
2. Przypisywanie produktów do konkretnych klientów
3. Ponowne wykorzystanie produktów w różnych zamówieniach
4. Śledzenie statystyk użycia produktów

## Wykonane zmiany

### 1. Baza danych

#### Nowa tabela: `products_catalog`
Utworzono tabelę przechowującą produkty niezależnie od zamówień:
- **Plik SQL**: `add_products_catalog_table.sql`
- **Główne funkcje**:
  - Automatyczne generowanie kodów produktów (format P-XXXXX)
  - Opcjonalne przypisanie do klienta
  - Śledzenie statystyk użycia
  - Funkcja kopiowania produktu do części zamówienia

**Aby zastosować zmiany w bazie, wykonaj:**
```sql
-- W Supabase SQL Editor wykonaj zawartość pliku:
add_products_catalog_table.sql
```

### 2. Zmiany w kodzie Python

#### `part_edit_enhanced.py`
**Linie 92-108**: Dodano pole wyboru klienta
```python
# Nowe pole ComboBox dla wyboru klienta
self.customer_combo = ctk.CTkComboBox(
    customer_frame,
    values=customer_names,
    width=200
)
```

**Linie 650-685**: Dodano zapisywanie do `products_catalog` gdy brak `order_id`
```python
# Zapisywanie nowych produktów do katalogu
if not self.order_id:
    # Zapisz do products_catalog jako produkt niezależny
    response = self.db.client.table('products_catalog').insert(new_product_data).execute()
```

#### `products_selector_dialog.py`
**Linie 296-341**: Zmodyfikowano `load_products()` aby ładować z obu tabel
```python
# Ładowanie z katalogu produktów (nowe)
catalog_response = self.db.client.table('products_catalog').select(...)

# Ładowanie z części zamówień (istniejące)
parts_response = self.db.client.table('parts').select(...)

# Łączenie i usuwanie duplikatów
```

## Jak korzystać z nowych funkcji

### 1. Tworzenie nowego produktu bez zamówienia
1. Otwórz okno wyboru produktów: **[Nowe zamówienie]** → **[Wybierz produkty]**
2. Kliknij **[+ Nowy produkt]**
3. Wypełnij dane produktu
4. **NOWOŚĆ**: Wybierz klienta z listy rozwijanej (opcjonalne)
5. Kliknij **[Zapisz]**
6. Produkt zostanie zapisany w katalogu i będzie dostępny na liście

### 2. Używanie produktu z katalogu w zamówieniu
1. W oknie wyboru produktów produkty z katalogu są wyświetlane na górze listy
2. Wybierz produkt i przenieś go do prawej tabeli
3. Przy potwierdzeniu produkt zostanie skopiowany do części zamówienia

### 3. Statystyki użycia
Każde użycie produktu z katalogu automatycznie:
- Zwiększa licznik użycia (`usage_count`)
- Aktualizuje datę ostatniego użycia (`last_used_at`)

## Rozwiązane problemy

### Problem 1: Nowe produkty nie pojawiały się na liście
**Przyczyna**: Produkty tworzone bez `order_id` nie były zapisywane w bazie
**Rozwiązanie**: Dodano zapis do tabeli `products_catalog` dla produktów niezależnych

### Problem 2: Błąd "unknown option '-width'"
**Przyczyna**: Nieprawidłowe użycie parametru `width` w `tree.heading()`
**Rozwiązanie**: Usunięto parametr `width` z wywołań `tree.heading()`

### Problem 3: Brak możliwości przypisania produktu do klienta
**Przyczyna**: Brak pola w GUI
**Rozwiązanie**: Dodano ComboBox z listą klientów

## Korzyści z implementacji

1. **Reużywalność**: Produkty mogą być używane w wielu zamówieniach
2. **Organizacja**: Produkty są pogrupowane według klientów
3. **Analityka**: Śledzenie popularności produktów
4. **Wydajność**: Szybsze tworzenie zamówień przez wybór gotowych produktów
5. **Spójność**: Jednolite dane produktów w różnych zamówieniach

## Dalsze możliwości rozwoju

1. **Import/Export katalogu**: Możliwość importu produktów z pliku Excel/CSV
2. **Wersjonowanie**: Śledzenie historii zmian produktów
3. **Kategorie**: Dodanie kategoryzacji produktów
4. **Wyszukiwanie zaawansowane**: Filtrowanie po kliencie, materiale, grubości
5. **Szablony**: Tworzenie zestawów produktów często zamawianych razem

## Status implementacji

✅ Tabela `products_catalog` w bazie danych
✅ Pole wyboru klienta w GUI
✅ Zapisywanie nowych produktów do katalogu
✅ Ładowanie produktów z katalogu i części
✅ Usunięcie duplikatów przy wyświetlaniu
✅ Funkcja kopiowania z katalogu do zamówienia

## Uwagi techniczne

- Produkty z katalogu mają pole `_source = 'catalog'` dla identyfikacji
- Kod produktu generowany automatycznie jeśli nie podano
- RLS (Row Level Security) włączone dla tabeli `products_catalog`
- Trigger automatycznie aktualizuje pole `updated_at`

## Kontakt

W przypadku pytań lub problemów:
- Sprawdź logi aplikacji
- Zweryfikuj uprawnienia w Supabase
- Upewnij się, że tabela `products_catalog` została utworzona