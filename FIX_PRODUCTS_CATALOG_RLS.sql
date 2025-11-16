-- ============================================
-- NAPRAW POLITYKI RLS DLA TABELI products_catalog
-- ============================================

-- 1. Sprawdź czy RLS jest włączone
SELECT
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename = 'products_catalog';

-- 2. Sprawdź istniejące polityki
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE schemaname = 'public'
AND tablename = 'products_catalog';

-- 3. Usuń stare polityki (jeśli istnieją)
DROP POLICY IF EXISTS "Public read active products" ON products_catalog;
DROP POLICY IF EXISTS "Authenticated full access" ON products_catalog;
DROP POLICY IF EXISTS "Enable read access for all users" ON products_catalog;
DROP POLICY IF EXISTS "Enable insert for all users" ON products_catalog;
DROP POLICY IF EXISTS "Enable update for all users" ON products_catalog;
DROP POLICY IF EXISTS "Enable delete for all users" ON products_catalog;

-- 4. OPCJA A: Wyłącz RLS całkowicie (najłatwiejsze dla testów)
ALTER TABLE products_catalog DISABLE ROW LEVEL SECURITY;

-- 5. OPCJA B: Jeśli chcesz zachować RLS, dodaj liberalne polityki
-- Odkomentuj poniższe jeśli chcesz używać RLS:

/*
-- Włącz RLS
ALTER TABLE products_catalog ENABLE ROW LEVEL SECURITY;

-- Polityka: Każdy może czytać wszystko
CREATE POLICY "Anyone can read products"
ON products_catalog FOR SELECT
USING (true);

-- Polityka: Każdy może dodawać
CREATE POLICY "Anyone can insert products"
ON products_catalog FOR INSERT
WITH CHECK (true);

-- Polityka: Każdy może aktualizować
CREATE POLICY "Anyone can update products"
ON products_catalog FOR UPDATE
USING (true)
WITH CHECK (true);

-- Polityka: Każdy może usuwać
CREATE POLICY "Anyone can delete products"
ON products_catalog FOR DELETE
USING (true);
*/

-- 6. Weryfikacja - sprawdź status RLS
SELECT
    tablename,
    rowsecurity,
    (SELECT COUNT(*) FROM pg_policies WHERE tablename = 'products_catalog') as policy_count
FROM pg_tables
WHERE schemaname = 'public'
AND tablename = 'products_catalog';

-- 7. Test - spróbuj wstawić testowy rekord
-- INSERT INTO products_catalog (name, is_active) VALUES ('TEST PRODUCT', true);
-- DELETE FROM products_catalog WHERE name = 'TEST PRODUCT';

-- ============================================
-- JEŚLI UŻYWASZ ANON KEY (najprawdopodobniej)
-- ============================================
-- Aplikacja używa klucza 'anon' który nie ma uprawnień authenticated
-- Dlatego musisz albo:
-- A) Wyłączyć RLS (zalecane dla developmentu)
-- B) Dodać polityki dla roli 'anon'

-- Polityki dla roli ANON (jeśli RLS jest włączone):
/*
CREATE POLICY "Anon can read products"
ON products_catalog FOR SELECT
TO anon
USING (true);

CREATE POLICY "Anon can insert products"
ON products_catalog FOR INSERT
TO anon
WITH CHECK (true);

CREATE POLICY "Anon can update products"
ON products_catalog FOR UPDATE
TO anon
USING (true)
WITH CHECK (true);

CREATE POLICY "Anon can delete products"
ON products_catalog FOR DELETE
TO anon
USING (true);
*/