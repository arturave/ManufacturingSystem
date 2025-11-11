-- =====================================================
-- SKRYPT 2: CZYSZCZENIE I OPTYMALIZACJA BAZY DANYCH (POPRAWIONY)
-- =====================================================
-- UWAGA! Ten skrypt czyści lokalne ścieżki i optymalizuje strukturę
-- Wykonaj backup przed uruchomieniem!
-- Uruchom w Supabase SQL Editor

-- 1. BACKUP TABELI PARTS
-- ======================================
-- Tworzenie kopii zapasowej z datą
DO $$
BEGIN
    -- Sprawdź czy backup już istnieje
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'parts_backup_' || to_char(CURRENT_DATE, 'YYYY_MM_DD')
    ) THEN
        EXECUTE 'CREATE TABLE parts_backup_' || to_char(CURRENT_DATE, 'YYYY_MM_DD') ||
                ' AS SELECT * FROM parts';
        RAISE NOTICE 'Backup utworzony: parts_backup_%', to_char(CURRENT_DATE, 'YYYY_MM_DD');
    ELSE
        RAISE NOTICE 'Backup już istnieje: parts_backup_%', to_char(CURRENT_DATE, 'YYYY_MM_DD');
    END IF;
END $$;

-- 2. CZYSZCZENIE LOKALNYCH ŚCIEŻEK WINDOWS
-- ======================================
-- Usuwa lokalne ścieżki do plików (C:\, D:\, etc.)

DO $$
DECLARE
    rows_updated INTEGER;
BEGIN
    UPDATE parts
    SET
        cad_2d_file = NULL,
        cad_3d_file = NULL,
        user_image_file = NULL,
        graphic_high_res = NULL,
        graphic_low_res = NULL,
        documentation_path = NULL
    WHERE
        -- Ścieżki Windows z backslash
        (cad_2d_file IS NOT NULL AND cad_2d_file ~ '^[A-Za-z]:\\')
        OR (cad_3d_file IS NOT NULL AND cad_3d_file ~ '^[A-Za-z]:\\')
        OR (user_image_file IS NOT NULL AND user_image_file ~ '^[A-Za-z]:\\')
        OR (graphic_high_res IS NOT NULL AND graphic_high_res ~ '^[A-Za-z]:\\')
        OR (graphic_low_res IS NOT NULL AND graphic_low_res ~ '^[A-Za-z]:\\')
        OR (documentation_path IS NOT NULL AND documentation_path ~ '^[A-Za-z]:\\')
        -- Ścieżki Windows ze slash
        OR (cad_2d_file IS NOT NULL AND cad_2d_file ~ '^[A-Za-z]:/')
        OR (cad_3d_file IS NOT NULL AND cad_3d_file ~ '^[A-Za-z]:/')
        OR (user_image_file IS NOT NULL AND user_image_file ~ '^[A-Za-z]:/')
        OR (graphic_high_res IS NOT NULL AND graphic_high_res ~ '^[A-Za-z]:/')
        OR (graphic_low_res IS NOT NULL AND graphic_low_res ~ '^[A-Za-z]:/')
        OR (documentation_path IS NOT NULL AND documentation_path ~ '^[A-Za-z]:/');

    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    RAISE NOTICE 'Wyczyszczono lokalne ścieżki w % rekordach', rows_updated;
END $$;

-- 3. CZYSZCZENIE STARYCH TABEL BACKUP
-- ======================================
-- Usuwa stare backupy (starsze niż 30 dni)

DO $$
DECLARE
    backup_table RECORD;
    days_to_keep INTEGER := 30;
BEGIN
    FOR backup_table IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename LIKE 'parts_backup_%'
        AND tablename < 'parts_backup_' || to_char(CURRENT_DATE - INTERVAL '30 days', 'YYYY_MM_DD')
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || backup_table.tablename || ' CASCADE';
        RAISE NOTICE 'Usunięto stary backup: %', backup_table.tablename;
    END LOOP;
END $$;

-- Usuń inne stare backupy
DROP TABLE IF EXISTS customers_backup CASCADE;
DROP TABLE IF EXISTS files_backup_2025 CASCADE;
DROP TABLE IF EXISTS attachments_backup_2025 CASCADE;

-- 4. USUNIĘCIE ZBĘDNYCH TABEL (jeśli istnieją)
-- ======================================
DO $$
DECLARE
    row_count INTEGER;
BEGIN
    -- Sprawdź tabelę files
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'files') THEN
        SELECT COUNT(*) INTO row_count FROM files;
        IF row_count = 0 THEN
            DROP TABLE files CASCADE;
            RAISE NOTICE 'Usunięto pustą tabelę: files';
        ELSE
            RAISE NOTICE 'Tabela files zawiera % rekordów - nie usunięto', row_count;
        END IF;
    END IF;

    -- Sprawdź tabelę attachments
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'attachments') THEN
        SELECT COUNT(*) INTO row_count FROM attachments;
        IF row_count = 0 THEN
            DROP TABLE attachments CASCADE;
            RAISE NOTICE 'Usunięto pustą tabelę: attachments';
        ELSE
            RAISE NOTICE 'Tabela attachments zawiera % rekordów - nie usunięto', row_count;
        END IF;
    END IF;
