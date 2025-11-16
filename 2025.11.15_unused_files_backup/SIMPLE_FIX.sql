-- ============================================
-- SIMPLE_FIX.sql
-- Prosty skrypt naprawczy - usuwa problematyczne triggery
-- ============================================

-- Wyłącz wszystkie triggery
ALTER TABLE products_catalog DISABLE TRIGGER ALL;

-- Usuń wszystkie triggery użytkownika
DO $$
DECLARE
    t_name TEXT;
BEGIN
    FOR t_name IN
        SELECT tgname
        FROM pg_trigger
        WHERE tgrelid = 'products_catalog'::regclass
            AND NOT tgisinternal
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS %I ON products_catalog CASCADE', t_name);
        RAISE NOTICE 'Usunięto trigger: %', t_name;
    END LOOP;
END $$;

-- Usuń stare kolumny jeśli istnieją
ALTER TABLE products_catalog
DROP COLUMN IF EXISTS cad_2d_file CASCADE,
DROP COLUMN IF EXISTS cad_3d_file CASCADE,
DROP COLUMN IF EXISTS user_image_file CASCADE;

-- Stwórz prosty trigger dla updated_at
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_products_timestamp
    BEFORE UPDATE ON products_catalog
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Włącz triggery
ALTER TABLE products_catalog ENABLE TRIGGER ALL;

-- Test
UPDATE products_catalog
SET notes = notes
WHERE id = (SELECT id FROM products_catalog LIMIT 1);

-- Wynik
SELECT 'Naprawiono!' as status;