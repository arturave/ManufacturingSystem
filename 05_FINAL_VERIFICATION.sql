-- =====================================================
-- SKRYPT 5: WERYFIKACJA KOŃCOWA I RAPORT
-- =====================================================
-- Ten skrypt sprawdza stan bazy po wszystkich zmianach
-- Uruchom w Supabase SQL Editor

-- 1. INFORMACJE O BAZIE DANYCH
-- ======================================
SELECT '=== INFORMACJE O BAZIE DANYCH ===' as info;

SELECT
    current_database() as "Nazwa bazy",
    pg_database_size(current_database()) as "Rozmiar (bajty)",
    pg_size_pretty(pg_database_size(current_database())) as "Rozmiar",
    version() as "Wersja PostgreSQL";

-- 2. STRUKTURA TABELI PARTS - PODSUMOWANIE
-- ======================================
SELECT '=== STRUKTURA TABELI PARTS ===' as info;

SELECT
    COUNT(*) as "Liczba kolumn",
    COUNT(CASE WHEN is_nullable = 'NO' THEN 1 END) as "Kolumny NOT NULL",
    COUNT(CASE WHEN column_default IS NOT NULL THEN 1 END) as "Kolumny z wartością domyślną"
FROM information_schema.columns
WHERE table_name = 'parts';

-- Typy danych w tabeli
SELECT
    data_type as "Typ danych",
    COUNT(*) as "Liczba kolumn"
FROM information_schema.columns
WHERE table_name = 'parts'
GROUP BY data_type
ORDER BY COUNT(*) DESC;

-- 3. STATYSTYKI DANYCH
-- ======================================
SELECT '=== STATYSTYKI DANYCH W PARTS ===' as info;

SELECT
    COUNT(*) as "Wszystkie rekordy",
    COUNT(DISTINCT order_id) as "Unikalne zamówienia",
    COUNT(DISTINCT material) as "Unikalne materiały",
    COUNT(DISTINCT idx_code) as "Unikalne kody",
    MIN(created_at) as "Najstarszy rekord",
    MAX(created_at) as "Najnowszy rekord"
FROM parts;

-- 4. ANALIZA PLIKÓW I GRAFIK
-- ======================================
SELECT '=== ANALIZA PLIKÓW ===' as info;

SELECT
    'Ścieżki tekstowe' as "Typ",
    COUNT(CASE WHEN cad_2d_file IS NOT NULL THEN 1 END) as "CAD 2D",
    COUNT(CASE WHEN cad_3d_file IS NOT NULL THEN 1 END) as "CAD 3D",
    COUNT(CASE WHEN user_image_file IS NOT NULL THEN 1 END) as "Obrazy użytkownika",
    COUNT(CASE WHEN documentation_path IS NOT NULL THEN 1 END) as "Dokumentacja"
FROM parts
UNION ALL
SELECT
    'Dane binarne' as "Typ",
    COUNT(CASE WHEN cad_2d_binary IS NOT NULL THEN 1 END) as "CAD 2D",
    COUNT(CASE WHEN cad_3d_binary IS NOT NULL THEN 1 END) as "CAD 3D",
    COUNT(CASE WHEN user_image_binary IS NOT NULL THEN 1 END) as "Obrazy użytkownika",
    COUNT(CASE WHEN documentation_binary IS NOT NULL THEN 1 END) as "Dokumentacja"
FROM parts
UNION ALL
SELECT
    'Podglądy' as "Typ",
    COUNT(CASE WHEN thumbnail_100 IS NOT NULL THEN 1 END) as "Thumbnail 100px",
    COUNT(CASE WHEN preview_4k IS NOT NULL THEN 1 END) as "Preview 4K",
    0 as "—",
    0 as "—"
FROM parts;

-- 5. ANALIZA KOSZTÓW
-- ======================================
SELECT '=== ANALIZA KOSZTÓW ===' as info;

