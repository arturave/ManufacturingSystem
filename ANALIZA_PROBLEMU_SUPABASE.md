# 🔍 Analiza problemu z dodawaniem danych do Supabase

## 📋 Opis problemu

**Symptom:** Mimo poprawnego połączenia z Supabase nie można dodawać danych do tabeli `customers`.

**Ostrzeżenie Supabase:**
```
Title: Security Definer View
Entity: public.v_customer_contacts
Schema: public
Issue: View `public.v_customer_contacts` is defined with the SECURITY DEFINER property
```

---

## 🔎 Przyczyny problemu

### 1. **SECURITY DEFINER na widokach** ⚠️

**Problem:**
- Widoki `v_customer_contacts` i `v_customer_statistics` mogą być automatycznie tworzone przez Supabase jako SECURITY DEFINER
- SECURITY DEFINER oznacza, że widok działa z uprawnieniami **twórcy**, a nie użytkownika
- To może powodować konflikty z politykami RLS

**Skutek:**
- Użytkownik może nie mieć uprawnień do modyfikacji danych
- Polityki RLS mogą nie działać prawidłowo

### 2. **Triggery walidacyjne** 🚫

**Zidentyfikowane triggery w `enhance_customers_table.sql`:**

```sql
-- Trigger walidujący NIP i REGON
CREATE TRIGGER trg_validate_customer_tax_numbers
BEFORE INSERT OR UPDATE ON customers
FOR EACH ROW
EXECUTE FUNCTION validate_customer_tax_numbers();
```

**Problem:**
- Trigger **rzuca wyjątek** (`RAISE EXCEPTION`) jeśli NIP lub REGON są nieprawidłowe
- Blokuje całkowicie operację INSERT/UPDATE

**Warunki wywołania błędu:**
```sql
IF NEW.customer_type = 'company' AND NEW.nip IS NOT NULL AND NEW.nip != '' THEN
    IF NOT validate_nip(NEW.nip) THEN
        RAISE EXCEPTION 'Invalid NIP number: %', NEW.nip;  -- ❌ BLOKUJE OPERACJĘ
    END IF;
END IF;
```

### 3. **Constraints na tabeli customers** 🔒

**Zidentyfikowane ograniczenia:**

1. **NIP musi być UNIQUE** - duplikaty są blokowane
   ```sql
   nip TEXT UNIQUE,
   ```

2. **Walidacja formatu email:**
   ```sql
   CONSTRAINT check_email_format CHECK (
       email IS NULL OR
       email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
   )
   ```

3. **Walidacja contact_email:**
   ```sql
   CONSTRAINT check_contact_email_format CHECK (
       contact_email IS NULL OR
       contact_email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
   )
   ```

4. **Walidacja customer_type:**
   ```sql
   CONSTRAINT check_customer_type CHECK (
       customer_type IN ('company', 'individual')
   )
   ```

5. **Walidacja payment_terms:**
   ```sql
   CONSTRAINT check_payment_terms CHECK (payment_terms >= 0)
   ```

6. **Walidacja credit_limit:**
   ```sql
   CONSTRAINT check_credit_limit CHECK (credit_limit >= 0)
   ```

### 4. **Algorytmy walidacji NIP/REGON** 📊

**Zidentyfikowany problem z algorytmami:**

Z testów (`test_customer_standalone.py`) widać, że:
```
❌ 9542742927      - Valid NIP #3: False  (powinien być True)
❌ 1234567890      - Invalid checksum: True  (powinien być False)
❌ 140517018       - Valid 9-digit REGON: False  (powinien być True)
❌ 273339110       - Valid 9-digit REGON #2: False  (powinien być True)
```

**Skutek:**
- Prawidłowe numery NIP/REGON są odrzucane jako nieprawidłowe
- Użytkownik nie może dodać klienta z prawdziwym NIP/REGON

---

## ✅ Rozwiązania

### **Rozwiązanie 1: Napraw widoki (PRIORYTET 1)** 🎯

