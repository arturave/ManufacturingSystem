-- ============================================
-- BEZPIECZNA MIGRACJA DO PRZECHOWYWANIA BINARNEGO
-- Data: 2025-11-11
-- Wersja: Bezpieczna - nie usuwa starych kolumn
-- Cel: Dodaje nowe kolumny BLOB/BYTEA zachowując stare
-- ============================================

-- 1. ZATRZYMAJ TRANSAKCJĘ W RAZIE BŁĘDÓW
BEGIN;

-- ============================================
-- 2. PRODUCTS_CATALOG - DODAJ KOLUMNY BINARNE
-- ============================================

-- Dodaj kolumny binarne jeśli nie istnieją
ALTER TABLE public.products_catalog
ADD COLUMN IF NOT EXISTS cad_2d_binary bytea,
ADD COLUMN IF NOT EXISTS cad_3d_binary bytea,
ADD COLUMN IF NOT EXISTS user_image_binary bytea,
ADD COLUMN IF NOT EXISTS documentation_binary bytea,
ADD COLUMN IF NOT EXISTS additional_documentation bytea;

-- Dodaj kolumny metadanych
ALTER TABLE public.products_catalog
ADD COLUMN IF NOT EXISTS cad_2d_filename text,
ADD COLUMN IF NOT EXISTS cad_3d_filename text,
ADD COLUMN IF NOT EXISTS user_image_filename text,
ADD COLUMN IF NOT EXISTS documentation_filename text,
ADD COLUMN IF NOT EXISTS additional_documentation_filename text,
ADD COLUMN IF NOT EXISTS cad_2d_filesize bigint,
ADD COLUMN IF NOT EXISTS cad_3d_filesize bigint,
ADD COLUMN IF NOT EXISTS user_image_filesize bigint,
ADD COLUMN IF NOT EXISTS documentation_filesize bigint,
ADD COLUMN IF NOT EXISTS additional_documentation_filesize bigint,
ADD COLUMN IF NOT EXISTS cad_2d_mimetype text,
ADD COLUMN IF NOT EXISTS cad_3d_mimetype text,
ADD COLUMN IF NOT EXISTS user_image_mimetype text,
ADD COLUMN IF NOT EXISTS documentation_mimetype text,
ADD COLUMN IF NOT EXISTS additional_documentation_mimetype text;

-- Dodaj pola wymiarów i produkcji
ALTER TABLE public.products_catalog
ADD COLUMN IF NOT EXISTS subcategory text,
ADD COLUMN IF NOT EXISTS width_mm numeric,
ADD COLUMN IF NOT EXISTS height_mm numeric,
ADD COLUMN IF NOT EXISTS length_mm numeric,
ADD COLUMN IF NOT EXISTS weight_kg numeric,
ADD COLUMN IF NOT EXISTS surface_area_m2 numeric,
ADD COLUMN IF NOT EXISTS production_time_minutes integer,
ADD COLUMN IF NOT EXISTS machine_type text;

-- Dodaj pole thumbnail
ALTER TABLE public.products_catalog
ADD COLUMN IF NOT EXISTS thumbnail_100 bytea,
ADD COLUMN IF NOT EXISTS preview_800 bytea,
ADD COLUMN IF NOT EXISTS preview_4k bytea,
ADD COLUMN IF NOT EXISTS primary_graphic_source text;

-- ============================================
-- 3. PARTS - DODAJ KOLUMNY KOSZTÓW
-- ============================================

-- Dodaj kolumny kosztów jeśli nie istnieją
ALTER TABLE public.parts
ADD COLUMN IF NOT EXISTS material_laser_cost numeric,
ADD COLUMN IF NOT EXISTS bending_cost numeric,
ADD COLUMN IF NOT EXISTS additional_costs numeric,
ADD COLUMN IF NOT EXISTS total_cost numeric,
ADD COLUMN IF NOT EXISTS notes text;

-- ============================================
-- 4. AKTUALIZUJ WIDOKI (bez usuwania starych)
-- ============================================

-- Dodaj nowy widok dla kompatybilności
CREATE OR REPLACE VIEW public.v_products_binary_status AS
SELECT
    id,
    idx_code,
    name,
    -- Sprawdź stare kolumny
    CASE WHEN cad_2d_file IS NOT NULL THEN 'PATH'
         WHEN cad_2d_binary IS NOT NULL THEN 'BINARY'
         ELSE 'NONE' END as cad_2d_status,
    CASE WHEN cad_3d_file IS NOT NULL THEN 'PATH'
         WHEN cad_3d_binary IS NOT NULL THEN 'BINARY'
         ELSE 'NONE' END as cad_3d_status,
    CASE WHEN user_image_file IS NOT NULL THEN 'PATH'
         WHEN user_image_binary IS NOT NULL THEN 'BINARY'
         ELSE 'NONE' END as user_image_status,
    -- Rozmiary plików
    cad_2d_filesize,
    cad_3d_filesize,
    user_image_filesize,
    -- Nazwy plików
    COALESCE(cad_2d_filename, cad_2d_file) as cad_2d_name,
    COALESCE(cad_3d_filename, cad_3d_file) as cad_3d_name,
    COALESCE(user_image_filename, user_image_file) as user_image_name,
    created_at,
    updated_at
