-- =====================================================
-- SKRYPT 3: DODANIE BRAKUJĄCYCH KOLUMN I FUNKCJONALNOŚCI
-- =====================================================
-- Ten skrypt dodaje brakujące kolumny dla lepszej obsługi plików
-- Uruchom w Supabase SQL Editor

-- 1. DODANIE KOLUMN DLA METADANYCH PLIKÓW
-- ======================================
-- Kolumny przechowują nazwy oryginalnych plików i ich rozmiary

-- Dodaj kolumny dla nazw plików (jeśli nie istnieją)
ALTER TABLE parts
ADD COLUMN IF NOT EXISTS cad_2d_filename text,
ADD COLUMN IF NOT EXISTS cad_3d_filename text,
ADD COLUMN IF NOT EXISTS user_image_filename text,
ADD COLUMN IF NOT EXISTS documentation_filename text;

-- Dodaj kolumny dla rozmiarów plików
ALTER TABLE parts
ADD COLUMN IF NOT EXISTS cad_2d_filesize bigint,
ADD COLUMN IF NOT EXISTS cad_3d_filesize bigint,
ADD COLUMN IF NOT EXISTS user_image_filesize bigint,
ADD COLUMN IF NOT EXISTS documentation_filesize bigint;

-- Dodaj kolumny dla typów MIME
ALTER TABLE parts
ADD COLUMN IF NOT EXISTS cad_2d_mimetype text,
ADD COLUMN IF NOT EXISTS cad_3d_mimetype text,
ADD COLUMN IF NOT EXISTS user_image_mimetype text;

-- Dodaj kolumnę dla daty ostatniej aktualizacji plików
ALTER TABLE parts
ADD COLUMN IF NOT EXISTS files_updated_at timestamp with time zone;

-- 2. DODANIE KOLUMN DLA DANYCH BINARNYCH (jeśli potrzebne)
-- ======================================
-- Tylko jeśli chcesz przechowywać pliki CAD jako BLOB

ALTER TABLE parts
ADD COLUMN IF NOT EXISTS cad_2d_binary bytea,
ADD COLUMN IF NOT EXISTS cad_3d_binary bytea,
ADD COLUMN IF NOT EXISTS user_image_binary bytea,
ADD COLUMN IF NOT EXISTS documentation_binary bytea;

-- 3. DODANIE KOLUMN DLA WERSJONOWANIA
-- ======================================
ALTER TABLE parts
ADD COLUMN IF NOT EXISTS version_number integer DEFAULT 1,
ADD COLUMN IF NOT EXISTS is_latest_version boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS parent_version_id uuid REFERENCES parts(id);

-- 4. DODANIE KOLUMN DLA STATUSÓW
-- ======================================
ALTER TABLE parts
ADD COLUMN IF NOT EXISTS status text DEFAULT 'draft'
    CHECK (status IN ('draft', 'review', 'approved', 'production', 'archived')),
ADD COLUMN IF NOT EXISTS approved_by text,
ADD COLUMN IF NOT EXISTS approved_at timestamp with time zone;

-- 5. DODANIE KOLUMN DLA KATEGORYZACJI
-- ======================================
ALTER TABLE parts
ADD COLUMN IF NOT EXISTS category text,
ADD COLUMN IF NOT EXISTS subcategory text,
ADD COLUMN IF NOT EXISTS tags text[];

-- 6. DODANIE KOLUMN DLA WYMIARÓW
-- ======================================
ALTER TABLE parts
ADD COLUMN IF NOT EXISTS width_mm numeric,
ADD COLUMN IF NOT EXISTS height_mm numeric,
ADD COLUMN IF NOT EXISTS length_mm numeric,
ADD COLUMN IF NOT EXISTS weight_kg numeric,
ADD COLUMN IF NOT EXISTS surface_area_m2 numeric;

-- 7. DODANIE KOLUMN DLA PRODUKCJI
-- ======================================
ALTER TABLE parts
ADD COLUMN IF NOT EXISTS production_time_minutes integer,
ADD COLUMN IF NOT EXISTS machine_type text,
ADD COLUMN IF NOT EXISTS priority integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS notes text;

-- 8. DODANIE KOLUMN DLA ŚLEDZENIA ZMIAN
-- ======================================
ALTER TABLE parts
ADD COLUMN IF NOT EXISTS modified_by text,
ADD COLUMN IF NOT EXISTS modified_at timestamp with time zone DEFAULT now();

