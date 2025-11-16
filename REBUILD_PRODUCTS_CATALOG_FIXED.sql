-- ============================================
-- SKRYPT PRZEBUDOWY TABELI products_catalog (POPRAWIONY DLA UUID)
-- Usuwa starą tabelę i tworzy nową bez bytea
-- ============================================

-- UWAGA: Ten skrypt USUWA CAŁĄ TABELĘ z danymi!
-- Wykonaj backup przed uruchomieniem!

-- 1. Zapisz istniejące dane (opcjonalnie)
-- CREATE TABLE products_catalog_backup AS SELECT * FROM products_catalog;

-- 2. Usuń starą tabelę
DROP TABLE IF EXISTS products_catalog CASCADE;

-- 3. Utwórz nową strukturę tabeli
CREATE TABLE products_catalog (
    -- Klucz główny (UUID jak w pozostałych tabelach)
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idx_code TEXT UNIQUE,

    -- Podstawowe informacje
    name TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    description TEXT,
    notes TEXT,
    tags TEXT[],

    -- Relacje (UUID!)
    material_id UUID REFERENCES materials_dict(id),
    customer_id UUID REFERENCES customers(id),

    -- Parametry techniczne
    thickness_mm NUMERIC(10,2),

    -- Wymiary fizyczne
    width_mm NUMERIC(10,2),
    height_mm NUMERIC(10,2),
    length_mm NUMERIC(10,2),
    weight_kg NUMERIC(10,3),
    surface_area_m2 NUMERIC(10,4),

    -- Produkcja
    production_time_minutes INTEGER,
    machine_type TEXT,

    -- Koszty
    material_cost NUMERIC(10,2) DEFAULT 0,
    laser_cost NUMERIC(10,2) DEFAULT 0,
    material_laser_cost NUMERIC(10,2) DEFAULT 0,
    bending_cost NUMERIC(10,2) DEFAULT 0,
    additional_costs NUMERIC(10,2) DEFAULT 0,

    -- URL do plików w Supabase Storage (zamiast bytea)
    cad_2d_url TEXT,
    cad_2d_filename TEXT,
    cad_2d_filesize BIGINT,
    cad_2d_mimetype TEXT,

    cad_3d_url TEXT,
    cad_3d_filename TEXT,
    cad_3d_filesize BIGINT,
    cad_3d_mimetype TEXT,

    user_image_url TEXT,
    user_image_filename TEXT,
    user_image_filesize BIGINT,
    user_image_mimetype TEXT,

    thumbnail_100_url TEXT,
    preview_800_url TEXT,
    preview_4k_url TEXT,

    additional_documentation_url TEXT,
    additional_documentation_filename TEXT,
    additional_documentation_filesize BIGINT,
    additional_documentation_mimetype TEXT,

    -- Źródło grafiki
    primary_graphic_source TEXT CHECK (primary_graphic_source IN ('2D', '3D', 'USER')),

    -- Statystyki użycia
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Audyt
    created_by TEXT,
    updated_by TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Status
    is_active BOOLEAN DEFAULT true
);

-- 4. Utwórz indeksy dla wydajności
CREATE INDEX idx_products_name ON products_catalog(name);
CREATE INDEX idx_products_category ON products_catalog(category);
CREATE INDEX idx_products_material ON products_catalog(material_id);
CREATE INDEX idx_products_customer ON products_catalog(customer_id);
CREATE INDEX idx_products_active ON products_catalog(is_active);
CREATE INDEX idx_products_created ON products_catalog(created_at);

-- Indeksy na URL (dla szybkiego sprawdzania czy plik istnieje)
CREATE INDEX idx_products_cad_2d_url ON products_catalog(cad_2d_url) WHERE cad_2d_url IS NOT NULL;
CREATE INDEX idx_products_cad_3d_url ON products_catalog(cad_3d_url) WHERE cad_3d_url IS NOT NULL;
CREATE INDEX idx_products_user_image_url ON products_catalog(user_image_url) WHERE user_image_url IS NOT NULL;

-- 5. Utwórz trigger do automatycznej aktualizacji updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_products_catalog_updated_at
    BEFORE UPDATE ON products_catalog
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 6. Utwórz funkcję do generowania idx_code
CREATE OR REPLACE FUNCTION generate_idx_code()
RETURNS TRIGGER AS $$
DECLARE
    new_code TEXT;
    counter INTEGER := 1;
