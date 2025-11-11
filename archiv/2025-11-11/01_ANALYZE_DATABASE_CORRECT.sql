-- =====================================================
-- SKRYPT 1: ANALIZA BIEŻĄCEJ STRUKTURY BAZY DANYCH
-- =====================================================
-- Uruchom ten skrypt NAJPIERW, aby zrozumieć stan bazy
-- Wykonaj w Supabase SQL Editor

-- 1. LISTA WSZYSTKICH TABEL W BAZIE
-- ======================================
SELECT '=== WSZYSTKIE TABELE W BAZIE ===' as info;

SELECT
    tablename as "Nazwa tabeli",
    pg_size_pretty(pg_total_relation_size('public.'||tablename)) as "Rozmiar"
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size('public.'||tablename) DESC;

-- 2. SZCZEGÓŁOWA STRUKTURA TABELI PARTS
-- ======================================
SELECT '=== STRUKTURA TABELI PARTS ===' as info;

SELECT
    column_name as "Kolumna",
    data_type as "Typ danych",
    is_nullable as "Nullable",
    column_default as "Wartość domyślna",
    character_maximum_length as "Max długość"
FROM information_schema.columns
WHERE table_name = 'parts'
ORDER BY ordinal_position;

-- 3. STRUKTURA TABELI PRODUCTS_CATALOG (jeśli istnieje)
-- ======================================
SELECT '=== STRUKTURA TABELI PRODUCTS_CATALOG ===' as info;

SELECT
    CASE
        WHEN COUNT(*) > 0 THEN 'Tabela products_catalog ISTNIEJE'
        ELSE 'Tabela products_catalog NIE ISTNIEJE'
    END as status
FROM information_schema.tables
WHERE table_name = 'products_catalog';

-- Jeśli istnieje, pokaż strukturę
SELECT
    column_name as "Kolumna",
    data_type as "Typ danych",
    is_nullable as "Nullable",
    column_default as "Wartość domyślna"
FROM information_schema.columns
WHERE table_name = 'products_catalog'
ORDER BY ordinal_position;

-- 4. STRUKTURA TABELI ORDER_ITEMS (jeśli istnieje)
-- ======================================
SELECT '=== STRUKTURA TABELI ORDER_ITEMS ===' as info;

SELECT
    CASE
        WHEN COUNT(*) > 0 THEN 'Tabela order_items ISTNIEJE'
        ELSE 'Tabela order_items NIE ISTNIEJE'
    END as status
FROM information_schema.tables
WHERE table_name = 'order_items';

-- 5. ANALIZA DANYCH W TABELI PARTS
-- ======================================
SELECT '=== ANALIZA DANYCH W PARTS ===' as info;

SELECT
    COUNT(*) as "Wszystkie rekordy",
    COUNT(CASE WHEN cad_2d_file IS NOT NULL THEN 1 END) as "Rekordy z CAD 2D",
    COUNT(CASE WHEN cad_3d_file IS NOT NULL THEN 1 END) as "Rekordy z CAD 3D",
    COUNT(CASE WHEN user_image_file IS NOT NULL THEN 1 END) as "Rekordy z obrazem",
    COUNT(CASE WHEN thumbnail_100 IS NOT NULL THEN 1 END) as "Rekordy z thumbnail",
    COUNT(CASE WHEN preview_4k IS NOT NULL THEN 1 END) as "Rekordy z preview 4K"
FROM parts;

-- 6. SPRAWDZENIE ŚCIEŻEK LOKALNYCH
-- ======================================
SELECT '=== ŚCIEŻKI LOKALNE W PARTS ===' as info;

SELECT
    COUNT(CASE WHEN cad_2d_file LIKE 'C:\%' OR cad_2d_file LIKE 'C:/%' THEN 1 END) as "CAD 2D z lokalną ścieżką",
    COUNT(CASE WHEN cad_3d_file LIKE 'C:\%' OR cad_3d_file LIKE 'C:/%' THEN 1 END) as "CAD 3D z lokalną ścieżką",
    COUNT(CASE WHEN user_image_file LIKE 'C:\%' OR user_image_file LIKE 'C:/%' THEN 1 END) as "Obrazy z lokalną ścieżką",
    COUNT(CASE WHEN documentation_path LIKE '%:\%' OR documentation_path LIKE '%:/%' THEN 1 END) as "Dokumenty z lokalną ścieżką"
FROM parts;

-- Przykłady ścieżek lokalnych (pierwsze 5)
SELECT
    id,
    name,
    cad_2d_file,
    cad_3d_file,
    user_image_file
FROM parts
WHERE
    cad_2d_file LIKE '%:\%' OR cad_2d_file LIKE '%:/%'
    OR cad_3d_file LIKE '%:\%' OR cad_3d_file LIKE '%:/%'
    OR user_image_file LIKE '%:\%' OR user_image_file LIKE '%:/%'
LIMIT 5;

-- 7. SPRAWDZENIE INDEKSÓW
-- ======================================
SELECT '=== ISTNIEJĄCE INDEKSY NA PARTS ===' as info;

SELECT
    indexname as "Nazwa indeksu",
    indexdef as "Definicja"
FROM pg_indexes
WHERE tablename = 'parts'
ORDER BY indexname;

-- 8. SPRAWDZENIE KLUCZY OBCYCH
-- ======================================
SELECT '=== KLUCZE OBCE W PARTS ===' as info;

SELECT
    tc.constraint_name as "Nazwa klucza",
    kcu.column_name as "Kolumna",
    ccu.table_name AS "Tabela referencyjna",
    ccu.column_name AS "Kolumna referencyjna"
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'parts'
    AND tc.constraint_type = 'FOREIGN KEY';

-- 9. SPRAWDZENIE ROZMIARU DANYCH BINARNYCH
-- ======================================
SELECT '=== ROZMIAR DANYCH BINARNYCH W PARTS ===' as info;

SELECT
    COUNT(*) as "Rekordy z danymi binarnymi",
    pg_size_pretty(SUM(pg_column_size(thumbnail_100))) as "Rozmiar thumbnail_100",
    pg_size_pretty(SUM(pg_column_size(preview_4k))) as "Rozmiar preview_4k",
    pg_size_pretty(SUM(pg_column_size(thumbnail_100) + pg_column_size(preview_4k))) as "Całkowity rozmiar binarny"
FROM parts
WHERE thumbnail_100 IS NOT NULL OR preview_4k IS NOT NULL;

-- 10. PODSUMOWANIE
-- ======================================
SELECT '=== PODSUMOWANIE ===' as info;

SELECT
    'Tabela parts' as "Obiekt",
    COUNT(*) as "Liczba rekordów",
    pg_size_pretty(pg_total_relation_size('parts')) as "Rozmiar całkowity"
FROM parts;