-- 9. UTWORZENIE FUNKCJI POMOCNICZYCH
-- ======================================

-- Funkcja do automatycznej aktualizacji modified_at
CREATE OR REPLACE FUNCTION update_modified_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger dla automatycznej aktualizacji czasu modyfikacji
DROP TRIGGER IF EXISTS update_parts_modified ON parts;
CREATE TRIGGER update_parts_modified
    BEFORE UPDATE ON parts
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_time();

-- Funkcja do obliczania całkowitego kosztu
CREATE OR REPLACE FUNCTION calculate_total_cost(
    p_material_cost numeric,
    p_laser_cost numeric,
    p_bending_cost numeric,
    p_additional_costs numeric,
    p_qty integer
) RETURNS numeric AS $$
BEGIN
    RETURN COALESCE(
        (COALESCE(p_material_cost, 0) +
         COALESCE(p_laser_cost, 0) +
         COALESCE(p_bending_cost, 0) +
         COALESCE(p_additional_costs, 0)) * COALESCE(p_qty, 1),
        0
    );
END;
$$ LANGUAGE plpgsql;

-- 10. UTWORZENIE WIDOKU DLA ŁATWIEJSZEGO DOSTĘPU
-- ======================================
CREATE OR REPLACE VIEW parts_with_costs AS
SELECT
    p.*,
    calculate_total_cost(
        p.material_cost,
        p.laser_cost,
        p.bending_cost,
        p.additional_costs,
        p.qty
    ) as total_cost,
    CASE
        WHEN p.thumbnail_100 IS NOT NULL THEN 'thumbnail'
        WHEN p.preview_4k IS NOT NULL THEN 'preview'
        WHEN p.user_image_file IS NOT NULL THEN 'user_image'
        WHEN p.cad_2d_file IS NOT NULL THEN 'cad_2d'
        WHEN p.cad_3d_file IS NOT NULL THEN 'cad_3d'
        ELSE 'none'
    END as available_visualization,
    CASE
        WHEN p.cad_2d_binary IS NOT NULL THEN true
        WHEN p.cad_3d_binary IS NOT NULL THEN true
        WHEN p.user_image_binary IS NOT NULL THEN true
        WHEN p.documentation_binary IS NOT NULL THEN true
        ELSE false
    END as has_binary_files
FROM parts p;

-- 11. UTWORZENIE WIDOKU DLA HISTORII ZMIAN
-- ======================================
CREATE OR REPLACE VIEW parts_change_history AS
SELECT
    id,
    name,
    idx_code,
    change_history,
    jsonb_array_length(COALESCE(change_history, '[]'::jsonb)) as change_count,
    change_history->-1 as last_change,
    created_at,
    modified_at
FROM parts
WHERE jsonb_array_length(COALESCE(change_history, '[]'::jsonb)) > 0
ORDER BY modified_at DESC;

-- 12. RAPORT Z DODANYCH KOLUMN
-- ======================================
SELECT '=== NOWE KOLUMNY W TABELI PARTS ===' as info;

SELECT
    column_name as "Kolumna",
    data_type as "Typ danych",
    column_default as "Wartość domyślna"
FROM information_schema.columns
WHERE table_name = 'parts'
AND column_name IN (
    'cad_2d_filename', 'cad_3d_filename', 'user_image_filename', 'documentation_filename',
    'cad_2d_filesize', 'cad_3d_filesize', 'user_image_filesize', 'documentation_filesize',
    'cad_2d_mimetype', 'cad_3d_mimetype', 'user_image_mimetype',
    'cad_2d_binary', 'cad_3d_binary', 'user_image_binary', 'documentation_binary',
    'files_updated_at', 'version_number', 'is_latest_version', 'parent_version_id',
    'status', 'approved_by', 'approved_at',
    'category', 'subcategory', 'tags',
    'width_mm', 'height_mm', 'length_mm', 'weight_kg', 'surface_area_m2',
    'production_time_minutes', 'machine_type', 'priority', 'notes',
    'modified_by', 'modified_at'
)
ORDER BY column_name;

-- Pokaż utworzone widoki
SELECT '=== UTWORZONE WIDOKI ===' as info;
SELECT
    viewname as "Widok",
    definition as "Definicja"
FROM pg_views
WHERE schemaname = 'public'
AND viewname IN ('parts_with_costs', 'parts_change_history');