FROM public.products_catalog;

-- ============================================
-- 5. DODAJ KOMENTARZE DO TABEL
-- ============================================

COMMENT ON TABLE public.products_catalog IS
'Katalog produktów - szablony produktów
UWAGA: W trakcie migracji z path-based na binary storage
Nowe pola binarne (bytea):
- cad_2d_binary: Pliki CAD 2D (DXF, DWG)
- cad_3d_binary: Pliki CAD 3D (STEP, STL, IGS)
- user_image_binary: Zdjęcie produktu (JPG, PNG)
- documentation_binary: Dokumentacja główna (PDF, DOC)
- additional_documentation: Dokumentacja dodatkowa (ZIP, 7Z)
- thumbnail_100: Miniaturka 100x100 px
Stare pola (do usunięcia po migracji):
- cad_2d_file, cad_3d_file, user_image_file';

-- ============================================
-- 6. INDEKSY DLA WYDAJNOŚCI
-- ============================================

-- Indeksy na często używanych kolumnach
CREATE INDEX IF NOT EXISTS idx_products_catalog_idx_code ON public.products_catalog(idx_code);
CREATE INDEX IF NOT EXISTS idx_products_catalog_name ON public.products_catalog(name);
CREATE INDEX IF NOT EXISTS idx_products_catalog_material ON public.products_catalog(material_id);
CREATE INDEX IF NOT EXISTS idx_products_catalog_active ON public.products_catalog(is_active);

-- ============================================
-- 7. FUNKCJA POMOCNICZA DO ANALIZY
-- ============================================

CREATE OR REPLACE FUNCTION analyze_migration_status()
RETURNS TABLE (
    description text,
    count bigint
) AS $$
BEGIN
    RETURN QUERY
    SELECT 'Products with old path fields'::text,
           COUNT(*)
    FROM public.products_catalog
    WHERE cad_2d_file IS NOT NULL
       OR cad_3d_file IS NOT NULL
       OR user_image_file IS NOT NULL

    UNION ALL

    SELECT 'Products with new binary fields'::text,
           COUNT(*)
    FROM public.products_catalog
    WHERE cad_2d_binary IS NOT NULL
       OR cad_3d_binary IS NOT NULL
       OR user_image_binary IS NOT NULL

    UNION ALL

    SELECT 'Products with both (conflict)'::text,
           COUNT(*)
    FROM public.products_catalog
    WHERE (cad_2d_file IS NOT NULL AND cad_2d_binary IS NOT NULL)
       OR (cad_3d_file IS NOT NULL AND cad_3d_binary IS NOT NULL)
       OR (user_image_file IS NOT NULL AND user_image_binary IS NOT NULL)

    UNION ALL

    SELECT 'Products without any files'::text,
           COUNT(*)
    FROM public.products_catalog
    WHERE cad_2d_file IS NULL AND cad_2d_binary IS NULL
      AND cad_3d_file IS NULL AND cad_3d_binary IS NULL
      AND user_image_file IS NULL AND user_image_binary IS NULL;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 8. PODSUMOWANIE MIGRACJI
-- ============================================

-- Sprawdź status migracji
SELECT * FROM analyze_migration_status();

-- Wyświetl nowe kolumny
SELECT
    column_name,
    data_type,
    is_nullable
FROM
    information_schema.columns
WHERE
    table_schema = 'public'
    AND table_name = 'products_catalog'
    AND (column_name LIKE '%binary%'
         OR column_name LIKE '%filename%'
         OR column_name LIKE '%filesize%')
ORDER BY
    ordinal_position;

-- Komunikat końcowy
SELECT 'Bezpieczna migracja zakończona!' AS message,
       'Stare kolumny (cad_2d_file, cad_3d_file, user_image_file) NIE zostały usunięte.' AS info,
       'Możesz je usunąć później używając skryptu MIGRATE_TO_BLOB_STORAGE.sql' AS next_step;

-- ============================================
-- 9. ZATWIERDŹ TRANSAKCJĘ
-- ============================================

COMMIT;

-- ============================================
-- KOLEJNE KROKI:
-- 1. Zweryfikuj że aplikacja działa z nowymi kolumnami
-- 2. Przenieś dane ze starych kolumn do nowych (jeśli potrzebne)
-- 3. Gdy wszystko działa, uruchom pełną migrację
--    która usunie stare kolumny
-- ============================================