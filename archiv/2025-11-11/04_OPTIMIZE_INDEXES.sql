-- =====================================================
-- SKRYPT 4: OPTYMALIZACJA INDEKSÓW I WYDAJNOŚCI
-- =====================================================
-- Ten skrypt tworzy indeksy dla poprawy wydajności zapytań
-- Uruchom w Supabase SQL Editor
-- Wersja: 2.0 (Poprawiona dla PostgreSQL/Supabase)

-- 1. USUNIĘCIE STARYCH/ZDUPLIKOWANYCH INDEKSÓW
-- ======================================
-- Najpierw usuń potencjalnie zduplikowane indeksy

DROP INDEX IF EXISTS idx_parts_order_id;
DROP INDEX IF EXISTS idx_parts_material_id;
DROP INDEX IF EXISTS idx_parts_name;
DROP INDEX IF EXISTS idx_parts_idx_code;
DROP INDEX IF EXISTS idx_parts_created_at;
DROP INDEX IF EXISTS idx_parts_qty;
DROP INDEX IF EXISTS idx_parts_material;
DROP INDEX IF EXISTS idx_parts_thickness;
DROP INDEX IF EXISTS idx_parts_status;
DROP INDEX IF EXISTS idx_parts_category;
DROP INDEX IF EXISTS idx_parts_parent_version_id;

-- 2. INDEKSY DLA KLUCZY OBCYCH
-- ======================================
-- Przyspiesza JOIN-y między tabelami

CREATE INDEX IF NOT EXISTS idx_parts_order_id
    ON parts(order_id)
    WHERE order_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_parts_material_id
    ON parts(material_id)
    WHERE material_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_parts_parent_version_id
    ON parts(parent_version_id)
    WHERE parent_version_id IS NOT NULL;

-- 3. INDEKSY DLA WYSZUKIWANIA TEKSTOWEGO
-- ======================================
-- Przyspiesza wyszukiwanie po nazwach i kodach

-- Indeks dla wyszukiwania po nazwie (case-insensitive)
CREATE INDEX IF NOT EXISTS idx_parts_name_lower
    ON parts(LOWER(name));

-- Indeks dla wyszukiwania po kodzie
CREATE INDEX IF NOT EXISTS idx_parts_idx_code
    ON parts(idx_code)
    WHERE idx_code IS NOT NULL;

-- Indeks dla wyszukiwania pełnotekstowego
CREATE INDEX IF NOT EXISTS idx_parts_name_gin
    ON parts USING gin(to_tsvector('simple', name));

-- 4. INDEKSY DLA FILTROWANIA
-- ======================================
-- Przyspiesza filtrowanie po często używanych kolumnach

-- Indeks dla materiału
CREATE INDEX IF NOT EXISTS idx_parts_material
    ON parts(material)
    WHERE material IS NOT NULL;

-- Indeks dla grubości
CREATE INDEX IF NOT EXISTS idx_parts_thickness_mm
    ON parts(thickness_mm)
    WHERE thickness_mm IS NOT NULL;

-- Indeks dla statusu
CREATE INDEX IF NOT EXISTS idx_parts_status
    ON parts(status)
    WHERE status IS NOT NULL;

-- Indeks dla kategorii
CREATE INDEX IF NOT EXISTS idx_parts_category
    ON parts(category)
    WHERE category IS NOT NULL;

-- Indeks kompozytowy dla materiału i grubości
CREATE INDEX IF NOT EXISTS idx_parts_material_thickness
    ON parts(material, thickness_mm)
    WHERE material IS NOT NULL AND thickness_mm IS NOT NULL;

-- 5. INDEKSY DLA SORTOWANIA
-- ======================================
-- Przyspiesza sortowanie wyników