END $$;

-- 5. NORMALIZACJA WARTOŚCI NULL I DOMYŚLNYCH
-- ======================================
DO $$
DECLARE
    rows_updated INTEGER;
    total_updated INTEGER := 0;
BEGIN
    -- Ustaw domyślne wartości dla pól liczbowych
    UPDATE parts SET material_laser_cost = 0.00 WHERE material_laser_cost IS NULL;
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    total_updated := total_updated + rows_updated;

    UPDATE parts SET bending_cost = 0.00 WHERE bending_cost IS NULL;
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    total_updated := total_updated + rows_updated;

    UPDATE parts SET additional_costs = 0.00 WHERE additional_costs IS NULL;
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    total_updated := total_updated + rows_updated;

    UPDATE parts SET duplicate_number = 0 WHERE duplicate_number IS NULL;
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    total_updated := total_updated + rows_updated;

    UPDATE parts SET qty = 1 WHERE qty IS NULL OR qty = 0;
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    total_updated := total_updated + rows_updated;

    RAISE NOTICE 'Znormalizowano wartości domyślne w % rekordach', total_updated;
END $$;

-- 6. CZYSZCZENIE PUSTYCH REKORDÓW
-- ======================================
DO $$
DECLARE
    rows_deleted INTEGER;
BEGIN
    DELETE FROM parts WHERE name IS NULL OR name = '';
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    IF rows_deleted > 0 THEN
        RAISE NOTICE 'Usunięto % pustych rekordów', rows_deleted;
    ELSE
        RAISE NOTICE 'Brak pustych rekordów do usunięcia';
    END IF;
END $$;

-- 7. OPTYMALIZACJA TYPÓW KOLUMN
-- ======================================
DO $$
BEGIN
    -- Sprawdź typ thumbnail_100
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'parts'
        AND column_name = 'thumbnail_100'
        AND data_type != 'bytea'
    ) THEN
        ALTER TABLE parts ALTER COLUMN thumbnail_100 TYPE bytea USING NULL;
        RAISE NOTICE 'Zmieniono typ kolumny thumbnail_100 na bytea';
    END IF;

    -- Sprawdź typ preview_4k
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'parts'
        AND column_name = 'preview_4k'
        AND data_type != 'bytea'
    ) THEN
        ALTER TABLE parts ALTER COLUMN preview_4k TYPE bytea USING NULL;
        RAISE NOTICE 'Zmieniono typ kolumny preview_4k na bytea';
    END IF;
END $$;

-- 8. AKTUALIZACJA KOLUMNY primary_graphic_source
-- ======================================
DO $$
DECLARE
    rows_updated INTEGER;
BEGIN
    UPDATE parts
    SET primary_graphic_source =
        CASE
            WHEN thumbnail_100 IS NOT NULL OR preview_4k IS NOT NULL THEN 'binary'
            WHEN user_image_file IS NOT NULL THEN 'user_image'
            WHEN cad_2d_file IS NOT NULL THEN 'cad_2d'
            WHEN cad_3d_file IS NOT NULL THEN 'cad_3d'
            ELSE NULL
        END
    WHERE primary_graphic_source IS NULL;

    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    RAISE NOTICE 'Zaktualizowano primary_graphic_source w % rekordach', rows_updated;
END $$;

-- 9. ANALYZE (bez VACUUM - musi być uruchomiony osobno)
-- ======================================
-- Aktualizacja statystyk dla optymalizatora zapytań
ANALYZE parts;

-- UWAGA: VACUUM musi być uruchomiony osobno poza transakcją!
-- Po zakończeniu tego skryptu, uruchom ręcznie:
-- VACUUM ANALYZE parts;

-- 10. RAPORT KOŃCOWY
-- ======================================
SELECT '=== PODSUMOWANIE CZYSZCZENIA ===' as info;

SELECT
    'parts' as "Tabela",
    COUNT(*) as "Liczba rekordów",
    COUNT(CASE WHEN thumbnail_100 IS NOT NULL THEN 1 END) as "Z thumbnail",
    COUNT(CASE WHEN preview_4k IS NOT NULL THEN 1 END) as "Z preview",
    COUNT(CASE WHEN cad_2d_file IS NOT NULL THEN 1 END) as "Ze ścieżką CAD 2D",
    COUNT(CASE WHEN cad_3d_file IS NOT NULL THEN 1 END) as "Ze ścieżką CAD 3D",
    pg_size_pretty(pg_total_relation_size('parts')) as "Rozmiar tabeli"
FROM parts;

-- Lista utworzonych backupów
SELECT
    tablename as "Backup",
    pg_size_pretty(pg_total_relation_size('public.'||tablename)) as "Rozmiar"
FROM pg_tables
WHERE schemaname = 'public'
AND tablename LIKE 'parts_backup_%'
ORDER BY tablename DESC;

-- Pokaż podsumowanie zmian
SELECT '=== PODSUMOWANIE ZMIAN ===' as info;
SELECT
    'Sprawdź komunikaty NOTICE powyżej' as "Status",
    'aby zobaczyć szczegóły wykonanych operacji' as "Informacja";