SELECT
    COUNT(*) as "Rekordy z kosztami",
    ROUND(AVG(material_cost), 2) as "Średni koszt materiału",
    ROUND(AVG(laser_cost), 2) as "Średni koszt cięcia",
    ROUND(AVG(bending_cost), 2) as "Średni koszt gięcia",
    ROUND(AVG(additional_costs), 2) as "Średnie koszty dodatkowe",
    ROUND(SUM(material_cost + laser_cost + bending_cost + additional_costs), 2) as "Suma wszystkich kosztów"
FROM parts
WHERE material_cost > 0 OR laser_cost > 0 OR bending_cost > 0 OR additional_costs > 0;

-- 6. SPRAWDZENIE INDEKSÓW
-- ======================================
SELECT '=== INDEKSY NA TABELI PARTS ===' as info;

SELECT
    COUNT(*) as "Liczba indeksów",
    pg_size_pretty(SUM(pg_relation_size((schemaname||'.'||indexname)::regclass))) as "Całkowity rozmiar indeksów"
FROM pg_indexes
WHERE tablename = 'parts';

-- Lista indeksów z wykorzystaniem
SELECT
    indexrelname as "Indeks",
    idx_scan as "Liczba użyć",
    CASE
        WHEN idx_scan = 0 THEN 'NIEUŻYWANY'
        WHEN idx_scan < 100 THEN 'RZADKO'
        WHEN idx_scan < 1000 THEN 'ŚREDNIO'
        ELSE 'CZĘSTO'
    END as "Częstotliwość użycia"
FROM pg_stat_user_indexes
WHERE relname = 'parts'
ORDER BY idx_scan DESC;

-- 7. SPRAWDZENIE WIDOKÓW
-- ======================================
SELECT '=== WIDOKI W BAZIE ===' as info;

SELECT
    viewname as "Widok",
    pg_size_pretty(pg_relation_size(viewname::regclass)) as "Rozmiar"
FROM pg_views
WHERE schemaname = 'public'
AND viewname LIKE '%parts%';

-- 8. SPRAWDZENIE TRIGGERÓW
-- ======================================
SELECT '=== TRIGGERY NA TABELI PARTS ===' as info;

SELECT
    tgname as "Trigger",
    tgtype as "Typ",
    proname as "Funkcja"
FROM pg_trigger t
JOIN pg_proc p ON t.tgfoid = p.oid
WHERE t.tgrelid = 'parts'::regclass
AND NOT tgisinternal;

-- 9. SPRAWDZENIE CONSTRAINTÓW
-- ======================================
SELECT '=== CONSTRAINTY NA TABELI PARTS ===' as info;

SELECT
    conname as "Constraint",
    contype as "Typ",
    CASE contype
        WHEN 'p' THEN 'PRIMARY KEY'
        WHEN 'f' THEN 'FOREIGN KEY'
        WHEN 'c' THEN 'CHECK'
        WHEN 'u' THEN 'UNIQUE'
        ELSE contype::text
    END as "Opis"
FROM pg_constraint
WHERE conrelid = 'parts'::regclass;

-- 10. SPRAWDZENIE BACKUPÓW
-- ======================================
SELECT '=== ISTNIEJĄCE BACKUPY ===' as info;

SELECT
    tablename as "Backup",
    pg_size_pretty(pg_total_relation_size('public.'||tablename)) as "Rozmiar",
    CASE
        WHEN tablename ~ '\d{4}_\d{2}_\d{2}$'
        THEN 'Data: ' || substring(tablename from '\d{4}_\d{2}_\d{2}$')
        ELSE 'Inny format'
    END as "Utworzony"
FROM pg_tables
WHERE schemaname = 'public'
AND (tablename LIKE 'parts_backup%' OR tablename LIKE '%_backup_%')
ORDER BY tablename DESC;

-- 11. PROBLEMY DO ROZWIĄZANIA
-- ======================================
SELECT '=== POTENCJALNE PROBLEMY ===' as info;