CREATE INDEX IF NOT EXISTS idx_parts_created_at_desc
    ON parts(created_at DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_parts_modified_at_desc
    ON parts(modified_at DESC NULLS LAST)
    WHERE modified_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_parts_priority_desc
    ON parts(priority DESC NULLS LAST)
    WHERE priority IS NOT NULL;

-- 6. INDEKSY DLA KOSZTÓW
-- ======================================
-- Przyspiesza obliczenia i sortowanie po kosztach

CREATE INDEX IF NOT EXISTS idx_parts_material_cost
    ON parts(material_cost)
    WHERE material_cost IS NOT NULL AND material_cost > 0;

CREATE INDEX IF NOT EXISTS idx_parts_total_cost
    ON parts((COALESCE(material_cost, 0) + COALESCE(laser_cost, 0) +
              COALESCE(bending_cost, 0) + COALESCE(additional_costs, 0)))
    WHERE material_cost IS NOT NULL OR laser_cost IS NOT NULL;

-- 7. INDEKSY DLA PLIKÓW BINARNYCH
-- ======================================
-- Przyspiesza sprawdzanie dostępności plików

CREATE INDEX IF NOT EXISTS idx_parts_has_thumbnail
    ON parts((thumbnail_100 IS NOT NULL))
    WHERE thumbnail_100 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_parts_has_preview
    ON parts((preview_4k IS NOT NULL))
    WHERE preview_4k IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_parts_has_binary_files
    ON parts((cad_2d_binary IS NOT NULL OR cad_3d_binary IS NOT NULL OR
              user_image_binary IS NOT NULL OR documentation_binary IS NOT NULL))
    WHERE cad_2d_binary IS NOT NULL OR cad_3d_binary IS NOT NULL OR
          user_image_binary IS NOT NULL OR documentation_binary IS NOT NULL;

-- 8. INDEKSY CZĘŚCIOWE DLA STATUSÓW
-- ======================================
-- Małe indeksy dla często używanych filtrów

CREATE INDEX IF NOT EXISTS idx_parts_draft
    ON parts(id)
    WHERE status = 'draft';

CREATE INDEX IF NOT EXISTS idx_parts_approved
    ON parts(id)
    WHERE status = 'approved';

CREATE INDEX IF NOT EXISTS idx_parts_production
    ON parts(id)
    WHERE status = 'production';

CREATE INDEX IF NOT EXISTS idx_parts_latest_version
    ON parts(id, version_number)
    WHERE is_latest_version = true;

-- 9. INDEKSY DLA TAGÓW (ARRAY)
-- ======================================
-- Jeśli używasz tagów jako array

DO $$
BEGIN
    -- Sprawdź czy kolumna tags istnieje
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'parts' AND column_name = 'tags'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_parts_tags_gin
        ON parts USING gin(tags)
        WHERE tags IS NOT NULL AND array_length(tags, 1) > 0;
    END IF;
END $$;

-- 10. INDEKSY DLA HISTORII ZMIAN (JSONB)
-- ======================================
CREATE INDEX IF NOT EXISTS idx_parts_change_history_gin
    ON parts USING gin(change_history)
    WHERE change_history IS NOT NULL AND change_history != '[]'::jsonb;

-- 11. INDEKSY DLA INNYCH TABEL (jeśli istnieją)
-- ======================================

-- Indeksy dla products_catalog
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'products_catalog') THEN
        -- Podstawowe indeksy
        CREATE INDEX IF NOT EXISTS idx_products_catalog_idx_code ON products_catalog(idx_code);
        CREATE INDEX IF NOT EXISTS idx_products_catalog_name_lower ON products_catalog(LOWER(name));
        CREATE INDEX IF NOT EXISTS idx_products_catalog_customer_id ON products_catalog(customer_id);
        CREATE INDEX IF NOT EXISTS idx_products_catalog_material_id ON products_catalog(material_id);
        CREATE INDEX IF NOT EXISTS idx_products_catalog_category ON products_catalog(category);
        RAISE NOTICE 'Utworzono indeksy dla products_catalog';
    END IF;
END $$;

-- Indeksy dla orders
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'orders') THEN
        CREATE INDEX IF NOT EXISTS idx_orders_process_no ON orders(process_no);
        CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
        CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
        RAISE NOTICE 'Utworzono indeksy dla orders';
    END IF;
END $$;

-- Indeksy dla order_items
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'order_items') THEN
        CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
        CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);
        CREATE INDEX IF NOT EXISTS idx_order_items_material_id ON order_items(material_id);
        RAISE NOTICE 'Utworzono indeksy dla order_items';
    END IF;
END $$;

-- 12. STATYSTYKI I OPTYMALIZACJA
-- ======================================
-- Aktualizuj statystyki dla optymalizatora zapytań

ANALYZE parts;

-- Ustaw parametry autovacuum dla tabeli (jeśli masz uprawnienia)
DO $$
BEGIN
    ALTER TABLE parts SET (
        autovacuum_vacuum_scale_factor = 0.1,
        autovacuum_analyze_scale_factor = 0.05
    );
    RAISE NOTICE 'Ustawiono parametry autovacuum dla parts';
EXCEPTION
    WHEN insufficient_privilege THEN
        RAISE NOTICE 'Brak uprawnień do zmiany parametrów autovacuum';
END $$;

-- 13. RAPORT Z INDEKSÓW - UTWORZONE
-- ======================================
SELECT '=== UTWORZONE INDEKSY NA TABELI PARTS ===' as info;

-- Lista wszystkich indeksów na tabeli parts z pg_indexes
SELECT
    indexname as "Nazwa indeksu",
    pg_size_pretty(pg_relation_size((schemaname||'.'||indexname)::regclass)) as "Rozmiar",
    indexdef as "Definicja (pierwsze 100 znaków)"
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename = 'parts'
ORDER BY indexname;

-- 14. RAPORT Z INDEKSÓW - WYKORZYSTANIE
-- ======================================
SELECT '=== WYKORZYSTANIE INDEKSÓW ===' as info;

