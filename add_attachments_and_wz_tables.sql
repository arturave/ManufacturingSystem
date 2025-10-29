-- ============================================
-- Tabele dla załączników i dokumentów WZ
-- System Zarządzania Produkcją - Rozszerzenie
-- ============================================

-- ============================================
-- 1. TABELA: attachments - system załączników
-- ============================================

DROP TABLE IF EXISTS attachments CASCADE;

CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Odniesienie do encji (zamówienie lub oferta)
    entity_type TEXT NOT NULL CHECK (entity_type IN ('order', 'quotation')),
    entity_id UUID NOT NULL,

    -- Dane archiwum ZIP
    archive_data BYTEA NOT NULL,  -- Spakowane pliki jako ZIP
    files_metadata JSONB NOT NULL DEFAULT '[]'::jsonb,  -- Lista plików w archiwum

    -- Format files_metadata:
    -- [
    --   {"filename": "drawing.pdf", "size": 1024, "type": "application/pdf"},
    --   {"filename": "spec.docx", "size": 2048, "type": "application/vnd..."}
    -- ]

    -- Metadane
    total_size BIGINT NOT NULL,  -- Całkowity rozmiar rozpakowanych plików
    compressed_size BIGINT,      -- Rozmiar archiwum ZIP
    files_count INTEGER NOT NULL DEFAULT 0,

    -- Audyt
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by TEXT,

    -- Dodatkowe pole dla notatek
    notes TEXT
);

-- Indeksy dla wydajności
CREATE INDEX idx_attachments_entity ON attachments(entity_type, entity_id);
CREATE INDEX idx_attachments_created_at ON attachments(created_at);

-- Trigger dla updated_at
CREATE OR REPLACE FUNCTION update_attachments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_attachments_updated_at ON attachments;
CREATE TRIGGER trg_update_attachments_updated_at
BEFORE UPDATE ON attachments
FOR EACH ROW
EXECUTE FUNCTION update_attachments_updated_at();

-- Funkcja pomocnicza do pobierania liczby załączników dla encji
CREATE OR REPLACE FUNCTION get_attachments_count(
    p_entity_type TEXT,
    p_entity_id UUID
)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM attachments
    WHERE entity_type = p_entity_type
      AND entity_id = p_entity_id;

    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Funkcja pomocnicza do pobierania całkowitego rozmiaru załączników
CREATE OR REPLACE FUNCTION get_attachments_total_size(
    p_entity_type TEXT,
    p_entity_id UUID
)
RETURNS BIGINT AS $$
DECLARE
    v_total BIGINT;
BEGIN
    SELECT COALESCE(SUM(total_size), 0) INTO v_total
    FROM attachments
    WHERE entity_type = p_entity_type
      AND entity_id = p_entity_id;

    RETURN v_total;
END;
$$ LANGUAGE plpgsql;

-- Komentarze
COMMENT ON TABLE attachments IS 'Załączniki do zamówień i ofert przechowywane jako archiwa ZIP';
COMMENT ON COLUMN attachments.entity_type IS 'Typ encji: order lub quotation';
COMMENT ON COLUMN attachments.entity_id IS 'ID zamówienia (orders.id) lub oferty (quotations.id)';
COMMENT ON COLUMN attachments.archive_data IS 'Spakowane pliki w formacie ZIP jako BYTEA';
COMMENT ON COLUMN attachments.files_metadata IS 'JSON z listą plików w archiwum';


-- ============================================
-- 2. TABELA: delivery_notes - dokumenty WZ
-- ============================================

DROP TABLE IF EXISTS delivery_notes CASCADE;

