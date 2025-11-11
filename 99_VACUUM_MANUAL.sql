-- =====================================================
-- SKRYPT VACUUM - URUCHOM PO GŁÓWNYCH OPERACJACH
-- =====================================================
-- Ten skrypt należy uruchomić OSOBNO po wykonaniu
-- skryptów czyszczenia bazy danych
--
-- VACUUM nie może być uruchomiony w transakcji,
-- dlatego musi być wykonany osobno
-- =====================================================

-- 1. VACUUM I ANALYZE DLA TABELI PARTS
-- ======================================
-- Odzyskuje miejsce po usuniętych rekordach
-- i aktualizuje statystyki dla optymalizatora

VACUUM (VERBOSE, ANALYZE) parts;

-- 2. VACUUM DLA INNYCH WAŻNYCH TABEL (jeśli istnieją)
-- ======================================

-- Jeśli masz tabelę products_catalog
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'products_catalog') THEN
        EXECUTE 'VACUUM ANALYZE products_catalog';
        RAISE NOTICE 'Wykonano VACUUM dla products_catalog';
    END IF;
END $$;

-- Jeśli masz tabelę orders
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'orders') THEN
        EXECUTE 'VACUUM ANALYZE orders';
        RAISE NOTICE 'Wykonano VACUUM dla orders';
    END IF;
END $$;

-- Jeśli masz tabelę order_items
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'order_items') THEN
        EXECUTE 'VACUUM ANALYZE order_items';
        RAISE NOTICE 'Wykonano VACUUM dla order_items';
    END IF;
END $$;

-- 3. POKAŻ STATYSTYKI PO VACUUM
-- ======================================
SELECT '=== STATYSTYKI PO VACUUM ===' as info;

SELECT
    schemaname,
    tablename,
    n_live_tup as "Żywe krotki",
    n_dead_tup as "Martwe krotki",
    CASE
        WHEN n_live_tup > 0
        THEN ROUND(100.0 * n_dead_tup / n_live_tup, 2)
        ELSE 0
    END as "% martwych",
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_dead_tup DESC;

-- 4. ROZMIARY TABEL PO VACUUM
-- ======================================
SELECT '=== ROZMIARY PO VACUUM ===' as info;

SELECT
    tablename as "Tabela",
    pg_size_pretty(pg_table_size(schemaname||'.'||tablename)) as "Rozmiar danych",
    pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as "Rozmiar indeksów",
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as "Rozmiar całkowity"
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;

-- 5. REKOMENDACJE
-- ======================================
SELECT '=== REKOMENDACJE ===' as info;

SELECT
    CASE
        WHEN n_dead_tup > 1000 AND (100.0 * n_dead_tup / NULLIF(n_live_tup, 0)) > 20
        THEN 'UWAGA: Tabela ' || tablename || ' nadal ma dużo martwych krotek. Rozważ VACUUM FULL.'
        WHEN last_vacuum IS NULL AND last_autovacuum IS NULL
        THEN 'INFO: Tabela ' || tablename || ' nigdy nie była vacuum-owana.'
        ELSE 'OK: Tabela ' || tablename || ' jest zoptymalizowana.'
    END as "Status"
FROM pg_stat_user_tables
WHERE schemaname = 'public'
AND (n_dead_tup > 100 OR last_vacuum IS NULL)
ORDER BY n_dead_tup DESC;