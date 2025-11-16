-- SKRYPT DIAGNOSTYCZNY I NAPRAWCZY DLA TRIGGERÓW
-- ================================================

-- 1. Znajdź wszystkie funkcje triggerów które odwołują się do pól cad_2d_file lub cad_3d_file
SELECT
    p.proname AS function_name,
    p.prosrc AS function_source
FROM
    pg_proc p
WHERE
    p.prosrc LIKE '%cad_2d_file%'
    OR p.prosrc LIKE '%cad_3d_file%'
    OR p.prosrc LIKE '%OLD.cad%'
    OR p.prosrc LIKE '%NEW.cad%';

-- 2. Znajdź wszystkie triggery na tabeli products_catalog
SELECT
    t.tgname as trigger_name,
    p.proname as function_name,
    pg_get_triggerdef(t.oid) as trigger_definition
FROM
    pg_trigger t
    JOIN pg_proc p ON t.tgfoid = p.oid
WHERE
    t.tgrelid = 'products_catalog'::regclass
    AND NOT t.tgisinternal
ORDER BY
    t.tgname;

-- 3. Usuń wszystkie niestandardowe triggery (zachowaj tylko systemowe)
DO $$
DECLARE
    r RECORD;
BEGIN
    -- Usuń wszystkie triggery oprócz systemowych
    FOR r IN (
        SELECT tgname
        FROM pg_trigger
        WHERE tgrelid = 'products_catalog'::regclass
        AND NOT tgisinternal
        AND tgname != 'update_products_catalog_modtime'  -- zachowaj ten jeśli istnieje
    ) LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS %I ON products_catalog', r.tgname);
        RAISE NOTICE 'Dropped trigger: %', r.tgname;
    END LOOP;
END $$;

-- 4. Usuń funkcje które mogą powodować problemy
DROP FUNCTION IF EXISTS check_product_update() CASCADE;
DROP FUNCTION IF EXISTS validate_product_update() CASCADE;
DROP FUNCTION IF EXISTS product_update_check() CASCADE;

-- 5. Stwórz tylko niezbędny trigger dla updated_at
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Usuń stary trigger jeśli istnieje i stwórz nowy
DROP TRIGGER IF EXISTS update_products_catalog_modtime ON products_catalog;

CREATE TRIGGER update_products_catalog_modtime
    BEFORE UPDATE ON products_catalog
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- 6. Upewnij się że wszystkie potrzebne kolumny istnieją
-- Lista kolumn które mogą być używane przez kod
ALTER TABLE products_catalog
    ADD COLUMN IF NOT EXISTS cad_2d_filename TEXT,
    ADD COLUMN IF NOT EXISTS cad_3d_filename TEXT,
    ADD COLUMN IF NOT EXISTS cad_2d_filesize INTEGER,
    ADD COLUMN IF NOT EXISTS cad_3d_filesize INTEGER,
    ADD COLUMN IF NOT EXISTS user_image_filename TEXT,
    ADD COLUMN IF NOT EXISTS user_image_filesize INTEGER,
    ADD COLUMN IF NOT EXISTS additional_documentation_filename TEXT,
    ADD COLUMN IF NOT EXISTS additional_documentation_filesize INTEGER,
    ADD COLUMN IF NOT EXISTS primary_graphic_source TEXT;

-- 7. Sprawdź końcowy stan
SELECT '=== TRIGGERY PO NAPRAWIE ===' as info;
SELECT
    t.tgname as trigger_name,
    p.proname as function_name
FROM
    pg_trigger t
    JOIN pg_proc p ON t.tgfoid = p.oid
WHERE
    t.tgrelid = 'products_catalog'::regclass
    AND NOT t.tgisinternal;

SELECT '=== KOLUMNY ZWIĄZANE Z PLIKAMI ===' as info;
SELECT
    column_name,
    data_type,
    is_nullable
FROM
    information_schema.columns
WHERE
    table_schema = 'public'
    AND table_name = 'products_catalog'
    AND (
        column_name LIKE '%file%'
        OR column_name LIKE '%cad%'
        OR column_name LIKE '%image%'
        OR column_name LIKE '%documentation%'
        OR column_name LIKE '%graphic%'
    )
ORDER BY
    column_name;