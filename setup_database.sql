-- ============================================
-- KOMPLETNY SKRYPT SETUP DLA BAZY DANYCH
-- System Zarządzania Produkcją - Laser/Prasa
-- Wykonaj w Supabase SQL Editor
-- ============================================

-- 1. ENUM dla statusów
DROP TYPE IF EXISTS order_status CASCADE;
CREATE TYPE order_status AS ENUM (
    'RECEIVED',     -- Wpłynęło
    'CONFIRMED',    -- Potwierdzono
    'PLANNED',      -- Na planie
    'IN_PROGRESS',  -- W realizacji
    'DONE',         -- Gotowe
    'INVOICED'      -- Wyfakturowane
);

-- 2. TABELA: Klienci
DROP TABLE IF EXISTS customers CASCADE;
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    contact TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. TABELA: Zamówienia
DROP TABLE IF EXISTS orders CASCADE;
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    process_no TEXT UNIQUE NOT NULL,
    customer_id UUID REFERENCES customers(id),
    title TEXT NOT NULL,
    status order_status NOT NULL DEFAULT 'RECEIVED',
    price_pln NUMERIC(12,2) DEFAULT 0,
    received_at DATE DEFAULT CURRENT_DATE,
    planned_at DATE,
    finished_at DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indeksy dla wydajności
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_dates ON orders(received_at, planned_at);

-- 4. TABELA: Części/Detale
DROP TABLE IF EXISTS parts CASCADE;
CREATE TABLE parts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    idx_code TEXT,
    name TEXT NOT NULL,
    material TEXT,
    thickness_mm NUMERIC(6,2),
    qty INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(order_id, name)  -- Unikalność nazwy w ramach zamówienia
);

CREATE INDEX idx_parts_order ON parts(order_id);

-- 5. TABELA: Pliki załączników
DROP TABLE IF EXISTS files CASCADE;
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    part_id UUID REFERENCES parts(id) ON DELETE CASCADE,
    kind TEXT,  -- typ pliku (dxf, dwg, pdf, etc.)
    storage_path TEXT NOT NULL,
    original_name TEXT,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_files_order ON files(order_id);
CREATE INDEX idx_files_part ON files(part_id);

-- 6. TABELA: Historia zmian statusów
DROP TABLE IF EXISTS order_status_history CASCADE;
CREATE TABLE order_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    old_status order_status,
    new_status order_status,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    changed_by TEXT  -- może przechowywać user_id lub nazwę użytkownika
);

CREATE INDEX idx_history_order ON order_status_history(order_id);

-- 7. TABELA: Liczniki numerów procesowych
DROP TABLE IF EXISTS process_counters CASCADE;
CREATE TABLE process_counters (
    year INTEGER PRIMARY KEY,
    last_no INTEGER NOT NULL DEFAULT 0
);

-- 8. FUNKCJA: Generowanie kolejnego numeru procesowego
CREATE OR REPLACE FUNCTION next_process_no_fn(p_date DATE DEFAULT NOW()::DATE)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_year INTEGER;
    v_next_no INTEGER;
BEGIN
    -- Pobierz rok z daty
    v_year := EXTRACT(YEAR FROM p_date);
    
    -- Wstaw rok jeśli nie istnieje
    INSERT INTO process_counters(year, last_no) 
    VALUES (v_year, 0)
    ON CONFLICT (year) DO NOTHING;
    
    -- Zwiększ licznik i pobierz nową wartość
    UPDATE process_counters 
    SET last_no = last_no + 1
    WHERE year = v_year
    RETURNING last_no INTO v_next_no;
    
    -- Zwróć sformatowany numer: YYYY-00001
    RETURN v_year::TEXT || '-' || LPAD(v_next_no::TEXT, 5, '0');
END;
$$;

-- Ustaw właściciela funkcji
ALTER FUNCTION next_process_no_fn(DATE) OWNER TO postgres;

-- 9. TRIGGER: Automatyczne nadawanie numeru procesowego
CREATE OR REPLACE FUNCTION set_process_no_before_insert()
RETURNS TRIGGER 
LANGUAGE plpgsql 
AS $$
BEGIN
    -- Nadaj numer tylko jeśli nie został podany
    IF NEW.process_no IS NULL OR LENGTH(NEW.process_no) = 0 THEN
        NEW.process_no := next_process_no_fn(COALESCE(NEW.received_at, NOW()::DATE));
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_set_process_no ON orders;
CREATE TRIGGER trg_set_process_no
BEFORE INSERT ON orders
FOR EACH ROW
EXECUTE FUNCTION set_process_no_before_insert();

