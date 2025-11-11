-- =====================================================
-- SKRYPT SPRAWDZAJĄCY POPRAWNOŚĆ BAZY DANYCH
-- =====================================================
-- Ten skrypt wykonuje kompleksową walidację struktury i danych
-- Uruchom w Supabase SQL Editor
-- Wersja: 1.0

-- =====================================================
-- SEKCJA 1: INFORMACJE OGÓLNE
-- =====================================================

SELECT '========================================' as separator;
SELECT '1. INFORMACJE O BAZIE DANYCH' as section;
SELECT '========================================' as separator;

SELECT
    current_database() as "Nazwa bazy",
    version() as "Wersja PostgreSQL",
    pg_database_size(current_database())::bigint as "Rozmiar (bajty)",
    pg_size_pretty(pg_database_size(current_database())) as "Rozmiar",
    current_user as "Użytkownik",
    inet_server_addr() as "Adres serwera",
    current_timestamp as "Data sprawdzenia";

-- =====================================================
-- SEKCJA 2: SPRAWDZENIE TABEL
-- =====================================================

SELECT '========================================' as separator;
SELECT '2. STRUKTURA TABEL' as section;
SELECT '========================================' as separator;

-- Lista wszystkich tabel z informacjami
WITH table_info AS (
    SELECT
        t.tablename,
        COUNT(c.column_name) as column_count,
        pg_size_pretty(pg_total_relation_size(t.schemaname||'.'||t.tablename)) as size,
        obj_description((t.schemaname||'.'||t.tablename)::regclass, 'pg_class') as comment
    FROM pg_tables t
    LEFT JOIN information_schema.columns c
        ON c.table_schema = t.schemaname
        AND c.table_name = t.tablename
    WHERE t.schemaname = 'public'
    GROUP BY t.tablename, t.schemaname
)
SELECT
    tablename as "Tabela",
    column_count as "Liczba kolumn",
    size as "Rozmiar",
    CASE
        WHEN tablename IN ('parts', 'orders', 'order_items', 'customers', 'products_catalog')
        THEN '✅ Główna'
        WHEN tablename LIKE '%_backup%' THEN '📦 Backup'
        WHEN tablename LIKE '%_dict' THEN '📖 Słownik'
        ELSE '📋 Pomocnicza'
    END as "Typ"
FROM table_info
ORDER BY
    CASE
        WHEN tablename IN ('parts', 'orders', 'order_items', 'customers', 'products_catalog') THEN 1
        WHEN tablename LIKE '%_dict' THEN 2
        WHEN tablename LIKE '%_backup%' THEN 4
        ELSE 3
    END,
    tablename;

-- =====================================================
-- SEKCJA 3: SPRAWDZENIE TYPÓW ENUM
-- =====================================================

SELECT '========================================' as separator;
SELECT '3. TYPY ENUM' as section;
SELECT '========================================' as separator;

SELECT
    t.typname as "Typ",
    array_agg(e.enumlabel ORDER BY e.enumsortorder) as "Wartości",
    COUNT(e.enumlabel) as "Liczba wartości",
    CASE
        WHEN t.typname = 'order_status' THEN '✅ Wymagany'
        ELSE '📋 Opcjonalny'
    END as "Status"
FROM pg_type t
JOIN pg_enum e ON t.oid = e.enumtypid
WHERE t.typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
GROUP BY t.typname;

-- =====================================================
-- SEKCJA 4: SPRAWDZENIE KLUCZY GŁÓWNYCH
-- =====================================================

SELECT '========================================' as separator;
SELECT '4. KLUCZE GŁÓWNE' as section;
SELECT '========================================' as separator;

SELECT
    tc.table_name as "Tabela",
    kcu.column_name as "Kolumna PK",
    col.data_type as "Typ danych",
    CASE
        WHEN col.column_default LIKE '%gen_random_uuid%' THEN '✅ UUID auto'
        WHEN col.column_default IS NOT NULL THEN '✅ Ma domyślną'
        ELSE '⚠️ Brak domyślnej'
    END as "Status"
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.columns col
    ON col.table_name = tc.table_name
    AND col.column_name = kcu.column_name
WHERE tc.constraint_type = 'PRIMARY KEY'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name;

-- =====================================================
-- SEKCJA 5: SPRAWDZENIE KLUCZY OBCYCH
-- =====================================================

SELECT '========================================' as separator;
SELECT '5. KLUCZE OBCE' as section;
SELECT '========================================' as separator;