**Wykonaj skrypt:** `fix_supabase_security.sql`

```sql
-- Usuń SECURITY DEFINER, użyj SECURITY INVOKER
DROP VIEW IF EXISTS v_customer_contacts;
CREATE VIEW v_customer_contacts
SECURITY INVOKER  -- ✅ Używa uprawnień użytkownika
AS
SELECT ... FROM customers c WHERE c.is_active = TRUE;
```

**Wykonanie w Supabase:**
1. Otwórz **SQL Editor** w Supabase Dashboard
2. Wklej zawartość pliku `fix_supabase_security.sql`
3. Kliknij **Run**

---

### **Rozwiązanie 2: Wyłącz lub złagodź walidację NIP/REGON** 🔧

**Opcja A: Całkowicie wyłącz trigger (jeśli chcesz dodawać dane bez walidacji)**

```sql
-- Wyłącz trigger walidacji
DROP TRIGGER IF EXISTS trg_validate_customer_tax_numbers ON customers;
```

**Opcja B: Zmień na ostrzeżenie zamiast błędu (ZALECANE)**

```sql
CREATE OR REPLACE FUNCTION validate_customer_tax_numbers()
RETURNS TRIGGER AS $$
BEGIN
    -- Waliduj NIP, ale tylko ostrzeż zamiast blokować
    IF NEW.customer_type = 'company' AND NEW.nip IS NOT NULL AND NEW.nip != '' THEN
        IF NOT validate_nip(NEW.nip) THEN
            RAISE WARNING 'Nieprawidłowy NIP: %. Operacja kontynuowana.', NEW.nip;
            -- ✅ Nie blokuj operacji
        END IF;
    END IF;

    -- Waliduj REGON
    IF NEW.regon IS NOT NULL AND NEW.regon != '' THEN
        IF NOT validate_regon(NEW.regon) THEN
            RAISE WARNING 'Nieprawidłowy REGON: %. Operacja kontynuowana.', NEW.regon;
            -- ✅ Nie blokuj operacji
        END IF;
    END IF;

    RETURN NEW;  -- ✅ Zawsze zwróć NEW
END;
$$ LANGUAGE plpgsql;
```

**Opcja C: Pozwól na puste NIP/REGON**

```sql
CREATE OR REPLACE FUNCTION validate_customer_tax_numbers()
RETURNS TRIGGER AS $$
BEGIN
    -- Waliduj tylko jeśli podano wartość
    -- Jeśli NIP jest pusty lub NULL, pomiń walidację
    IF NEW.customer_type = 'company'
       AND NEW.nip IS NOT NULL
       AND NEW.nip != ''
       AND LENGTH(REPLACE(REPLACE(NEW.nip, '-', ''), ' ', '')) = 10 THEN
        IF NOT validate_nip(NEW.nip) THEN
            RAISE EXCEPTION 'Invalid NIP number: %', NEW.nip;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

### **Rozwiązanie 3: Napraw algorytmy walidacji NIP/REGON** 🔢

**Problem:** Algorytmy mogą być nieprawidłowe.

**Test walidacji:**
```sql
-- Test NIP
SELECT validate_nip('5252248481');  -- Powinien zwrócić TRUE
SELECT validate_nip('9542742927');  -- Powinien zwrócić TRUE
SELECT validate_nip('1234567890');  -- Powinien zwrócić FALSE