-- Sprawdź duplikaty idx_code
SELECT
    'Duplikaty idx_code' as "Problem",
    COUNT(*) as "Liczba"
FROM (
    SELECT idx_code
    FROM parts
    WHERE idx_code IS NOT NULL
    GROUP BY idx_code
    HAVING COUNT(*) > 1
) dup
UNION ALL
-- Sprawdź rekordy bez nazwy
SELECT
    'Rekordy bez nazwy' as "Problem",
    COUNT(*) as "Liczba"
FROM parts
WHERE name IS NULL OR name = ''
UNION ALL
-- Sprawdź rekordy z ujemnymi kosztami
SELECT
    'Ujemne koszty' as "Problem",
    COUNT(*) as "Liczba"
FROM parts
WHERE material_cost < 0 OR laser_cost < 0 OR bending_cost < 0 OR additional_costs < 0
UNION ALL
-- Sprawdź rekordy bez materiału ale z grubością
SELECT
    'Grubość bez materiału' as "Problem",
    COUNT(*) as "Liczba"
FROM parts
WHERE material IS NULL AND thickness_mm IS NOT NULL
UNION ALL
-- Sprawdź martwe krotki
SELECT
    'Martwe krotki (>10%)' as "Problem",
    n_dead_tup as "Liczba"
FROM pg_stat_user_tables
WHERE tablename = 'parts'
AND n_live_tup > 0
AND (100.0 * n_dead_tup / n_live_tup) > 10;

-- 12. REKOMENDACJE
-- ======================================
SELECT '=== REKOMENDACJE ===' as info;

WITH recommendations AS (
    SELECT 1 as ord, 'Uruchom VACUUM ANALYZE parts' as rekomendacja
    WHERE EXISTS (
        SELECT 1 FROM pg_stat_user_tables
        WHERE tablename = 'parts'
        AND n_dead_tup > 1000
    )
    UNION ALL
    SELECT 2, 'Rozważ usunięcie nieużywanych indeksów'
    WHERE EXISTS (
        SELECT 1 FROM pg_stat_user_indexes
        WHERE relname = 'parts' AND idx_scan = 0
    )
    UNION ALL
    SELECT 3, 'Rozważ kompresję danych binarnych'
    WHERE EXISTS (
        SELECT 1 FROM parts
        WHERE pg_column_size(thumbnail_100) + pg_column_size(preview_4k) > 1000000
    )
    UNION ALL
    SELECT 4, 'Usuń stare backupy (>30 dni)'
    WHERE EXISTS (
        SELECT 1 FROM pg_tables
        WHERE tablename LIKE 'parts_backup_%'
        AND tablename < 'parts_backup_' || to_char(CURRENT_DATE - INTERVAL '30 days', 'YYYY_MM_DD')
    )
    UNION ALL
    SELECT 5, 'Rozważ partycjonowanie tabeli'
    WHERE (SELECT COUNT(*) FROM parts) > 100000
)
SELECT rekomendacja as "Rekomendacja"
FROM recommendations
ORDER BY ord;

-- 13. PODSUMOWANIE KOŃCOWE
-- ======================================
SELECT '=== PODSUMOWANIE KOŃCOWE ===' as info;

SELECT
    'Tabela parts' as "Obiekt",
    pg_size_pretty(pg_total_relation_size('parts')) as "Rozmiar całkowity",
    pg_size_pretty(pg_table_size('parts')) as "Rozmiar danych",
    pg_size_pretty(pg_indexes_size('parts')) as "Rozmiar indeksów",
    (SELECT COUNT(*) FROM parts) as "Liczba rekordów",
    CASE
        WHEN (SELECT COUNT(*) FROM parts) > 0
        THEN pg_size_pretty((pg_total_relation_size('parts') / (SELECT COUNT(*) FROM parts))::bigint)
        ELSE '0'
    END as "Średni rozmiar rekordu";