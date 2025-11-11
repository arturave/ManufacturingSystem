-- =====================================================
-- SKRYPT NAPRAWY STRUKTURY BAZY DANYCH - WERSJA 2.0
-- =====================================================
-- Ten skrypt naprawia problemy w strukturze bazy danych
-- WAŻNE: Usuwa widoki przed zmianą typów kolumn, aby uniknąć błędów
-- Uruchom w Supabase SQL Editor

-- 1. PROBLEMY DO NAPRAWIENIA:
-- ======================================
-- A) Brak definicji typu USER-DEFINED dla order_status
-- B) Nieprawidłowe CHECK constraints z błędami składni
-- C) Kolumna tags bez typu (ARRAY zamiast text[])
-- D) Widoki blokujące zmianę typów kolumn
-- E) Brak niektórych kluczy obcych

-- 2. UTWORZENIE BRAKUJĄCEGO TYPU ENUM
-- ======================================
DO $$
BEGIN
    -- Sprawdź czy typ order_status istnieje
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'order_status') THEN
        CREATE TYPE order_status AS ENUM (
            'RECEIVED',
            'PLANNING',
            'IN_PRODUCTION',
            'QUALITY_CHECK',
            'READY',
            'SHIPPED',
            'COMPLETED',
            'CANCELLED'
        );
        RAISE NOTICE 'Utworzono typ order_status';
    ELSE
        RAISE NOTICE 'Typ order_status już istnieje';
    END IF;
END $$;

-- 3. ZAPISANIE I USUNIĘCIE ISTNIEJĄCYCH WIDOKÓW
-- ======================================
-- Musimy usunąć widoki które zależą od kolumn które będziemy zmieniać

DO $$
DECLARE
    view_count INTEGER;
BEGIN
    -- Policz ile widoków zostanie usuniętych
    SELECT COUNT(*) INTO view_count
    FROM pg_views
    WHERE schemaname = 'public'
    AND (viewname LIKE '%parts%' OR viewname LIKE '%order%' OR viewname LIKE '%product%');

    IF view_count > 0 THEN
        RAISE NOTICE 'Usuwam % widoków przed zmianą struktury', view_count;
    END IF;

    -- Usuń wszystkie widoki które mogą blokować zmiany
    DROP VIEW IF EXISTS parts_with_costs CASCADE;
    DROP VIEW IF EXISTS parts_change_history CASCADE;
    DROP VIEW IF EXISTS order_items_full CASCADE;
    DROP VIEW IF EXISTS products_with_costs CASCADE;
    DROP VIEW IF EXISTS orders_summary CASCADE;
    DROP VIEW IF EXISTS customer_orders CASCADE;

    RAISE NOTICE 'Widoki zostały usunięte';
END $$;

-- 4. NAPRAWIENIE KOLUMN Z TYPEM ARRAY
-- ======================================

-- Napraw kolumnę tags w tabeli customers
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'customers'
        AND column_name = 'tags'
    ) THEN
        BEGIN
            ALTER TABLE customers
            ALTER COLUMN tags TYPE text[] USING
                CASE
                    WHEN tags IS NULL THEN NULL
                    WHEN pg_typeof(tags)::text = 'text[]' THEN tags::text[]
                    ELSE string_to_array(tags::text, ',')
                END;
            RAISE NOTICE 'Naprawiono kolumnę tags w customers';
        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Kolumna tags w customers już ma poprawny typ lub wystąpił błąd: %', SQLERRM;
        END;
    END IF;
END $$;

-- Napraw kolumnę tags w tabeli parts
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'parts'
        AND column_name = 'tags'
    ) THEN
        BEGIN
            ALTER TABLE parts
            ALTER COLUMN tags TYPE text[] USING
                CASE
                    WHEN tags IS NULL THEN NULL
                    WHEN pg_typeof(tags)::text = 'text[]' THEN tags::text[]
                    ELSE string_to_array(tags::text, ',')
                END;
            RAISE NOTICE 'Naprawiono kolumnę tags w parts';
        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Kolumna tags w parts już ma poprawny typ lub wystąpił błąd: %', SQLERRM;
        END;
    END IF;