WITH foreign_keys AS (
    SELECT
        tc.table_name,
        kcu.column_name,
        ccu.table_name AS foreign_table,
        ccu.column_name AS foreign_column,
        tc.constraint_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public'
)
SELECT
    table_name as "Tabela",
    column_name as "Kolumna",
    foreign_table || '(' || foreign_column || ')' as "Referencja",
    CASE
        WHEN constraint_name LIKE '%fkey' THEN '✅ Poprawna nazwa'
        ELSE '⚠️ Niestandardowa nazwa'
    END as "Status"
FROM foreign_keys
ORDER BY table_name, column_name;

-- =====================================================
-- SEKCJA 6: SPRAWDZENIE INDEKSÓW
-- =====================================================

SELECT '========================================' as separator;
SELECT '6. INDEKSY' as section;
SELECT '========================================' as separator;

WITH index_usage AS (
    SELECT
        schemaname,
        relname as tablename,
        indexrelname,
        idx_scan,
        pg_size_pretty(pg_relation_size(indexrelid)) as index_size
    FROM pg_stat_user_indexes
    WHERE schemaname = 'public'
)
SELECT
    tablename as "Tabela",
    COUNT(*) as "Liczba indeksów",
    COUNT(CASE WHEN idx_scan = 0 THEN 1 END) as "Nieużywane",
    COUNT(CASE WHEN idx_scan > 0 THEN 1 END) as "Używane",
    STRING_AGG(index_size, ', ') as "Rozmiary",
    CASE
        WHEN COUNT(CASE WHEN idx_scan = 0 THEN 1 END) = 0 THEN '✅ Wszystkie używane'
        WHEN COUNT(CASE WHEN idx_scan = 0 THEN 1 END) <= 2 THEN '⚠️ Niektóre nieużywane'
        ELSE '❌ Dużo nieużywanych'
    END as "Status"
FROM index_usage
GROUP BY tablename
ORDER BY tablename;

-- =====================================================
-- SEKCJA 7: SPRAWDZENIE CONSTRAINTS
-- =====================================================

SELECT '========================================' as separator;
SELECT '7. CHECK CONSTRAINTS' as section;
SELECT '========================================' as separator;

SELECT
    tc.table_name as "Tabela",
    tc.constraint_name as "Constraint",
    cc.check_clause as "Warunek",
    CASE
        WHEN cc.check_clause LIKE '%email%' AND cc.check_clause LIKE '%~%' THEN '✅ Email regex'
        WHEN cc.check_clause LIKE '%>=%' THEN '✅ Wartość min'
        WHEN cc.check_clause LIKE '%ANY%ARRAY%' THEN '✅ Enum check'
        ELSE '📋 Inny'
    END as "Typ"
FROM information_schema.table_constraints tc
JOIN information_schema.check_constraints cc
    ON tc.constraint_name = cc.constraint_name
WHERE tc.constraint_type = 'CHECK'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name, tc.constraint_name;

-- =====================================================
-- SEKCJA 8: SPRAWDZENIE TRIGGERÓW
-- =====================================================

SELECT '========================================' as separator;
SELECT '8. TRIGGERY' as section;
SELECT '========================================' as separator;

SELECT
    c.relname as "Tabela",
    t.tgname as "Trigger",
    p.proname as "Funkcja",
    CASE t.tgtype
        WHEN 17 THEN 'BEFORE UPDATE'
        WHEN 19 THEN 'BEFORE INSERT/UPDATE'
        WHEN 23 THEN 'BEFORE INSERT/UPDATE/DELETE'
        ELSE 'INNY (' || t.tgtype || ')'
    END as "Zdarzenie",
    CASE
        WHEN t.tgname LIKE '%updated_at%' THEN '✅ Timestamp'
        WHEN t.tgname LIKE '%modified%' THEN '✅ Audit'
        ELSE '📋 Inny'
    END as "Typ"
FROM pg_trigger t
JOIN pg_proc p ON t.tgfoid = p.oid
JOIN pg_class c ON t.tgrelid = c.oid
JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE n.nspname = 'public'
    AND NOT t.tgisinternal
ORDER BY c.relname, t.tgname;

-- =====================================================
-- SEKCJA 9: SPRAWDZENIE WIDOKÓW
-- =====================================================

SELECT '========================================' as separator;
SELECT '9. WIDOKI' as section;
SELECT '========================================' as separator;

SELECT
    viewname as "Widok",
    CASE
        WHEN definition LIKE '%parts%' THEN 'Parts'
        WHEN definition LIKE '%order%' THEN 'Orders'
        WHEN definition LIKE '%product%' THEN 'Products'
        ELSE 'Inny'
    END as "Obszar",
    CASE
        WHEN viewname LIKE '%_full' THEN '✅ Widok pełny'
        WHEN viewname LIKE '%_with_%' THEN '✅ Widok rozszerzony'
        WHEN viewname LIKE '%_history' THEN '📊 Historia'
        ELSE '📋 Standardowy'
    END as "Typ"