-- 10. TRIGGER: Logowanie zmian statusu
CREATE OR REPLACE FUNCTION log_order_status_change()
RETURNS TRIGGER 
LANGUAGE plpgsql 
AS $$
BEGIN
    -- Loguj tylko gdy status się zmienił
    IF TG_OP = 'UPDATE' AND NEW.status IS DISTINCT FROM OLD.status THEN
        INSERT INTO order_status_history(
            order_id, 
            old_status, 
            new_status, 
            changed_by
        )
        VALUES (
            OLD.id, 
            OLD.status, 
            NEW.status, 
            COALESCE(current_setting('request.jwt.claims', true)::json->>'email', 'system')
        );
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_log_order_status ON orders;
CREATE TRIGGER trg_log_order_status
AFTER UPDATE ON orders
FOR EACH ROW
EXECUTE FUNCTION log_order_status_change();

-- 11. WIDOK: Zamówienia z nazwami klientów
CREATE OR REPLACE VIEW v_orders_full AS
SELECT 
    o.*,
    c.name AS customer_name,
    c.contact AS customer_contact
FROM orders o
LEFT JOIN customers c ON c.id = o.customer_id;

-- 12. WIDOK: Liczba zamówień wg statusów
CREATE OR REPLACE VIEW v_orders_status_counts AS
SELECT 
    status,
    COUNT(*) AS cnt
FROM orders
GROUP BY status;

-- 13. WIDOK: Dashboard SLA (terminy)
CREATE OR REPLACE VIEW v_orders_sla AS
SELECT
    o.id,
    o.process_no,
    o.title,
    o.status,
    o.planned_at,
    o.finished_at,
    c.name AS customer_name,
    -- Dni do terminu (ujemne = przeterminowane)
    (o.planned_at - CURRENT_DATE) AS days_to_deadline,
    -- Czy przeterminowane
    CASE 
        WHEN o.planned_at IS NOT NULL 
             AND o.finished_at IS NULL 
             AND o.planned_at < CURRENT_DATE
        THEN TRUE 
        ELSE FALSE 
    END AS overdue,
    -- Kategoria SLA
    CASE
        WHEN o.finished_at IS NOT NULL THEN 'COMPLETED'
        WHEN o.planned_at IS NULL THEN 'NO_DEADLINE'
        WHEN o.planned_at < CURRENT_DATE THEN 'OVERDUE'
        WHEN o.planned_at - CURRENT_DATE <= 2 THEN 'URGENT'
        ELSE 'ON_TIME'
    END AS sla_category
FROM orders o
LEFT JOIN customers c ON c.id = o.customer_id;

-- 14. WIDOK: Statystyki miesięczne
CREATE OR REPLACE VIEW v_monthly_stats AS
SELECT 
    TO_CHAR(received_at, 'YYYY-MM') AS month,
    COUNT(*) AS order_count,
    SUM(price_pln) AS total_revenue,
    AVG(price_pln) AS avg_price,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM orders
WHERE received_at IS NOT NULL
GROUP BY TO_CHAR(received_at, 'YYYY-MM')
ORDER BY month DESC;

-- 15. RLS (Row Level Security) - MVP z dostępem anon
-- UWAGA: Dla produkcji zmień na authenticated!

-- Włącz RLS dla wszystkich tabel
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE parts ENABLE ROW LEVEL SECURITY;
ALTER TABLE files ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_status_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE process_counters ENABLE ROW LEVEL SECURITY;

-- Polityki dla roli 'anon' (MVP - desktop bez autoryzacji)
-- CUSTOMERS
DROP POLICY IF EXISTS customers_anon_all ON customers;
CREATE POLICY customers_anon_all ON customers
    FOR ALL 
    TO anon
    USING (true)
    WITH CHECK (true);

-- ORDERS
DROP POLICY IF EXISTS orders_anon_all ON orders;
CREATE POLICY orders_anon_all ON orders
    FOR ALL 
    TO anon
    USING (true)
    WITH CHECK (true);

-- PARTS
DROP POLICY IF EXISTS parts_anon_all ON parts;
CREATE POLICY parts_anon_all ON parts
    FOR ALL 
    TO anon
    USING (true)
    WITH CHECK (true);

