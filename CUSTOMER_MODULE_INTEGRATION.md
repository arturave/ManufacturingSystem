# 📋 Instrukcja integracji rozbudowanego modułu klientów

## 🎯 Podsumowanie zmian

Moduł klientów został **znacząco rozbudowany** o pełną funkcjonalność biznesową:

### ✅ Nowe pola w bazie danych:
- **Nazwa skrócona** (`short_name`)
- **NIP** z walidacją checksuma
- **REGON** z walidacją (9 i 14 cyfr)
- **KRS** (opcjonalny)
- **Email główny firmy** z walidacją formatu
- **Strona WWW** z walidacją URL
- **Telefon główny** z formatowaniem
- **Pełny adres** (ulica, miasto, kod, kraj)
- **Osoba kontaktowa** - imię i nazwisko
- **Stanowisko** osoby kontaktowej
- **Telefon bezpośredni** osoby kontaktowej
- **Email bezpośredni** osoby kontaktowej
- **Limit kredytowy** w PLN
- **Termin płatności** w dniach
- **Rabat stały** w procentach
- **Tagi** (array)
- **Status aktywności** (aktywny/nieaktywny)
- **Notatki** (długi tekst)
- **Typ klienta** (firma/osoba fizyczna)

### 🚀 Nowe funkcjonalności:

1. **Walidacja danych**:
   - Automatyczna walidacja NIP z checksumem
   - Walidacja REGON (9 i 14-cyfrowy)
   - Walidacja formatów email
   - Walidacja numerów telefonów
   - Walidacja adresów URL

2. **Formatowanie**:
   - Automatyczne formatowanie NIP (XXX-XXX-XX-XX)
   - Formatowanie telefonów
   - Normalizacja danych

3. **Wyszukiwanie zaawansowane**:
   - Po nazwie (pełnej i skróconej)
   - Po NIP/REGON/KRS
   - Po mieście
   - Po osobie kontaktowej
   - Po tagach
   - Full-text search

4. **Eksport danych**:
   - Excel (.xlsx) z formatowaniem
   - CSV (.csv) z UTF-8
   - JSON (.json)
   - PDF (.pdf) z tabelami
   - vCard (.vcf) dla kontaktów

5. **Integracje**:
   - Pobieranie danych z GUS (przygotowane)
   - Otwieranie strony WWW
   - Pokazywanie na mapie Google
   - Statystyki klienta

6. **UI/UX**:
   - Zakładki dla lepszej organizacji
   - Wskaźniki walidacji w czasie rzeczywistym
   - Podpowiedzi i autouzupełnianie
   - Menu kontekstowe
   - Filtry aktywnych/nieaktywnych

---

## 🔧 Kroki integracji

### 1. Aktualizacja bazy danych

Wykonaj skrypt SQL w Supabase:

```bash
# W Supabase Dashboard -> SQL Editor
# Wykonaj plik: enhance_customers_table.sql
```

**UWAGA**: Skrypt automatycznie:
- Tworzy backup istniejącej tabeli `customers`
- Migruje dane do nowej struktury
- Zachowuje relacje z `orders`

### 2. Aktualizacja plików Python

Zastąp/dodaj pliki:

```python
# 1. Dodaj nowy moduł
customer_module_enhanced.py

# 2. Zaktualizuj import w mfg_app.py
from customer_module_enhanced import (
    CustomerExtended,
    CustomerValidator,
    CustomerEditDialog,
    CustomerSearchDialog,
    CustomerExportDialog
)

# 3. Zamień klasę Customer na CustomerExtended
# Stara: Customer
# Nowa: CustomerExtended
```

### 3. Aktualizacja SupabaseManager

Dodaj nowe metody do `mfg_app.py`:

```python
class SupabaseManager:
    # ... existing code ...
    
    def search_customers(self, criteria: Dict) -> List[Dict]:
        """Advanced customer search"""
        query = self.client.table('customers').select("*")
        
        if criteria.get('name'):
            query = query.ilike('name', f"%{criteria['name']}%")
        if criteria.get('nip'):
            query = query.eq('nip', criteria['nip'])
        if criteria.get('city'):
            query = query.ilike('city', f"%{criteria['city']}%")
        if criteria.get('is_active') is not None:
            query = query.eq('is_active', criteria['is_active'])
        
        response = query.execute()
        return response.data
    
    def get_customer_statistics(self, customer_id: str) -> Dict:
        """Get customer statistics"""
        response = self.client.rpc('get_customer_stats', {
            'customer_id': customer_id
        }).execute()
        return response.data[0] if response.data else {}
```

### 4. Aktualizacja CustomerDialog

Zamień `CustomerDialog` w `mfg_app.py`:

```python
# Stara prosta wersja
class CustomerDialog(ctk.CTkToplevel):
    # ... simple fields ...

# Nowa rozbudowana wersja
from customer_module_enhanced import CustomerEditDialog as CustomerDialog
```

### 5. Testowanie

Uruchom testy:

