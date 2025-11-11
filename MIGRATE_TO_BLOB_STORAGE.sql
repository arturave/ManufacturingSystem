-- ============================================
-- MIGRACJA DO PRZECHOWYWANIA BINARNEGO
-- Data: 2025-11-11
-- Cel: Zmiana pól na typ BLOB/BYTEA dla lepszej obsługi plików binarnych
-- ============================================

-- 1. ZATRZYMAJ TRANSAKCJĘ W RAZIE BŁĘDÓW
BEGIN;

-- ============================================
-- 2. PRODUCTS_CATALOG - MIGRACJA NA BYTEA
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
ADD COLUMN IF NOT EXISTS primary_graphic_source text;

-- ============================================
-- 3. PARTS - DODAJ KOLUMNY BINARNE
-- ============================================

-- Dodaj kolumny kosztów jeśli nie istnieją
ALTER TABLE public.parts
ADD COLUMN IF NOT EXISTS material_laser_cost numeric,
ADD COLUMN IF NOT EXISTS bending_cost numeric,
ADD COLUMN IF NOT EXISTS additional_costs numeric,
ADD COLUMN IF NOT EXISTS total_cost numeric,
ADD COLUMN IF NOT EXISTS notes text;

-- ============================================
-- 4. OBSŁUGA WIDOKÓW ZALEŻNYCH
-- ============================================

-- Zapisz definicje widoków przed usunięciem (opcjonalne - do dokumentacji)
-- Usuń widoki które zależą od starych kolumn
DROP VIEW IF EXISTS public.v_products_catalog_graphics CASCADE;
DROP VIEW IF EXISTS public.v_products_with_graphics CASCADE;
DROP VIEW IF EXISTS public.v_graphics_statistics CASCADE;

-- ============================================
-- 5. USUŃ STARE KOLUMNY PATH-BASED
-- ============================================

-- Teraz możemy bezpiecznie usunąć stare kolumny
-- UWAGA: Upewnij się że dane zostały zmigowane przed uruchomieniem!
ALTER TABLE public.products_catalog
DROP COLUMN IF EXISTS cad_2d_file CASCADE,
DROP COLUMN IF EXISTS cad_3d_file CASCADE,
DROP COLUMN IF EXISTS user_image_file CASCADE;

-- ============================================
-- 6. ODTWÓRZ WIDOKI Z NOWYMI KOLUMNAMI
-- ============================================

-- Widok: Produkty z informacją o plikach graficznych
CREATE OR REPLACE VIEW public.v_products_catalog_graphics AS
SELECT
    id,
    idx_code,
    name,
    material_id,
    CASE WHEN cad_2d_binary IS NOT NULL THEN TRUE ELSE FALSE END as has_2d,
    CASE WHEN cad_3d_binary IS NOT NULL THEN TRUE ELSE FALSE END as has_3d,
    CASE WHEN user_image_binary IS NOT NULL THEN TRUE ELSE FALSE END as has_image,
    CASE WHEN documentation_binary IS NOT NULL THEN TRUE ELSE FALSE END as has_docs,
    cad_2d_filename,
    cad_3d_filename,
    user_image_filename,
    documentation_filename,
    cad_2d_filesize,
    cad_3d_filesize,
    user_image_filesize,
    documentation_filesize,
    primary_graphic_source,
    created_at,
    updated_at
FROM public.products_catalog;

-- Widok: Produkty z pełnymi informacjami graficznymi
CREATE OR REPLACE VIEW public.v_products_with_graphics AS
SELECT
    p.*,
    m.name as material_name,
    m.category as material_category,
    CASE
        WHEN p.cad_2d_binary IS NOT NULL AND p.cad_3d_binary IS NOT NULL THEN 'Complete'
        WHEN p.cad_2d_binary IS NOT NULL OR p.cad_3d_binary IS NOT NULL THEN 'Partial'
        ELSE 'None'
    END as cad_status,
    COALESCE(
        octet_length(p.cad_2d_binary) +
        octet_length(p.cad_3d_binary) +
        octet_length(p.user_image_binary) +
        octet_length(p.documentation_binary) +
        octet_length(p.additional_documentation), 0
    ) as total_files_size
FROM public.products_catalog p
LEFT JOIN public.materials_dict m ON p.material_id = m.id;

-- Widok: Statystyki plików graficznych
CREATE OR REPLACE VIEW public.v_graphics_statistics AS
SELECT
    COUNT(*) as total_products,
    COUNT(cad_2d_binary) as products_with_2d,
    COUNT(cad_3d_binary) as products_with_3d,
    COUNT(user_image_binary) as products_with_images,
    COUNT(documentation_binary) as products_with_docs,
    COUNT(thumbnail_100) as products_with_thumbnails,
    pg_size_pretty(SUM(
        COALESCE(octet_length(cad_2d_binary), 0) +
        COALESCE(octet_length(cad_3d_binary), 0) +
        COALESCE(octet_length(user_image_binary), 0) +
        COALESCE(octet_length(documentation_binary), 0) +
        COALESCE(octet_length(additional_documentation), 0)
    )::bigint) as total_storage_size,
    ROUND(
        100.0 * COUNT(cad_2d_binary) / NULLIF(COUNT(*), 0), 2
    ) as percent_with_2d,
    ROUND(
        100.0 * COUNT(cad_3d_binary) / NULLIF(COUNT(*), 0), 2
    ) as percent_with_3d
