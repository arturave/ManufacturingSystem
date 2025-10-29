# ⚠️ INSTRUKCJA PILNA - Utworzenie tabeli products_catalog

## Problem
Aplikacja próbuje używać tabeli `products_catalog`, która nie istnieje w bazie danych.
Powoduje to błąd przy wybieraniu produktów.

## Rozwiązanie - Wykonaj TERAZ:

### Krok 1: Zaloguj się do Supabase
1. Otwórz przeglądarkę
2. Przejdź do: https://supabase.com/dashboard
3. Zaloguj się i wybierz swój projekt

### Krok 2: Otwórz SQL Editor
1. W menu bocznym kliknij **SQL Editor**
2. Kliknij **+ New Query**

### Krok 3: Skopiuj i wklej poniższy kod SQL

```sql
-- ============================================
-- Tabela katalogu produktów
-- Przechowuje produkty niezależnie od zamówień
-- ============================================

-- Sprawdź czy tabela już istnieje, jeśli nie - utwórz
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'products_catalog') THEN

        -- Tabela katalogu produktów
        CREATE TABLE products_catalog (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

            -- Podstawowe dane produktu
            idx_code TEXT UNIQUE,  -- Unikalny kod produktu
            name TEXT NOT NULL,
            material_id UUID REFERENCES materials_dict(id),
            thickness_mm NUMERIC(6,2),

            -- Opcjonalne przypisanie do klienta
            customer_id UUID REFERENCES customers(id),

            -- Koszty
            bending_cost NUMERIC(10,2) DEFAULT 0,
            additional_costs NUMERIC(10,2) DEFAULT 0,

            -- Grafiki i dokumentacja
            graphic_high_res TEXT,
            graphic_low_res TEXT,
            documentation_path TEXT,

            -- Dodatkowe informacje
            description TEXT,
            notes TEXT,
            tags TEXT[],

            -- Statystyki użycia
            usage_count INTEGER DEFAULT 0,  -- Ile razy użyto w zamówieniach
            last_used_at TIMESTAMPTZ,

            -- Audyt
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            created_by TEXT,
            updated_by TEXT
        );

        -- Indeksy dla wydajności
        CREATE INDEX idx_products_catalog_name ON products_catalog(name);
        CREATE INDEX idx_products_catalog_customer ON products_catalog(customer_id);
        CREATE INDEX idx_products_catalog_material ON products_catalog(material_id);
        CREATE INDEX idx_products_catalog_active ON products_catalog(is_active);
        CREATE INDEX idx_products_catalog_tags ON products_catalog USING gin(tags);

        -- Trigger dla updated_at
        CREATE OR REPLACE FUNCTION update_products_catalog_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trg_update_products_catalog_updated_at ON products_catalog;
        CREATE TRIGGER trg_update_products_catalog_updated_at
        BEFORE UPDATE ON products_catalog
        FOR EACH ROW
        EXECUTE FUNCTION update_products_catalog_updated_at();

        -- Funkcja do generowania unikalnego kodu produktu
        CREATE OR REPLACE FUNCTION generate_product_code()
        RETURNS TEXT AS $$
        DECLARE
            v_code TEXT;
            v_exists BOOLEAN;
        BEGIN
            LOOP
                -- Generuj kod w formacie P-XXXXX
                v_code := 'P-' || LPAD(FLOOR(RANDOM() * 99999)::TEXT, 5, '0');

                -- Sprawdź czy kod już istnieje
                SELECT EXISTS(SELECT 1 FROM products_catalog WHERE idx_code = v_code) INTO v_exists;

                EXIT WHEN NOT v_exists;
            END LOOP;

            RETURN v_code;
        END;
        $$ LANGUAGE plpgsql;

        -- Trigger do automatycznego generowania kodu produktu
        CREATE OR REPLACE FUNCTION set_product_code_before_insert()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.idx_code IS NULL OR LENGTH(NEW.idx_code) = 0 THEN
                NEW.idx_code := generate_product_code();
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trg_set_product_code ON products_catalog;
        CREATE TRIGGER trg_set_product_code
        BEFORE INSERT ON products_catalog
        FOR EACH ROW
        EXECUTE FUNCTION set_product_code_before_insert();

        -- Widok produktów z nazwami materiałów
        CREATE OR REPLACE VIEW v_products_catalog_full AS
        SELECT
            pc.*,
            md.name AS material_name,
            md.category AS material_category,
            md.density AS material_density,
            c.name AS customer_name,
            c.short_name AS customer_short_name
        FROM products_catalog pc
        LEFT JOIN materials_dict md ON md.id = pc.material_id
        LEFT JOIN customers c ON c.id = pc.customer_id;

        -- Funkcja do kopiowania produktu z katalogu do części zamówienia
        CREATE OR REPLACE FUNCTION copy_product_to_part(
            p_product_id UUID,
            p_order_id UUID,
            p_qty INTEGER DEFAULT 1
        )
        RETURNS UUID AS $$
        DECLARE
            v_product RECORD;
            v_part_id UUID;
        BEGIN
            -- Pobierz produkt
            SELECT * INTO v_product FROM products_catalog WHERE id = p_product_id;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Produkt nie został znaleziony: %', p_product_id;
            END IF;

            -- Utwórz część na podstawie produktu
            INSERT INTO parts (
                order_id,
                idx_code,
                name,
                material_id,
                thickness_mm,
                qty,
                bending_cost,
                additional_costs,
                graphic_high_res,
                graphic_low_res,
                documentation_path
            ) VALUES (
                p_order_id,
                v_product.idx_code,
                v_product.name,
                v_product.material_id,
                v_product.thickness_mm,
                p_qty,
                v_product.bending_cost,
                v_product.additional_costs,
                v_product.graphic_high_res,
                v_product.graphic_low_res,
                v_product.documentation_path
            ) RETURNING id INTO v_part_id;

            -- Zaktualizuj statystyki użycia produktu
            UPDATE products_catalog
            SET usage_count = usage_count + 1,
                last_used_at = NOW()
            WHERE id = p_product_id;

            RETURN v_part_id;
        END;
        $$ LANGUAGE plpgsql;

        RAISE NOTICE 'Tabela products_catalog została utworzona pomyślnie';
    ELSE
        RAISE NOTICE 'Tabela products_catalog już istnieje';
    END IF;
END $$;

-- Uprawnienia dla roli anon (MVP)
GRANT SELECT, INSERT, UPDATE, DELETE ON products_catalog TO anon;
GRANT SELECT ON v_products_catalog_full TO anon;
GRANT EXECUTE ON FUNCTION generate_product_code() TO anon;
GRANT EXECUTE ON FUNCTION copy_product_to_part(UUID, UUID, INTEGER) TO anon;

-- Row Level Security
ALTER TABLE products_catalog ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS products_catalog_anon_all ON products_catalog;
CREATE POLICY products_catalog_anon_all ON products_catalog
    FOR ALL TO anon
    USING (true)
    WITH CHECK (true);

DO $$
BEGIN
    RAISE NOTICE '✅ Tabela products_catalog jest gotowa do użycia';
    RAISE NOTICE '✅ Produkty mogą być teraz zapisywane niezależnie od zamówień';
END $$;
```