CREATE TABLE delivery_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Numer WZ bazujący na numerze zamówienia
    wz_number TEXT UNIQUE NOT NULL,  -- Format: WZ-{process_no} np. WZ-2025-00001

    -- Odniesienie do zamówienia
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,

    -- Dane dokumentu
    issue_date DATE NOT NULL DEFAULT CURRENT_DATE,

    -- Dane odbiorcy (kopiowane z customers, można edytować)
    recipient_name TEXT NOT NULL,
    recipient_address TEXT,
    recipient_city TEXT,
    recipient_postal_code TEXT,
    recipient_nip TEXT,
    recipient_contact_person TEXT,
    recipient_contact_phone TEXT,

    -- Pozycje WZ (jako JSON dla elastyczności)
    items JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Format items:
    -- [
    --   {
    --     "lp": 1,
    --     "name": "Blacha perforowana",
    --     "quantity": 10,
    --     "unit": "szt",
    --     "notes": "Stal S235"
    --   }
    -- ]

    -- Dodatkowe informacje
    notes TEXT,
    transport_info TEXT,  -- Informacje o transporcie

    -- Status WZ
    status TEXT DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'ISSUED', 'RECEIVED')),

    -- Daty
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by TEXT,
    issued_at TIMESTAMPTZ,  -- Kiedy WZ zostało wystawione
    received_at TIMESTAMPTZ -- Kiedy potwierdzono odbiór
);

-- Indeksy
CREATE INDEX idx_delivery_notes_order ON delivery_notes(order_id);
CREATE INDEX idx_delivery_notes_issue_date ON delivery_notes(issue_date);
CREATE INDEX idx_delivery_notes_status ON delivery_notes(status);
CREATE UNIQUE INDEX idx_delivery_notes_wz_number ON delivery_notes(wz_number);

-- Trigger dla updated_at
CREATE OR REPLACE FUNCTION update_delivery_notes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_delivery_notes_updated_at ON delivery_notes;
CREATE TRIGGER trg_update_delivery_notes_updated_at
BEFORE UPDATE ON delivery_notes
FOR EACH ROW
EXECUTE FUNCTION update_delivery_notes_updated_at();

-- Funkcja do generowania numeru WZ na podstawie process_no
CREATE OR REPLACE FUNCTION generate_wz_number(p_order_id UUID)
RETURNS TEXT AS $$
DECLARE
    v_process_no TEXT;
    v_wz_number TEXT;
BEGIN
    -- Pobierz numer procesowy zamówienia
    SELECT process_no INTO v_process_no
    FROM orders
    WHERE id = p_order_id;

    IF v_process_no IS NULL THEN
        RAISE EXCEPTION 'Order not found with id: %', p_order_id;
    END IF;

    -- Wygeneruj numer WZ: WZ-{process_no}
    v_wz_number := 'WZ-' || v_process_no;

    RETURN v_wz_number;
END;
$$ LANGUAGE plpgsql;

-- Trigger do automatycznego generowania numeru WZ
CREATE OR REPLACE FUNCTION set_wz_number_before_insert()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.wz_number IS NULL OR LENGTH(NEW.wz_number) = 0 THEN
        NEW.wz_number := generate_wz_number(NEW.order_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_wz_number ON delivery_notes;
CREATE TRIGGER trg_set_wz_number
BEFORE INSERT ON delivery_notes
FOR EACH ROW
EXECUTE FUNCTION set_wz_number_before_insert();

-- Widok z pełnymi danymi WZ
CREATE OR REPLACE VIEW v_delivery_notes_full AS
SELECT
    dn.*,
    o.process_no,
    o.title AS order_title,
    o.customer_id,
    c.name AS customer_name,
    c.short_name AS customer_short_name
FROM delivery_notes dn
LEFT JOIN orders o ON o.id = dn.order_id
LEFT JOIN customers c ON c.id = o.customer_id;

-- Komentarze
COMMENT ON TABLE delivery_notes IS 'Dokumenty wydania zewnętrznego (WZ) dla zamówień';
COMMENT ON COLUMN delivery_notes.wz_number IS 'Numer WZ w formacie WZ-{process_no}';
COMMENT ON COLUMN delivery_notes.items IS 'JSON z pozycjami WZ';


-- ============================================
-- 3. Rozszerzenie tabeli quotations (jeśli nie istnieje)
-- ============================================

-- Sprawdź czy tabela quotations istnieje, jeśli nie - utwórz
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'quotations') THEN
        -- Tabela ofert
        CREATE TABLE quotations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            quote_no TEXT UNIQUE NOT NULL,
            customer_id UUID REFERENCES customers(id),
            title TEXT NOT NULL,
            status TEXT DEFAULT 'DRAFT',
            total_price NUMERIC(12,2) DEFAULT 0,
            cost_estimate NUMERIC(12,2) DEFAULT 0,
            margin_percent NUMERIC(5,2) DEFAULT 30,
            valid_until DATE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            converted_to_order UUID REFERENCES orders(id),
            notes TEXT
        );

        -- Pozycje oferty
        CREATE TABLE quotation_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            quotation_id UUID REFERENCES quotations(id) ON DELETE CASCADE,
            description TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            unit_price NUMERIC(10,2),
            total_price NUMERIC(12,2),
            material TEXT,
            processing_type TEXT,
            notes TEXT
        );

        -- Licznik numerów ofert
        CREATE TABLE quote_counters (
            year INTEGER PRIMARY KEY,
            last_no INTEGER DEFAULT 0
        );

        RAISE NOTICE 'Tabele quotations zostały utworzone';
    ELSE
        RAISE NOTICE 'Tabela quotations już istnieje';
    END IF;