FROM public.products_catalog;

-- ============================================
-- 7. DODAJ KOMENTARZE DO TABEL
-- ============================================

COMMENT ON TABLE public.products_catalog IS
'Katalog produktów - szablony produktów z plikami binarnymi
Pola binarne (bytea):
- cad_2d_binary: Pliki CAD 2D (DXF, DWG)
- cad_3d_binary: Pliki CAD 3D (STEP, STL, IGS)
- user_image_binary: Zdjęcie produktu (JPG, PNG)
- documentation_binary: Dokumentacja główna (PDF, DOC)
- additional_documentation: Dokumentacja dodatkowa (ZIP, 7Z)
- thumbnail_100: Miniaturka 100x100 px';

COMMENT ON TABLE public.parts IS
'Części w zamówieniach - instancje produktów z katalogu
Koszty produkcji są przechowywane per część';

COMMENT ON COLUMN public.products_catalog.cad_2d_binary IS 'Plik CAD 2D w formacie binarnym (bytea)';
COMMENT ON COLUMN public.products_catalog.cad_3d_binary IS 'Plik CAD 3D w formacie binarnym (bytea)';
COMMENT ON COLUMN public.products_catalog.user_image_binary IS 'Zdjęcie produktu w formacie binarnym (bytea)';
COMMENT ON COLUMN public.products_catalog.documentation_binary IS 'Dokumentacja główna w formacie binarnym (bytea)';
COMMENT ON COLUMN public.products_catalog.additional_documentation IS 'Dokumentacja dodatkowa (ZIP/7Z) w formacie binarnym (bytea)';

-- ============================================
-- 8. INDEKSY DLA WYDAJNOŚCI
-- ============================================

-- Indeksy na często używanych kolumnach
CREATE INDEX IF NOT EXISTS idx_products_catalog_idx_code ON public.products_catalog(idx_code);
CREATE INDEX IF NOT EXISTS idx_products_catalog_name ON public.products_catalog(name);
CREATE INDEX IF NOT EXISTS idx_products_catalog_material ON public.products_catalog(material_id);
CREATE INDEX IF NOT EXISTS idx_products_catalog_active ON public.products_catalog(is_active);

-- ============================================
-- 9. FUNKCJA POMOCNICZA DO SPRAWDZENIA ROZMIARU
-- ============================================

CREATE OR REPLACE FUNCTION get_binary_sizes()
RETURNS TABLE (
    table_name text,
    column_name text,
    total_size text,
    avg_size text,
    count bigint
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        'products_catalog'::text as table_name,
        'cad_2d_binary'::text as column_name,
        pg_size_pretty(sum(octet_length(cad_2d_binary))::bigint) as total_size,
        pg_size_pretty(avg(octet_length(cad_2d_binary))::bigint) as avg_size,
        count(*) filter (where cad_2d_binary is not null) as count
    FROM public.products_catalog
    UNION ALL
    SELECT
        'products_catalog'::text,
        'cad_3d_binary'::text,
        pg_size_pretty(sum(octet_length(cad_3d_binary))::bigint),
        pg_size_pretty(avg(octet_length(cad_3d_binary))::bigint),
        count(*) filter (where cad_3d_binary is not null)
    FROM public.products_catalog
    UNION ALL
    SELECT
        'products_catalog'::text,
        'user_image_binary'::text,
        pg_size_pretty(sum(octet_length(user_image_binary))::bigint),
        pg_size_pretty(avg(octet_length(user_image_binary))::bigint),
        count(*) filter (where user_image_binary is not null)
    FROM public.products_catalog;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 10. PODSUMOWANIE MIGRACJI
-- ============================================

-- Wyświetl informacje o strukturze tabel
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM
    information_schema.columns
WHERE
    table_schema = 'public'
    AND table_name = 'products_catalog'
    AND column_name LIKE '%binary%'
ORDER BY
    ordinal_position;

-- Sprawdź rozmiary danych binarnych
SELECT * FROM get_binary_sizes();

-- Sprawdź czy widoki zostały poprawnie utworzone
SELECT
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'public'
    AND table_name IN ('v_products_catalog_graphics', 'v_products_with_graphics', 'v_graphics_statistics')
ORDER BY table_name;

-- Komunikat końcowy
SELECT 'Migracja do przechowywania binarnego zakończona pomyślnie!' AS message;

-- ============================================
-- 11. ZATWIERDŹ TRANSAKCJĘ
-- ============================================

COMMIT;

-- ============================================
-- UWAGI:
-- 1. Przed uruchomieniem wykonaj BACKUP bazy danych
-- 2. Upewnij się że aplikacja obsługuje typ bytea
-- 3. Po migracji zweryfikuj działanie aplikacji
-- 4. Rozważ kompresję danych przed zapisem (ZIP)
-- ============================================