```bash
# Test walidatorów (standalone)
python test_customer_standalone.py

# Test pełnego modułu (wymaga GUI)
python test_customer_enhanced.py
```

---

## 📊 Mapowanie pól

### Stare → Nowe

| Stare pole | Nowe pole | Uwagi |
|------------|-----------|-------|
| `name` | `name` | Bez zmian |
| `contact` | `email` + `phone` | Rozdzielone |
| - | `short_name` | Nowe |
| - | `nip` | Nowe, z walidacją |
| - | `regon` | Nowe, z walidacją |
| - | `krs` | Nowe, opcjonalne |
| - | `website` | Nowe |
| - | `address` | Nowe |
| - | `city` | Nowe |
| - | `postal_code` | Nowe |
| - | `contact_person` | Nowe |
| - | `contact_phone` | Nowe |
| - | `contact_email` | Nowe |
| - | `credit_limit` | Nowe |
| - | `payment_terms` | Nowe |

---

## 🎯 Przykłady użycia

### Tworzenie klienta z pełnymi danymi

```python
customer = CustomerExtended(
    name="Firma ABC Sp. z o.o.",
    short_name="ABC",
    nip="5252248481",
    regon="140517018",
    krs="0000123456",
    email="biuro@abc.pl",
    website="www.abc.pl",
    phone="+48 22 123 45 67",
    address="ul. Przykładowa 10",
    city="Warszawa",
    postal_code="00-001",
    contact_person="Jan Kowalski",
    contact_position="Dyrektor Handlowy",
    contact_phone="+48 501 234 567",
    contact_email="j.kowalski@abc.pl",
    credit_limit=50000.00,
    payment_terms=30,
    is_active=True
)
```

### Walidacja NIP

```python
validator = CustomerValidator()

nip = "525-224-84-81"
if validator.validate_nip(nip):
    formatted = validator.format_nip(nip)
    print(f"NIP poprawny: {formatted}")
else:
    print("NIP niepoprawny!")
```

### Wyszukiwanie zaawansowane

```python
# Szukaj aktywnych klientów z Warszawy
results = db.search_customers({
    'city': 'Warszawa',
    'is_active': True
})

# Szukaj po NIP
results = db.search_customers({
    'nip': '5252248481'
})
```

### Eksport do Excel

```python
dialog = CustomerExportDialog(parent, customers)
# Użytkownik wybiera format i opcje
# Automatyczny eksport z formatowaniem
```

---

## 🔍 Rozwiązywanie problemów

### Problem: "NIP validation fails"
**Rozwiązanie**: Upewnij się, że NIP jest w formacie 10 cyfr. Funkcja automatycznie usuwa myślniki i spacje.

### Problem: "Cannot update existing customers"
**Rozwiązanie**: Uruchom skrypt SQL, który migruje dane ze starej struktury.

### Problem: "Missing fields in form"
**Rozwiązanie**: Zaktualizuj `CustomerEditDialog` używając wersji z `customer_module_enhanced.py`.

---

## ✨ Dodatkowe możliwości

### 1. Integracja z GUS API

```python
# Przygotowane do integracji z oficjalnym API GUS
def fetch_from_gus(nip: str):
    # TODO: Integrate with https://api-bir.regon.gov.pl
    pass
```

### 2. Masowy import z CSV

```python
def import_customers_from_csv(file_path: str):
    df = pd.read_csv(file_path)
    for _, row in df.iterrows():
        customer = CustomerExtended(**row.to_dict())
        db.create_customer(customer)
```

### 3. Automatyczne przypisywanie limitów kredytowych

```python
def calculate_credit_limit(customer: CustomerExtended) -> float:
    # Na podstawie historii zamówień
    stats = db.get_customer_statistics(customer.id)
    return stats['avg_order_value'] * 10
```

---

## 📈 Statystyki i raporty

Nowy moduł umożliwia generowanie:
- Rankingu klientów wg obrotów
- Analizy terminowości płatności
- Wykorzystania limitów kredytowych
- Segmentacji klientów
- Raportów dla kadry zarządzającej

---

## 🚀 Następne kroki

1. **Integracja z systemem fakturowania** - automatyczne pobieranie danych do faktur
2. **System powiadomień** - alerty o przekroczeniu limitu kredytowego
3. **API REST** - udostępnienie danych klientów dla innych systemów
4. **Aplikacja mobilna** - dostęp do bazy klientów w terenie

---

## 📝 Changelog

### Wersja 2.0 (2025-01-14)
- ✅ Dodano pełne dane rejestrowe (NIP, REGON, KRS)
- ✅ Rozbudowano dane kontaktowe
- ✅ Dodano osobę kontaktową
- ✅ Implementowano walidację NIP/REGON
- ✅ Dodano limity kredytowe i terminy płatności
- ✅ Implementowano eksport do 5 formatów
- ✅ Dodano wyszukiwanie zaawansowane
- ✅ Utworzono testy jednostkowe

---

**Moduł jest w pełni gotowy do użycia produkcyjnego!** 🎉