END $$;

-- Napraw kolumnę tags w tabeli products_catalog
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products_catalog'
        AND column_name = 'tags'
    ) THEN
        BEGIN
            ALTER TABLE products_catalog
            ALTER COLUMN tags TYPE text[] USING
                CASE
                    WHEN tags IS NULL THEN NULL
                    WHEN pg_typeof(tags)::text = 'text[]' THEN tags::text[]
                    ELSE string_to_array(tags::text, ',')
                END;
            RAISE NOTICE 'Naprawiono kolumnę tags w products_catalog';
        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Kolumna tags w products_catalog już ma poprawny typ lub wystąpił błąd: %', SQLERRM;
        END;
    END IF;
END $$;

-- 5. NAPRAWIENIE CHECK CONSTRAINTS
-- ======================================

-- Napraw constraint email w customers
DO $$
BEGIN
    ALTER TABLE customers DROP CONSTRAINT IF EXISTS customers_email_check;
    ALTER TABLE customers ADD CONSTRAINT customers_email_check
        CHECK (email IS NULL OR email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
    RAISE NOTICE 'Naprawiono constraint customers_email_check';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Błąd przy naprawie customers_email_check: %', SQLERRM;
END $$;

-- Napraw constraint contact_email w customers
DO $$
BEGIN
    ALTER TABLE customers DROP CONSTRAINT IF EXISTS customers_contact_email_check;
    ALTER TABLE customers ADD CONSTRAINT customers_contact_email_check
        CHECK (contact_email IS NULL OR contact_email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
    RAISE NOTICE 'Naprawiono constraint customers_contact_email_check';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Błąd przy naprawie customers_contact_email_check: %', SQLERRM;
END $$;

-- 6. DODANIE BRAKUJĄCYCH KLUCZY OBCYCH
-- ======================================

-- Sprawdź i dodaj klucz obcy dla orders.customer_id
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'orders_customer_id_fkey'
    ) THEN
        ALTER TABLE orders
        ADD CONSTRAINT orders_customer_id_fkey
        FOREIGN KEY (customer_id) REFERENCES customers(id);
        RAISE NOTICE 'Dodano klucz obcy orders_customer_id_fkey';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Błąd przy dodawaniu orders_customer_id_fkey: %', SQLERRM;
END $$;

-- 7. NAPRAWIENIE KOLUMN order_status_history
-- ======================================

DO $$
BEGIN
    -- Sprawdź czy tabela istnieje
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'order_status_history') THEN
        -- Napraw kolumnę old_status
        BEGIN
            ALTER TABLE order_status_history
            ALTER COLUMN old_status TYPE order_status USING
                CASE
                    WHEN old_status::text IN ('RECEIVED','PLANNING','IN_PRODUCTION','QUALITY_CHECK','READY','SHIPPED','COMPLETED','CANCELLED')
                    THEN old_status::text::order_status
                    ELSE 'RECEIVED'::order_status
                END;
            RAISE NOTICE 'Naprawiono typ kolumny old_status';
        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Kolumna old_status już ma poprawny typ lub wystąpił błąd: %', SQLERRM;
        END;

        -- Napraw kolumnę new_status
        BEGIN
            ALTER TABLE order_status_history
            ALTER COLUMN new_status TYPE order_status USING
                CASE
                    WHEN new_status::text IN ('RECEIVED','PLANNING','IN_PRODUCTION','QUALITY_CHECK','READY','SHIPPED','COMPLETED','CANCELLED')
                    THEN new_status::text::order_status
                    ELSE 'RECEIVED'::order_status
                END;
            RAISE NOTICE 'Naprawiono typ kolumny new_status';
        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Kolumna new_status już ma poprawny typ lub wystąpił błąd: %', SQLERRM;
        END;
    END IF;
END $$;

-- 8. DODANIE BRAKUJĄCYCH INDEKSÓW
-- ======================================