BEGIN
    -- Jeśli idx_code już jest ustawiony, nie zmieniaj
    IF NEW.idx_code IS NOT NULL THEN
        RETURN NEW;
    END IF;

    -- Generuj kod w formacie: PC-YYYYMM-XXXX
    LOOP
        new_code := 'PC-' || TO_CHAR(NOW(), 'YYYYMM') || '-' || LPAD(counter::TEXT, 4, '0');

        -- Sprawdź czy kod jest unikalny
        IF NOT EXISTS (SELECT 1 FROM products_catalog WHERE idx_code = new_code) THEN
            NEW.idx_code := new_code;
            EXIT;
        END IF;

        counter := counter + 1;

        -- Zabezpieczenie przed nieskończoną pętlą
        IF counter > 9999 THEN
            RAISE EXCEPTION 'Cannot generate unique idx_code';
        END IF;
    END LOOP;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER generate_idx_code_trigger
    BEFORE INSERT ON products_catalog
    FOR EACH ROW
    EXECUTE FUNCTION generate_idx_code();

-- 7. Nadaj uprawnienia (jeśli używasz RLS)
ALTER TABLE products_catalog ENABLE ROW LEVEL SECURITY;

-- Polityka: wszyscy mogą czytać aktywne produkty
CREATE POLICY "Public read active products" ON products_catalog
    FOR SELECT USING (is_active = true);

-- Polityka: authenticated users mogą wszystko
CREATE POLICY "Authenticated full access" ON products_catalog
    FOR ALL USING (auth.uid() IS NOT NULL);

-- 8. Komentarze do kolumn (dokumentacja)
COMMENT ON TABLE products_catalog IS 'Katalog produktów/części z URL do plików w Storage';
COMMENT ON COLUMN products_catalog.idx_code IS 'Unikalny kod produktu (auto-generowany)';
COMMENT ON COLUMN products_catalog.primary_graphic_source IS 'Źródło głównej grafiki: 2D, 3D lub USER';
COMMENT ON COLUMN products_catalog.cad_2d_url IS 'URL do pliku CAD 2D w Supabase Storage';
COMMENT ON COLUMN products_catalog.cad_3d_url IS 'URL do pliku CAD 3D w Supabase Storage';
COMMENT ON COLUMN products_catalog.user_image_url IS 'URL do grafiki użytkownika w Storage';
COMMENT ON COLUMN products_catalog.thumbnail_100_url IS 'URL do miniatury 100x100 w Storage';
COMMENT ON COLUMN products_catalog.preview_800_url IS 'URL do podglądu 800px w Storage';
COMMENT ON COLUMN products_catalog.preview_4k_url IS 'URL do podglądu 4K w Storage';

-- ============================================
-- WERYFIKACJA
-- ============================================

-- Sprawdź strukturę tabeli
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'products_catalog'
ORDER BY ordinal_position;

-- ============================================
-- IMPORT DANYCH ZE STAREJ TABELI (opcjonalnie)
-- ============================================
-- Jeśli utworzyłeś backup, możesz zaimportować podstawowe dane:
/*
INSERT INTO products_catalog (
    id, idx_code,
    name, category, subcategory, description, notes, tags,
    material_id, customer_id, thickness_mm,
    width_mm, height_mm, length_mm, weight_kg, surface_area_m2,
    production_time_minutes, machine_type,
    material_cost, laser_cost, material_laser_cost, bending_cost, additional_costs,
    cad_2d_filename, cad_2d_filesize, cad_2d_mimetype,
    cad_3d_filename, cad_3d_filesize, cad_3d_mimetype,
    user_image_filename, user_image_filesize, user_image_mimetype,
    additional_documentation_filename, additional_documentation_filesize, additional_documentation_mimetype,
    primary_graphic_source, usage_count, last_used_at,
    is_active, created_at, updated_at, created_by, updated_by
)
SELECT
    id, idx_code,
    name, category, subcategory, description, notes, tags,
    material_id, customer_id, thickness_mm,
    width_mm, height_mm, length_mm, weight_kg, surface_area_m2,
    production_time_minutes, machine_type,
    material_cost, laser_cost, material_laser_cost, bending_cost, additional_costs,
    cad_2d_filename, cad_2d_filesize, cad_2d_mimetype,
    cad_3d_filename, cad_3d_filesize, cad_3d_mimetype,
    user_image_filename, user_image_filesize, user_image_mimetype,
    additional_documentation_filename, additional_documentation_filesize, additional_documentation_mimetype,
    primary_graphic_source, usage_count, last_used_at,
    is_active, created_at, updated_at, created_by, updated_by
FROM products_catalog_backup
WHERE TRUE;  -- Możesz dodać warunek filtrowania jeśli chcesz
*/

-- Koniec skryptu