FROM pg_views
WHERE schemaname = 'public'
ORDER BY viewname;

-- =====================================================
-- SEKCJA 10: SPRAWDZENIE DANYCH - INTEGRALNOŚĆ
-- =====================================================

SELECT '========================================' as separator;
SELECT '10. INTEGRALNOŚĆ DANYCH' as section;
SELECT '========================================' as separator;

-- Sprawdzenie osierocoonych rekordów
WITH orphan_checks AS (
    -- Parts bez order_id
    SELECT
        'parts bez zamówienia' as check_type,
        COUNT(*) as count
    FROM parts
    WHERE order_id IS NULL

    UNION ALL

    -- Order_items bez istniejącego order_id
    SELECT
        'order_items z nieistniejącym order_id',
        COUNT(*)
    FROM order_items oi
    WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.id = oi.order_id)

    UNION ALL

    -- Orders bez customer_id
    SELECT
        'orders bez klienta',
        COUNT(*)
    FROM orders
    WHERE customer_id IS NULL

    UNION ALL

    -- Parts z nieprawidłowym material_id
    SELECT
        'parts z nieprawidłowym material_id',
        COUNT(*)
    FROM parts p
    WHERE p.material_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM materials_dict m WHERE m.id = p.material_id)
)
SELECT
    check_type as "Test",
    count as "Liczba problemów",
    CASE
        WHEN count = 0 THEN '✅ OK'
        WHEN count <= 5 THEN '⚠️ Niewiele'
        ELSE '❌ Dużo problemów'
    END as "Status"
FROM orphan_checks
ORDER BY count DESC;

-- =====================================================
-- SEKCJA 11: SPRAWDZENIE DANYCH - WARTOŚCI
-- =====================================================

SELECT '========================================' as separator;
SELECT '11. POPRAWNOŚĆ WARTOŚCI' as section;
SELECT '========================================' as separator;

WITH data_checks AS (
    -- Sprawdzenie ujemnych wartości
    SELECT
        'parts z ujemnymi kosztami' as check_type,
        COUNT(*) as count
    FROM parts
    WHERE material_cost < 0 OR laser_cost < 0 OR bending_cost < 0 OR additional_costs < 0

    UNION ALL

    -- Sprawdzenie dat
    SELECT
        'orders z datą finished < received',
        COUNT(*)
    FROM orders
    WHERE finished_at < received_at

    UNION ALL

    -- Sprawdzenie ilości
    SELECT
        'parts/order_items z qty <= 0',
        COUNT(*)
    FROM (
        SELECT qty FROM parts WHERE qty <= 0
        UNION ALL
        SELECT qty FROM order_items WHERE qty <= 0
    ) t

    UNION ALL

    -- Sprawdzenie duplikatów process_no
    SELECT
        'duplikaty process_no',
        COUNT(*) - COUNT(DISTINCT process_no)
    FROM orders
    WHERE process_no IS NOT NULL

    UNION ALL

    -- Sprawdzenie emaili
    SELECT
        'niepoprawne emaile',
        COUNT(*)
    FROM customers
    WHERE email IS NOT NULL
    AND email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
)
SELECT
    check_type as "Test",
    count as "Liczba problemów",
    CASE
        WHEN count = 0 THEN '✅ OK'
        WHEN count <= 5 THEN '⚠️ Niewiele'
        ELSE '❌ Dużo problemów'
    END as "Status"
FROM data_checks
ORDER BY count DESC;

-- =====================================================
-- SEKCJA 12: SPRAWDZENIE WYDAJNOŚCI
-- =====================================================

SELECT '========================================' as separator;
SELECT '12. WYDAJNOŚĆ' as section;
SELECT '========================================' as separator;

-- Statystyki tabel
SELECT
    relname as "Tabela",
    n_live_tup as "Żywe wiersze",
    n_dead_tup as "Martwe wiersze",
    CASE
        WHEN n_live_tup > 0 THEN ROUND(100.0 * n_dead_tup / n_live_tup, 2)
        ELSE 0
    END as "% martwych",
    last_vacuum as "Ostatni vacuum",
    last_analyze as "Ostatni analyze",
    CASE
        WHEN n_dead_tup > 1000 AND (100.0 * n_dead_tup / NULLIF(n_live_tup, 0)) > 20 THEN '❌ Potrzebny VACUUM'
        WHEN last_vacuum IS NULL THEN '⚠️ Nigdy nie vacuum'
        ELSE '✅ OK'
    END as "Status"