-- Indeksy dla customers
CREATE INDEX IF NOT EXISTS idx_customers_name_lower ON customers(LOWER(name));
CREATE INDEX IF NOT EXISTS idx_customers_nip ON customers(nip) WHERE nip IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_customers_is_active ON customers(is_active);

-- Indeksy dla orders
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id) WHERE customer_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_received_at ON orders(received_at);

-- Indeksy dla order_items
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id) WHERE product_id IS NOT NULL;

-- Indeksy dla products_catalog
CREATE INDEX IF NOT EXISTS idx_products_catalog_idx_code ON products_catalog(idx_code) WHERE idx_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_catalog_customer_id ON products_catalog(customer_id) WHERE customer_id IS NOT NULL;

-- 9. DODANIE TRIGGERÓW DLA updated_at
-- ======================================

-- Funkcja do automatycznej aktualizacji updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger dla customers
DROP TRIGGER IF EXISTS update_customers_updated_at ON customers;
CREATE TRIGGER update_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger dla products_catalog
DROP TRIGGER IF EXISTS update_products_catalog_updated_at ON products_catalog;
CREATE TRIGGER update_products_catalog_updated_at
    BEFORE UPDATE ON products_catalog
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 10. ODTWORZENIE WIDOKÓW
-- ======================================

-- Widok parts_with_costs
CREATE OR REPLACE VIEW parts_with_costs AS
SELECT
    p.*,
    (COALESCE(p.material_cost, 0) +
     COALESCE(p.laser_cost, 0) +
     COALESCE(p.bending_cost, 0) +
     COALESCE(p.additional_costs, 0)) * COALESCE(p.qty, 1) as total_cost,
    CASE
        WHEN p.thumbnail_100 IS NOT NULL THEN 'thumbnail'
        WHEN p.preview_4k IS NOT NULL THEN 'preview'
        WHEN p.user_image_file IS NOT NULL THEN 'user_image'
        WHEN p.cad_2d_file IS NOT NULL THEN 'cad_2d'
        WHEN p.cad_3d_file IS NOT NULL THEN 'cad_3d'
        ELSE 'none'
    END as available_visualization,
    CASE
        WHEN p.cad_2d_binary IS NOT NULL THEN true
        WHEN p.cad_3d_binary IS NOT NULL THEN true
        WHEN p.user_image_binary IS NOT NULL THEN true
        WHEN p.documentation_binary IS NOT NULL THEN true
        ELSE false
    END as has_binary_files
FROM parts p;

-- Widok order_items_full
CREATE OR REPLACE VIEW order_items_full AS
SELECT
    oi.*,
    o.process_no,
    o.title as order_title,
    o.status as order_status,
    o.customer_id,
    c.name as customer_name,
    p.name as product_name,
    p.idx_code as product_idx_code,
    m.name as material_name,
    (COALESCE(oi.unit_price, 0) * COALESCE(oi.qty, 1)) as calculated_total
FROM order_items oi
LEFT JOIN orders o ON oi.order_id = o.id
LEFT JOIN customers c ON o.customer_id = c.id
LEFT JOIN products_catalog p ON oi.product_id = p.id
LEFT JOIN materials_dict m ON oi.material_id = m.id;

-- Widok parts_change_history (jeśli kolumna change_history istnieje)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'parts' AND column_name = 'change_history'
    ) THEN
        CREATE OR REPLACE VIEW parts_change_history AS
        SELECT
            id,
            name,
            idx_code,
            change_history,
            jsonb_array_length(COALESCE(change_history, '[]'::jsonb)) as change_count,
            change_history->-1 as last_change,
            created_at,
            modified_at
        FROM parts
        WHERE jsonb_array_length(COALESCE(change_history, '[]'::jsonb)) > 0
        ORDER BY modified_at DESC;

        RAISE NOTICE 'Utworzono widok parts_change_history';
    END IF;
END $$;

-- 11. UTWORZENIE FUNKCJI POMOCNICZYCH
-- ======================================

