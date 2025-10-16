-- ============================================
-- ROZSZERZENIE MODUŁU PRODUKTÓW (DETALI)
-- System Zarządzania Produkcją - Laser/Prasa
-- Wykonaj w Supabase SQL Editor
-- ============================================

-- 1. TABELA: Słownik materiałów
DROP TABLE IF EXISTS materials_dict CASCADE;
CREATE TABLE materials_dict (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    category TEXT, -- np. 'STAL', 'ALUMINIUM', 'STAL NIERDZEWNA'
    density NUMERIC(6,3), -- gęstość [g/cm³]
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_materials_category ON materials_dict(category);
CREATE INDEX idx_materials_active ON materials_dict(is_active);

-- 2. ROZSZERZENIE TABELI PARTS (detali) o nowe pola
-- Dodaj nowe kolumny do istniejącej tabeli parts
ALTER TABLE parts
    ADD COLUMN IF NOT EXISTS bending_cost NUMERIC(12,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS additional_costs NUMERIC(12,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS graphic_high_res TEXT, -- ścieżka do grafiki HD
    ADD COLUMN IF NOT EXISTS graphic_low_res TEXT, -- ścieżka do grafiki miniaturki 200x200
    ADD COLUMN IF NOT EXISTS documentation_path TEXT, -- ścieżka do pliku CAD/PDF/ZIP
    ADD COLUMN IF NOT EXISTS duplicate_number INTEGER DEFAULT 0, -- numer powtórzenia nazwy
    ADD COLUMN IF NOT EXISTS material_id UUID REFERENCES materials_dict(id), -- relacja do słownika
    ADD COLUMN IF NOT EXISTS change_history JSONB DEFAULT '[]'::jsonb; -- historia zmian

-- Indeksy dla wydajności
CREATE INDEX IF NOT EXISTS idx_parts_material_id ON parts(material_id);
CREATE INDEX IF NOT EXISTS idx_parts_duplicate ON parts(duplicate_number);
CREATE INDEX IF NOT EXISTS idx_parts_name_search ON parts(name);
CREATE INDEX IF NOT EXISTS idx_parts_idx_code ON parts(idx_code);

-- 3. WIDOK: Części z nazwami materiałów
CREATE OR REPLACE VIEW v_parts_full AS
SELECT
    p.*,
    m.name AS material_name,
    m.category AS material_category,
    m.density AS material_density
FROM parts p
LEFT JOIN materials_dict m ON m.id = p.material_id;

-- 4. FUNKCJA: Automatyczne nadawanie indeksu dla nowego detalu
CREATE OR REPLACE FUNCTION generate_part_index_fn()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_next_id INTEGER;
BEGIN
    -- Jeśli idx_code nie jest podany, wygeneruj automatycznie
    IF NEW.idx_code IS NULL OR LENGTH(NEW.idx_code) = 0 THEN
        -- Pobierz maksymalny numer indeksu
        SELECT COALESCE(MAX(CAST(SUBSTRING(idx_code FROM 'IDX-(\d+)') AS INTEGER)), 0) + 1
        INTO v_next_id
        FROM parts
        WHERE idx_code ~ '^IDX-\d+$';

        -- Ustaw nowy indeks: IDX-00001
        NEW.idx_code := 'IDX-' || LPAD(v_next_id::TEXT, 5, '0');
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_generate_part_index ON parts;
CREATE TRIGGER trg_generate_part_index
BEFORE INSERT ON parts
FOR EACH ROW
EXECUTE FUNCTION generate_part_index_fn();

-- 5. FUNKCJA: Sprawdzanie duplikatów detali
CREATE OR REPLACE FUNCTION check_duplicate_parts_fn(
    p_name TEXT,
    p_thickness NUMERIC,
    p_material_id UUID,
    p_exclude_id UUID DEFAULT NULL
)
RETURNS TABLE(
    id UUID,
    idx_code TEXT,
    name TEXT,
    material_name TEXT,
    thickness_mm NUMERIC,
    qty INTEGER,
    duplicate_number INTEGER,
    similarity_score NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.idx_code,
        p.name,
        m.name AS material_name,
        p.thickness_mm,
        p.qty,
        p.duplicate_number,
        -- Oblicz score podobieństwa (nazwa + grubość + materiał)
        (
            CASE WHEN LOWER(p.name) = LOWER(p_name) THEN 50 ELSE 0 END +
            CASE WHEN p.thickness_mm = p_thickness THEN 30 ELSE 0 END +
            CASE WHEN p.material_id = p_material_id THEN 20 ELSE 0 END
        )::NUMERIC AS similarity_score
    FROM parts p
    LEFT JOIN materials_dict m ON m.id = p.material_id
    WHERE
        (p.id != p_exclude_id OR p_exclude_id IS NULL)
        AND (
            LOWER(p.name) LIKE LOWER('%' || p_name || '%')
            OR similarity(p.name, p_name) > 0.3 -- wymaga rozszerzenia pg_trgm
            OR (p.thickness_mm = p_thickness AND p.material_id = p_material_id)
        )
    ORDER BY similarity_score DESC
    LIMIT 10;
END;
$$;

-- 6. FUNKCJA: Automatyczne ustawianie numeru duplikatu
CREATE OR REPLACE FUNCTION set_duplicate_number_fn()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_max_dup INTEGER;
BEGIN
    -- Sprawdź, czy istnieją inne detale o tej samej nazwie, grubości i materiale
    SELECT COALESCE(MAX(duplicate_number), -1) + 1
    INTO v_max_dup
    FROM parts
    WHERE
        LOWER(name) = LOWER(NEW.name)
        AND thickness_mm = NEW.thickness_mm
        AND material_id = NEW.material_id
        AND id != NEW.id;

    -- Jeśli znaleziono podobne detale, ustaw numer duplikatu
    IF v_max_dup > 0 THEN
        NEW.duplicate_number := v_max_dup;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_set_duplicate_number ON parts;
CREATE TRIGGER trg_set_duplicate_number
BEFORE INSERT ON parts
FOR EACH ROW
EXECUTE FUNCTION set_duplicate_number_fn();

-- 7. FUNKCJA: Logowanie zmian w historii detalu
CREATE OR REPLACE FUNCTION log_part_changes_fn()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_change_entry JSONB;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        -- Utwórz wpis zmiany
        v_change_entry := jsonb_build_object(
            'timestamp', NOW(),
            'user', COALESCE(current_setting('request.jwt.claims', true)::json->>'email', 'system'),
            'changes', jsonb_build_object(
                'name', CASE WHEN NEW.name != OLD.name THEN jsonb_build_object('old', OLD.name, 'new', NEW.name) ELSE NULL END,
                'material_id', CASE WHEN NEW.material_id != OLD.material_id THEN jsonb_build_object('old', OLD.material_id, 'new', NEW.material_id) ELSE NULL END,
                'thickness_mm', CASE WHEN NEW.thickness_mm != OLD.thickness_mm THEN jsonb_build_object('old', OLD.thickness_mm, 'new', NEW.thickness_mm) ELSE NULL END,
                'bending_cost', CASE WHEN NEW.bending_cost != OLD.bending_cost THEN jsonb_build_object('old', OLD.bending_cost, 'new', NEW.bending_cost) ELSE NULL END,
                'additional_costs', CASE WHEN NEW.additional_costs != OLD.additional_costs THEN jsonb_build_object('old', OLD.additional_costs, 'new', NEW.additional_costs) ELSE NULL END,
                'qty', CASE WHEN NEW.qty != OLD.qty THEN jsonb_build_object('old', OLD.qty, 'new', NEW.qty) ELSE NULL END
            )
        );

        -- Dodaj do historii
        NEW.change_history := COALESCE(NEW.change_history, '[]'::jsonb) || v_change_entry;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_log_part_changes ON parts;
CREATE TRIGGER trg_log_part_changes
BEFORE UPDATE ON parts
FOR EACH ROW
EXECUTE FUNCTION log_part_changes_fn();

-- 8. RLS (Row Level Security) dla nowych tabel
ALTER TABLE materials_dict ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS materials_dict_anon_all ON materials_dict;
CREATE POLICY materials_dict_anon_all ON materials_dict
    FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);

-- 9. GRANT dostęp do widoków
GRANT SELECT ON v_parts_full TO anon;
GRANT EXECUTE ON FUNCTION check_duplicate_parts_fn(TEXT, NUMERIC, UUID, UUID) TO anon;

-- 10. DANE TESTOWE - Słownik materiałów
INSERT INTO materials_dict (name, description, category, density) VALUES
    ('DC01', 'Stal DC01 - blacha zmiękczana', 'STAL', 7.85),
    ('DC04', 'Stal DC04 - blacha głębokotłoczna', 'STAL', 7.85),
    ('S235JR', 'Stal konstrukcyjna S235JR', 'STAL', 7.85),
    ('S355J2', 'Stal konstrukcyjna S355J2', 'STAL', 7.85),
    ('1.4301 (304)', 'Stal nierdzewna 304 (18/10)', 'STAL_NIERDZEWNA', 7.93),
    ('1.4404 (316L)', 'Stal nierdzewna 316L', 'STAL_NIERDZEWNA', 8.00),
    ('AW-5754', 'Aluminium AW-5754 (AlMg3)', 'ALUMINIUM', 2.67),
    ('AW-5083', 'Aluminium AW-5083', 'ALUMINIUM', 2.66),
    ('AW-6082', 'Aluminium AW-6082', 'ALUMINIUM', 2.70),
    ('CuZn37', 'Mosiądz CuZn37 (MS63)', 'MOSIADZ', 8.44),
    ('CW024A', 'Miedź elektrolityczna', 'MIEDZ', 8.96),
    ('Hardox 400', 'Stal Hardox 400 - odporna na ścieranie', 'STAL_SPECJALNA', 7.85),
    ('Hardox 500', 'Stal Hardox 500 - odporna na ścieranie', 'STAL_SPECJALNA', 7.85)
ON CONFLICT (name) DO NOTHING;

-- 11. WIDOK: Statystyki materiałów
CREATE OR REPLACE VIEW v_materials_usage_stats AS
SELECT
    m.id,
    m.name,
    m.category,
    COUNT(p.id) AS usage_count,
    SUM(p.qty) AS total_quantity,
    AVG(p.thickness_mm) AS avg_thickness,
    COUNT(DISTINCT p.order_id) AS order_count
FROM materials_dict m
LEFT JOIN parts p ON p.material_id = m.id
GROUP BY m.id, m.name, m.category
ORDER BY usage_count DESC;

GRANT SELECT ON v_materials_usage_stats TO anon;

-- 12. FUNKCJA: Wyszukiwanie części po filtrach
CREATE OR REPLACE FUNCTION search_parts_fn(
    p_name TEXT DEFAULT NULL,
    p_material_id UUID DEFAULT NULL,
    p_thickness_from NUMERIC DEFAULT NULL,
    p_thickness_to NUMERIC DEFAULT NULL,
    p_customer_id UUID DEFAULT NULL,
    p_date_from DATE DEFAULT NULL,
    p_date_to DATE DEFAULT NULL
)
RETURNS TABLE(
    id UUID,
    idx_code TEXT,
    name TEXT,
    material_name TEXT,
    thickness_mm NUMERIC,
    qty INTEGER,
    bending_cost NUMERIC,
    additional_costs NUMERIC,
    order_id UUID,
    process_no TEXT,
    customer_name TEXT,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.idx_code,
        p.name,
        m.name AS material_name,
        p.thickness_mm,
        p.qty,
        p.bending_cost,
        p.additional_costs,
        p.order_id,
        o.process_no,
        c.name AS customer_name,
        p.created_at
    FROM parts p
    LEFT JOIN materials_dict m ON m.id = p.material_id
    LEFT JOIN orders o ON o.id = p.order_id
    LEFT JOIN customers c ON c.id = o.customer_id
    WHERE
        (p_name IS NULL OR LOWER(p.name) LIKE LOWER('%' || p_name || '%'))
        AND (p_material_id IS NULL OR p.material_id = p_material_id)
        AND (p_thickness_from IS NULL OR p.thickness_mm >= p_thickness_from)
        AND (p_thickness_to IS NULL OR p.thickness_mm <= p_thickness_to)
        AND (p_customer_id IS NULL OR o.customer_id = p_customer_id)
        AND (p_date_from IS NULL OR p.created_at::DATE >= p_date_from)
        AND (p_date_to IS NULL OR p.created_at::DATE <= p_date_to)
    ORDER BY p.created_at DESC;
END;
$$;

GRANT EXECUTE ON FUNCTION search_parts_fn(TEXT, UUID, NUMERIC, NUMERIC, UUID, DATE, DATE) TO anon;

-- ============================================
-- STORAGE - Folder dla grafik detali
-- ============================================
-- Grafiki będą przechowywane w bucket 'attachments' w podfolderach:
-- - attachments/parts/{part_id}/high_res.png
-- - attachments/parts/{part_id}/low_res.png
-- - attachments/parts/{part_id}/documentation.{ext}

-- Polityki storage są już ustawione dla bucket 'attachments'

-- Koniec skryptu