FROM pg_stat_user_tables
WHERE schemaname = 'public'
    AND relname IN ('parts', 'orders', 'order_items', 'customers', 'products_catalog')
ORDER BY n_dead_tup DESC;

-- =====================================================
-- SEKCJA 13: SPRAWDZENIE FUNKCJI
-- =====================================================

SELECT '========================================' as separator;
SELECT '13. FUNKCJE' as section;
SELECT '========================================' as separator;

SELECT
    proname as "Funkcja",
    pronargs as "Liczba arg",
    pg_get_function_result(oid) as "Zwraca",
    CASE
        WHEN proname LIKE '%generate%number%' THEN '✅ Generator'
        WHEN proname LIKE '%update%' THEN '✅ Trigger'
        WHEN proname LIKE '%calculate%' THEN '✅ Obliczenia'
        ELSE '📋 Inna'
    END as "Typ"
FROM pg_proc
WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
ORDER BY proname;

-- =====================================================
-- SEKCJA 14: SPRAWDZENIE KOLUMN BINARNYCH
-- =====================================================

SELECT '========================================' as separator;
SELECT '14. PLIKI BINARNE' as section;
SELECT '========================================' as separator;

-- Analiza plików binarnych w parts
SELECT
    'parts' as "Tabela",
    COUNT(*) as "Wszystkie rekordy",
    COUNT(CASE WHEN thumbnail_100 IS NOT NULL THEN 1 END) as "Z thumbnail",
    COUNT(CASE WHEN preview_4k IS NOT NULL THEN 1 END) as "Z preview",
    COUNT(CASE WHEN cad_2d_binary IS NOT NULL THEN 1 END) as "Z CAD 2D bin",
    COUNT(CASE WHEN cad_3d_binary IS NOT NULL THEN 1 END) as "Z CAD 3D bin",
    pg_size_pretty(
        COALESCE(SUM(pg_column_size(thumbnail_100)), 0) +
        COALESCE(SUM(pg_column_size(preview_4k)), 0) +
        COALESCE(SUM(pg_column_size(cad_2d_binary)), 0) +
        COALESCE(SUM(pg_column_size(cad_3d_binary)), 0)
    ) as "Rozmiar binarny"
FROM parts

UNION ALL

-- Analiza plików binarnych w products_catalog
SELECT
    'products_catalog',
    COUNT(*),
    COUNT(CASE WHEN thumbnail_100 IS NOT NULL THEN 1 END),
    COUNT(CASE WHEN preview_4k IS NOT NULL THEN 1 END),
    0,
    0,
    pg_size_pretty(
        COALESCE(SUM(pg_column_size(thumbnail_100)), 0) +
        COALESCE(SUM(pg_column_size(preview_4k)), 0)
    )
FROM products_catalog;

-- =====================================================
-- SEKCJA 15: PODSUMOWANIE PROBLEMÓW
-- =====================================================

SELECT '========================================' as separator;
SELECT '15. PODSUMOWANIE PROBLEMÓW' as section;
SELECT '========================================' as separator;

WITH problem_summary AS (
    -- Brakujące typy enum
    SELECT
        'Brakujący typ order_status' as problem,
        'KRYTYCZNY' as severity,
        NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'order_status') as exists

    UNION ALL

    -- Brakujące klucze główne
    SELECT
        'Tabele bez PK',
        'KRYTYCZNY',
        EXISTS (
            SELECT 1 FROM pg_tables t
            WHERE schemaname = 'public'
            AND NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints tc
                WHERE tc.table_name = t.tablename
                AND tc.constraint_type = 'PRIMARY KEY'
            )
        )

    UNION ALL

    -- Nieużywane indeksy
    SELECT
        'Więcej niż 10 nieużywanych indeksów',
        'ŚREDNI',
        (SELECT COUNT(*) FROM pg_stat_user_indexes
         WHERE schemaname = 'public' AND idx_scan = 0) > 10

    UNION ALL

    -- Dużo martwych krotek
    SELECT
        'Tabele z >20% martwych krotek',
        'ŚREDNI',
        EXISTS (
            SELECT 1 FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            AND n_live_tup > 0
            AND (100.0 * n_dead_tup / n_live_tup) > 20
        )

    UNION ALL

    -- Brak vacuum
    SELECT
        'Tabele nigdy nie vacuum',
        'NISKI',
        EXISTS (
            SELECT 1 FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            AND last_vacuum IS NULL
            AND last_autovacuum IS NULL
        )
)
SELECT
    problem as "Problem",
    severity as "Priorytet",
    CASE
        WHEN exists THEN '❌ WYSTĘPUJE'
        ELSE '✅ NIE WYSTĘPUJE'
    END as "Status"