END $$;


-- ============================================
-- 4. Uprawnienia (MVP - anon role)
-- ============================================

-- Attachments
GRANT SELECT, INSERT, UPDATE, DELETE ON attachments TO anon;
GRANT EXECUTE ON FUNCTION get_attachments_count TO anon;
GRANT EXECUTE ON FUNCTION get_attachments_total_size TO anon;

-- Delivery notes
GRANT SELECT, INSERT, UPDATE, DELETE ON delivery_notes TO anon;
GRANT EXECUTE ON FUNCTION generate_wz_number TO anon;
GRANT SELECT ON v_delivery_notes_full TO anon;

-- Quotations (jeśli utworzone)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'quotations') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON quotations TO anon;
        GRANT SELECT, INSERT, UPDATE, DELETE ON quotation_items TO anon;
        GRANT SELECT, UPDATE ON quote_counters TO anon;
    END IF;
END $$;


-- ============================================
-- 5. Row Level Security (RLS)
-- ============================================

-- Attachments RLS
ALTER TABLE attachments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS attachments_anon_all ON attachments;
CREATE POLICY attachments_anon_all ON attachments
    FOR ALL TO anon
    USING (true)
    WITH CHECK (true);

-- Delivery notes RLS
ALTER TABLE delivery_notes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS delivery_notes_anon_all ON delivery_notes;
CREATE POLICY delivery_notes_anon_all ON delivery_notes
    FOR ALL TO anon
    USING (true)
    WITH CHECK (true);

-- Quotations RLS (jeśli istnieją)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'quotations') THEN
        ALTER TABLE quotations ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS quotations_anon_all ON quotations;
        CREATE POLICY quotations_anon_all ON quotations
            FOR ALL TO anon USING (true) WITH CHECK (true);

        ALTER TABLE quotation_items ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS quotation_items_anon_all ON quotation_items;
        CREATE POLICY quotation_items_anon_all ON quotation_items
            FOR ALL TO anon USING (true) WITH CHECK (true);

        ALTER TABLE quote_counters ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS quote_counters_anon_all ON quote_counters;
        CREATE POLICY quote_counters_anon_all ON quote_counters
            FOR ALL TO anon USING (true) WITH CHECK (true);
    END IF;
END $$;


-- ============================================
-- 6. Weryfikacja
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '✅ Tabele attachments i delivery_notes zostały utworzone pomyślnie!';
    RAISE NOTICE '✅ Funkcje pomocnicze zostały dodane';
    RAISE NOTICE '✅ Triggery i widoki zostały skonfigurowane';
    RAISE NOTICE '✅ Uprawnienia dla roli anon zostały przyznane';
    RAISE NOTICE '';
    RAISE NOTICE '📋 Aby użyć, uruchom ten skrypt w Supabase SQL Editor';
END $$;