### Krok 4: Wykonaj skrypt
1. Kliknij przycisk **RUN** (lub Ctrl+Enter)
2. Poczekaj na komunikat sukcesu

### Krok 5: Weryfikacja
1. W SQL Editor wpisz i wykonaj:
```sql
SELECT * FROM products_catalog;
```
2. Powinno zwrócić pustą tabelę bez błędów

## Co zostanie utworzone:

✅ Tabela `products_catalog` - przechowuje produkty niezależne od zamówień
✅ Automatyczne generowanie kodów produktów (P-XXXXX)
✅ Możliwość przypisania produktu do klienta
✅ Śledzenie statystyk użycia
✅ Funkcje pomocnicze i triggery
✅ Odpowiednie uprawnienia

## Po wykonaniu:

1. **Uruchom ponownie aplikację**
2. Wybierz **[Nowe zamówienie]** → **[Wybierz produkty]**
3. Błąd powinien zniknąć
4. Możesz teraz tworzyć nowe produkty klikając **[+Nowy produkt]**

## Jeśli nadal występuje błąd:

1. Sprawdź czy skrypt wykonał się bez błędów
2. Odśwież cache Supabase (Settings → API → Reload Schema Cache)
3. Sprawdź uprawnienia użytkownika `anon`

## Kontakt w razie problemów:

Jeśli po wykonaniu skryptu nadal występują problemy:
1. Sprawdź logi w Supabase (Logs → API logs)
2. Zweryfikuj czy tabela istnieje: Table Editor → products_catalog
3. Upewnij się że RLS jest włączone i polityki są aktywne

---

**WAŻNE**: Ten skrypt należy wykonać TYLKO RAZ. Ponowne wykonanie nie spowoduje problemów (skrypt sprawdza czy tabela istnieje), ale nie jest konieczne.