-- FILES
DROP POLICY IF EXISTS files_anon_all ON files;
CREATE POLICY files_anon_all ON files
    FOR ALL 
    TO anon
    USING (true)
    WITH CHECK (true);

-- ORDER_STATUS_HISTORY
DROP POLICY IF EXISTS history_anon_all ON order_status_history;
CREATE POLICY history_anon_all ON order_status_history
    FOR ALL 
    TO anon
    USING (true)
    WITH CHECK (true);

-- PROCESS_COUNTERS
DROP POLICY IF EXISTS counters_anon_all ON process_counters;
CREATE POLICY counters_anon_all ON process_counters
    FOR ALL 
    TO anon
    USING (true)
    WITH CHECK (true);

-- 16. GRANT dostęp do widoków
GRANT SELECT ON v_orders_full TO anon;
GRANT SELECT ON v_orders_status_counts TO anon;
GRANT SELECT ON v_orders_sla TO anon;
GRANT SELECT ON v_monthly_stats TO anon;

-- 17. GRANT wykonywanie funkcji
GRANT EXECUTE ON FUNCTION next_process_no_fn(DATE) TO anon;

-- ============================================
-- STORAGE BUCKET - Wykonaj osobno w Storage
-- ============================================
-- 1. Utwórz bucket 'attachments' w Supabase Dashboard -> Storage
-- 2. Następnie wykonaj poniższe polityki w SQL Editor:

/*
-- Polityki dla Storage (bucket: attachments) - wersja MVP z anon
INSERT INTO storage.policies (bucket_id, name, definition, operation)
VALUES 
    ('attachments', 'attachments_read_anon', 
     '{"roles": ["anon"], "condition": {"bucket_id": "attachments"}}', 'SELECT'),
    ('attachments', 'attachments_write_anon', 
     '{"roles": ["anon"], "condition": {"bucket_id": "attachments"}}', 'INSERT'),
    ('attachments', 'attachments_delete_anon', 
     '{"roles": ["anon"], "condition": {"bucket_id": "attachments"}}', 'DELETE')
ON CONFLICT DO NOTHING;
*/

-- ============================================
-- DANE TESTOWE (opcjonalnie)
-- ============================================

-- Dodaj przykładowych klientów
INSERT INTO customers (name, contact) VALUES 
    ('Firma ABC Sp. z o.o.', 'kontakt@abc.pl'),
    ('XYZ Manufacturing', 'info@xyz.com'),
    ('Zakład Produkcyjny OMEGA', 'biuro@omega.pl'),
    ('TechMetal Solutions', 'zamowienia@techmetal.com'),
    ('Precision Cutting Ltd.', 'orders@precision.eu')
ON CONFLICT (name) DO NOTHING;

-- Dodaj przykładowe zamówienia
DO $$
DECLARE
    v_customer_id UUID;
BEGIN
    -- Pobierz ID pierwszego klienta
    SELECT id INTO v_customer_id FROM customers LIMIT 1;
    
    IF v_customer_id IS NOT NULL THEN
        INSERT INTO orders (customer_id, title, status, price_pln, received_at, planned_at)
        VALUES 
            (v_customer_id, 'Elementy konstrukcyjne - partia A', 'IN_PROGRESS', 5500.00, 
             CURRENT_DATE - INTERVAL '5 days', CURRENT_DATE + INTERVAL '2 days'),
            (v_customer_id, 'Blachy perforowane 2mm', 'PLANNED', 3200.00, 
             CURRENT_DATE - INTERVAL '3 days', CURRENT_DATE + INTERVAL '5 days'),
            (v_customer_id, 'Obudowy stalowe - prototyp', 'RECEIVED', 8900.00, 
             CURRENT_DATE, CURRENT_DATE + INTERVAL '10 days');
    END IF;
END $$;

-- ============================================
-- INSTRUKCJA PO WYKONANIU SKRYPTU
-- ============================================
-- 1. Przejdź do Storage -> New bucket -> Nazwa: 'attachments'
-- 2. Ustaw bucket jako Public jeśli chcesz łatwy dostęp
-- 3. Skopiuj URL i klucz API z Settings -> API
-- 4. Utwórz plik .env w projekcie z danymi dostępu
-- 5. Uruchom aplikację: python mfg_app.py

-- Koniec skryptu