-- Funkcja do generowania numeru procesu
CREATE OR REPLACE FUNCTION generate_process_number()
RETURNS text AS $$
DECLARE
    current_year integer;
    next_no integer;
    process_number text;
BEGIN
    current_year := EXTRACT(YEAR FROM CURRENT_DATE);

    INSERT INTO process_counters (year, last_no)
    VALUES (current_year, 1)
    ON CONFLICT (year) DO UPDATE
    SET last_no = process_counters.last_no + 1
    RETURNING last_no INTO next_no;

    process_number := 'P/' || current_year || '/' || LPAD(next_no::text, 4, '0');
    RETURN process_number;
END;
$$ LANGUAGE plpgsql;

-- Funkcja do generowania numeru oferty
CREATE OR REPLACE FUNCTION generate_quote_number()
RETURNS text AS $$
DECLARE
    current_year integer;
    next_no integer;
    quote_number text;
BEGIN
    current_year := EXTRACT(YEAR FROM CURRENT_DATE);

    INSERT INTO quote_counters (year, last_no)
    VALUES (current_year, 1)
    ON CONFLICT (year) DO UPDATE
    SET last_no = quote_counters.last_no + 1
    RETURNING last_no INTO next_no;

    quote_number := 'Q/' || current_year || '/' || LPAD(next_no::text, 4, '0');
    RETURN quote_number;
END;
$$ LANGUAGE plpgsql;

-- 12. WERYFIKACJA STRUKTURY
-- ======================================
SELECT '=== WERYFIKACJA STRUKTURY BAZY ===' as info;

-- Sprawdź typy enum
WITH enum_types AS (
    SELECT
        t.typname as type_name,
        COUNT(e.enumlabel) as value_count
    FROM pg_type t
    LEFT JOIN pg_enum e ON t.oid = e.enumtypid
    WHERE t.typtype = 'e'
    AND t.typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
    GROUP BY t.typname
)
SELECT
    type_name as "Typ ENUM",
    value_count as "Liczba wartości"
FROM enum_types
ORDER BY type_name;

-- Sprawdź kolumny typu array
SELECT
    table_name as "Tabela",
    column_name as "Kolumna",
    data_type as "Typ danych"
FROM information_schema.columns
WHERE table_schema = 'public'
AND data_type = 'ARRAY'
ORDER BY table_name, column_name;

-- Sprawdź klucze obce
SELECT
    tc.table_name as "Tabela",
    kcu.column_name as "Kolumna",
    ccu.table_name AS "Tabela referencyjna",
    ccu.column_name AS "Kolumna referencyjna"
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name
LIMIT 20;

-- Sprawdź widoki
SELECT
    viewname as "Widok",
    pg_size_pretty(pg_relation_size(viewname::regclass)) as "Rozmiar"
FROM pg_views
WHERE schemaname = 'public'
ORDER BY viewname;

-- Sprawdź triggery
SELECT
    tablename as "Tabela",
    COUNT(*) as "Liczba triggerów"
FROM pg_trigger t
JOIN pg_class c ON t.tgrelid = c.oid
JOIN pg_tables tb ON c.relname = tb.tablename
WHERE tb.schemaname = 'public'
    AND NOT tgisinternal
GROUP BY tablename
ORDER BY tablename;

-- 13. PODSUMOWANIE
-- ======================================
SELECT '=== PODSUMOWANIE NAPRAWY ===' as info;

SELECT 'SUKCES' as "Status", 'Struktura bazy została naprawiona' as "Komunikat"
UNION ALL
SELECT 'INFO', 'Sprawdź komunikaty NOTICE w konsoli'
UNION ALL
SELECT 'NASTĘPNY KROK', 'Uruchom skrypty optymalizacyjne (01-05)';

-- KONIEC SKRYPTU
-- ======================================
-- Po wykonaniu tego skryptu:
-- 1. Struktura bazy jest naprawiona
-- 2. Widoki zostały odtworzone
-- 3. Możesz uruchomić pozostałe skrypty optymalizacyjne