-- Test REGON
SELECT validate_regon('140517018');  -- Powinien zwrócić TRUE
SELECT validate_regon('273339110');  -- Powinien zwrócić TRUE
```

**Jeśli testy nie przechodzą, napraw algorytm w `enhance_customers_table.sql`**

---

### **Rozwiązanie 4: Dodawanie danych z obsługą błędów** 💻

**W kodzie Python (`mfg_app.py`):**

Dodaj lepszą obsługę błędów w metodzie `create_customer`:

```python
def create_customer(self, customer: CustomerExtended) -> Optional[Dict]:
    try:
        # Przygotuj dane
        data = customer.to_dict() if hasattr(customer, 'to_dict') else { ... }

        # Usuń puste wartości, które mogą powodować problemy z constraints
        data = {k: v for k, v in data.items() if v not in [None, '', []]}

        # Ustaw domyślne wartości
        if 'customer_type' not in data:
            data['customer_type'] = 'company'
        if 'is_active' not in data:
            data['is_active'] = True

        # Wyczyść NIP z myślników przed wysłaniem
        if 'nip' in data and data['nip']:
            data['nip'] = data['nip'].replace('-', '').replace(' ', '')

        response = self.client.table('customers').insert(data).execute()
        return response.data[0] if response.data else None

    except Exception as e:
        # Loguj szczegółowy błąd
        print(f"Error creating customer: {e}")
        print(f"Data attempted: {data}")

        # Sprawdź typ błędu
        error_message = str(e)
        if 'Invalid NIP' in error_message:
            print("❌ Błąd walidacji NIP - sprawdź numer")
        elif 'duplicate key' in error_message:
            print("❌ Klient z tym NIP już istnieje")
        elif 'check_email_format' in error_message:
            print("❌ Nieprawidłowy format email")

        return None
```

---

## 🎯 Plan działania (Krok po kroku)

### **Krok 1: Diagnoza** 🔍

Wykonaj w Supabase SQL Editor:

```sql
-- Sprawdź triggery
SELECT trigger_name, event_manipulation, action_statement
FROM information_schema.triggers
WHERE event_object_table = 'customers';

-- Sprawdź polityki RLS
SELECT policyname, cmd, qual, with_check
FROM pg_policies
WHERE tablename = 'customers';

-- Sprawdź uprawnienia
SELECT grantee, privilege_type
FROM information_schema.role_table_grants
WHERE table_name = 'customers' AND grantee = 'anon';
```

### **Krok 2: Napraw widoki** ⚙️

```sql
-- Wykonaj plik fix_supabase_security.sql
```

### **Krok 3: Test dodawania danych** 🧪

```sql
-- Spróbuj dodać prostego klienta (bez NIP)
INSERT INTO customers (name, email, customer_type, is_active)
VALUES ('Test Klient', 'test@example.com', 'company', true);

-- Jeśli działa, spróbuj z NIP
INSERT INTO customers (name, nip, email, customer_type, is_active)
VALUES ('Test Klient 2', '5252248481', 'test2@example.com', 'company', true);
```

### **Krok 4: Jeśli nadal nie działa** 🛠️

```sql
-- Wyłącz trigger walidacji
DROP TRIGGER IF EXISTS trg_validate_customer_tax_numbers ON customers;

-- Spróbuj ponownie dodać dane
```

### **Krok 5: Weryfikacja** ✅

```sql
-- Sprawdź czy dane zostały dodane
SELECT * FROM customers ORDER BY created_at DESC LIMIT 5;
```

---

## 📊 Podsumowanie

| Problem | Priorytet | Rozwiązanie |
|---------|-----------|-------------|
| SECURITY DEFINER na widokach | 🔴 WYSOKI | Wykonaj `fix_supabase_security.sql` |
| Trigger walidacji NIP/REGON | 🔴 WYSOKI | Wyłącz lub zmień na WARNING |
| Błędy w algorytmach walidacji | 🟡 ŚREDNI | Napraw algorytmy lub wyłącz |
| Constraints na email/NIP | 🟢 NISKI | Upewnij się, że dane są prawidłowe |

---

## 🚀 Szybkie rozwiązanie (TLDR)

**Jeśli chcesz szybko dodawać dane:**

```sql
-- 1. Napraw widoki
\i fix_supabase_security.sql

-- 2. Wyłącz walidację NIP/REGON (tymczasowo)
DROP TRIGGER IF EXISTS trg_validate_customer_tax_numbers ON customers;

-- 3. Teraz możesz dodawać dane!
```

**Gotowe!** Powinieneś móc dodawać dane do tabeli `customers`. 🎉