-- Statystyki użycia indeksów z pg_stat_user_indexes
SELECT
    indexrelname as "Nazwa indeksu",
    pg_size_pretty(pg_relation_size(indexrelid)) as "Rozmiar",
    idx_scan as "Liczba skanów",
    idx_tup_read as "Odczytane krotki",
    idx_tup_fetch as "Pobrane krotki",
    CASE
        WHEN idx_scan = 0 THEN '❌ NIEUŻYWANY'
        WHEN idx_scan < 100 THEN '⚠️ RZADKO'
        WHEN idx_scan < 1000 THEN '✓ ŚREDNIO'
        ELSE '✅ CZĘSTO'
    END as "Status"
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
AND relname = 'parts'
ORDER BY idx_scan DESC;

-- 15. NIEUŻYWANE INDEKSY
-- ======================================
SELECT '=== NIEUŻYWANE INDEKSY (rozważ usunięcie) ===' as info;

SELECT
    indexrelname as "Nieużywany indeks",
    pg_size_pretty(pg_relation_size(indexrelid)) as "Rozmiar",
    'DROP INDEX IF EXISTS ' || indexrelname || ';' as "Komenda do usunięcia"
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
    AND relname = 'parts'
    AND idx_scan = 0
    AND indexrelname != 'parts_pkey'
    AND indexrelname NOT LIKE '%_pkey'
    AND indexrelname NOT LIKE '%_fkey';

-- 16. NAJWIĘKSZE INDEKSY
-- ======================================
SELECT '=== TOP 10 NAJWIĘKSZYCH INDEKSÓW ===' as info;

SELECT
    indexname as "Indeks",
    tablename as "Tabela",
    pg_size_pretty(pg_relation_size((schemaname||'.'||indexname)::regclass)) as "Rozmiar"
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size((schemaname||'.'||indexname)::regclass) DESC
LIMIT 10;

-- 17. STATYSTYKI TABELI
-- ======================================
SELECT '=== STATYSTYKI TABELI PARTS ===' as info;

SELECT
    n_tup_ins as "Wstawienia",
    n_tup_upd as "Aktualizacje",
    n_tup_del as "Usunięcia",
    n_live_tup as "Żywe krotki",
    n_dead_tup as "Martwe krotki",
    CASE
        WHEN n_live_tup > 0
        THEN ROUND(100.0 * n_dead_tup / n_live_tup, 2)
        ELSE 0
    END as "% martwych krotek",
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public'
AND relname = 'parts';

-- 18. PODSUMOWANIE
-- ======================================
SELECT '=== PODSUMOWANIE OPTYMALIZACJI ===' as info;

WITH index_stats AS (
    SELECT
        COUNT(*) as total_indexes,
        COUNT(CASE WHEN idx_scan = 0 THEN 1 END) as unused_indexes,
        SUM(pg_relation_size(indexrelid)) as total_size
    FROM pg_stat_user_indexes
    WHERE schemaname = 'public' AND relname = 'parts'
),
table_stats AS (
    SELECT
        pg_relation_size('parts') as table_size,
        pg_total_relation_size('parts') as total_size
    FROM pg_stat_user_tables
    WHERE schemaname = 'public' AND relname = 'parts'
)
SELECT
    i.total_indexes as "Liczba indeksów",
    i.unused_indexes as "Nieużywane indeksy",
    pg_size_pretty(i.total_size) as "Rozmiar indeksów",
    pg_size_pretty(t.table_size) as "Rozmiar tabeli",
    pg_size_pretty(t.total_size) as "Rozmiar całkowity",
    ROUND(100.0 * i.total_size / NULLIF(t.table_size, 0), 2) as "% indeksy/dane"
FROM index_stats i, table_stats t;

-- 19. REKOMENDACJE
-- ======================================
SELECT '=== REKOMENDACJE ===' as info;

SELECT
    CASE
        WHEN n_dead_tup > 1000 AND (100.0 * n_dead_tup / NULLIF(n_live_tup, 0)) > 20
        THEN '⚠️ Uruchom VACUUM ANALYZE parts - dużo martwych krotek'
        WHEN last_vacuum IS NULL AND last_autovacuum IS NULL
        THEN '⚠️ Tabela nigdy nie była vacuum-owana'
        WHEN last_analyze IS NULL AND last_autoanalyze IS NULL
        THEN '⚠️ Tabela nigdy nie była analizowana'
        WHEN (SELECT COUNT(*) FROM pg_stat_user_indexes WHERE schemaname = 'public' AND relname = 'parts' AND idx_scan = 0) > 3
        THEN '⚠️ Masz ' || (SELECT COUNT(*) FROM pg_stat_user_indexes WHERE schemaname = 'public' AND relname = 'parts' AND idx_scan = 0)::text || ' nieużywanych indeksów - rozważ usunięcie'
        ELSE '✅ Tabela jest dobrze zoptymalizowana'
    END as "Status i rekomendacje"
FROM pg_stat_user_tables
WHERE schemaname = 'public' AND relname = 'parts';

-- KONIEC SKRYPTU
-- ======================================
-- Po wykonaniu tego skryptu:
-- 1. Sprawdź raporty powyżej
-- 2. Usuń nieużywane indeksy (jeśli są)
-- 3. Uruchom VACUUM ANALYZE parts (osobno, poza transakcją)
-- 4. Monitoruj wykorzystanie indeksów w czasie