FROM problem_summary
WHERE exists = true
ORDER BY
    CASE severity
        WHEN 'KRYTYCZNY' THEN 1
        WHEN 'ŚREDNI' THEN 2
        ELSE 3
    END;

-- =====================================================
-- SEKCJA 16: REKOMENDACJE
-- =====================================================

SELECT '========================================' as separator;
SELECT '16. REKOMENDACJE' as section;
SELECT '========================================' as separator;

WITH recommendations AS (
    -- Vacuum
    SELECT
        1 as priority,
        'Uruchom VACUUM ANALYZE' as action,
        'Tabele: ' || string_agg(relname, ', ') as details
    FROM pg_stat_user_tables
    WHERE schemaname = 'public'
    AND (n_dead_tup > 1000 OR last_vacuum IS NULL)
    GROUP BY 1, 2
    HAVING COUNT(*) > 0

    UNION ALL

    -- Nieużywane indeksy
    SELECT
        2,
        'Usuń nieużywane indeksy',
        'Liczba: ' || COUNT(*)::text
    FROM pg_stat_user_indexes
    WHERE schemaname = 'public' AND idx_scan = 0
    GROUP BY 1, 2
    HAVING COUNT(*) > 5

    UNION ALL

    -- Brakujące indeksy FK
    SELECT
        3,
        'Dodaj indeksy dla kluczy obcych',
        'Sprawdź kolumny FK bez indeksów'
    WHERE EXISTS (
        SELECT 1
        FROM information_schema.key_column_usage kcu
        WHERE kcu.constraint_name LIKE '%fkey'
        AND NOT EXISTS (
            SELECT 1 FROM pg_indexes i
            WHERE i.tablename = kcu.table_name
            AND i.indexdef LIKE '%' || kcu.column_name || '%'
        )
    )
)
SELECT
    priority as "Priorytet",
    action as "Akcja",
    details as "Szczegóły"
FROM recommendations
ORDER BY priority;

-- =====================================================
-- KOŃCOWY STATUS
-- =====================================================

SELECT '========================================' as separator;
SELECT 'STATUS KOŃCOWY' as section;
SELECT '========================================' as separator;

WITH problem_summary_final AS (
    -- Brakujące typy enum
    SELECT
        'Brakujący typ order_status' as problem,
        'KRYTYCZNY' as severity,
        NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'order_status') as exists

    UNION ALL

    -- Brakujące klucze główne
    SELECT
        'Tabele bez PK',
        'KRYTYCZNY',
        EXISTS (
            SELECT 1 FROM pg_tables t
            WHERE schemaname = 'public'
            AND NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints tc
                WHERE tc.table_name = t.tablename
                AND tc.constraint_type = 'PRIMARY KEY'
            )
        )

    UNION ALL

    -- Nieużywane indeksy
    SELECT
        'Więcej niż 10 nieużywanych indeksów',
        'ŚREDNI',
        (SELECT COUNT(*) FROM pg_stat_user_indexes
         WHERE schemaname = 'public' AND idx_scan = 0) > 10

    UNION ALL

    -- Dużo martwych krotek
    SELECT
        'Tabele z >20% martwych krotek',
        'ŚREDNI',
        EXISTS (
            SELECT 1 FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            AND n_live_tup > 0
            AND (100.0 * n_dead_tup / n_live_tup) > 20
        )

    UNION ALL

    -- Brak vacuum
    SELECT
        'Tabele nigdy nie vacuum',
        'NISKI',
        EXISTS (
            SELECT 1 FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            AND last_vacuum IS NULL
            AND last_autovacuum IS NULL
        )
)
SELECT
    CASE
        WHEN (SELECT COUNT(*) FROM problem_summary_final WHERE exists = true AND severity = 'KRYTYCZNY') > 0
        THEN '❌ KRYTYCZNE PROBLEMY - napraw natychmiast!'
        WHEN (SELECT COUNT(*) FROM problem_summary_final WHERE exists = true AND severity = 'ŚREDNI') > 0
        THEN '⚠️ PROBLEMY ŚREDNIE - napraw wkrótce'
        WHEN (SELECT COUNT(*) FROM problem_summary_final WHERE exists = true) > 0
        THEN '📋 DROBNE PROBLEMY - do optymalizacji'
        ELSE '✅ BAZA DANYCH W DOBRYM STANIE'
    END as "Status bazy danych",
    current_timestamp as "Sprawdzono";

-- KONIEC SKRYPTU