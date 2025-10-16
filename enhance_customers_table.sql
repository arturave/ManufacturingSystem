-- ============================================
-- Enhanced Customer Table Structure
-- Adds new fields for complete customer management
-- ============================================

-- First, backup existing customers table if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'customers') THEN
        -- Create backup table
        CREATE TABLE IF NOT EXISTS customers_backup AS SELECT * FROM customers;
        RAISE NOTICE 'Backup of customers table created as customers_backup';
    END IF;
END $$;

-- Drop existing customers table (CASCADE will handle dependencies)
DROP TABLE IF EXISTS customers CASCADE;

-- Create enhanced customers table with all business fields
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Basic company information
    name TEXT NOT NULL,                    -- Pełna nazwa firmy
    short_name TEXT,                       -- Nazwa skrócona
    customer_type TEXT DEFAULT 'company',  -- company/individual
    
    -- Tax/Registration numbers
    nip TEXT UNIQUE,                       -- NIP (Tax ID)
    regon TEXT,                            -- REGON (Business Registry)
    krs TEXT,                              -- KRS (Court Registry)
    
    -- Main contact information
    email TEXT,                            -- Główny email firmy
    phone TEXT,                            -- Główny telefon
    website TEXT,                          -- Strona WWW
    
    -- Address
    address TEXT,                          -- Ulica i numer
    city TEXT,                             -- Miasto
    postal_code TEXT,                      -- Kod pocztowy
    country TEXT DEFAULT 'Polska',         -- Kraj
    
    -- Contact person
    contact_person TEXT,                   -- Imię i nazwisko osoby kontaktowej
    contact_position TEXT,                 -- Stanowisko
    contact_phone TEXT,                    -- Telefon bezpośredni
    contact_email TEXT,                    -- Email bezpośredni
    
    -- Financial information
    credit_limit NUMERIC(12,2) DEFAULT 0,  -- Limit kredytowy
    payment_terms INTEGER DEFAULT 14,      -- Termin płatności w dniach
    discount_percent NUMERIC(5,2) DEFAULT 0, -- Stały rabat
    
    -- Additional information
    notes TEXT,                            -- Uwagi
    tags TEXT[],                           -- Tagi (array)
    is_active BOOLEAN DEFAULT TRUE,        -- Czy aktywny
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by TEXT,
    updated_by TEXT,
    
    -- Constraints
    CONSTRAINT check_email_format CHECK (email IS NULL OR email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT check_contact_email_format CHECK (contact_email IS NULL OR contact_email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT check_customer_type CHECK (customer_type IN ('company', 'individual')),
    CONSTRAINT check_payment_terms CHECK (payment_terms >= 0),
    CONSTRAINT check_credit_limit CHECK (credit_limit >= 0)
);

-- Create indexes for better performance
CREATE INDEX idx_customers_name ON customers(name);
CREATE INDEX idx_customers_nip ON customers(nip);
CREATE INDEX idx_customers_city ON customers(city);
CREATE INDEX idx_customers_is_active ON customers(is_active);
CREATE INDEX idx_customers_tags ON customers USING gin(tags);
CREATE INDEX idx_customers_search ON customers USING gin(
    to_tsvector('simple', coalesce(name, '') || ' ' || 
                          coalesce(short_name, '') || ' ' || 
                          coalesce(nip, '') || ' ' || 
                          coalesce(email, '') || ' ' ||
                          coalesce(contact_person, ''))
);

-- Function to validate Polish NIP
CREATE OR REPLACE FUNCTION validate_nip(nip_number TEXT) 
RETURNS BOOLEAN AS $$
DECLARE
    cleaned_nip TEXT;
    weights INTEGER[] := ARRAY[6, 5, 7, 2, 3, 4, 5, 6, 7];
    checksum INTEGER := 0;
    i INTEGER;
BEGIN
    -- Clean NIP (remove dashes and spaces)
    cleaned_nip := REPLACE(REPLACE(nip_number, '-', ''), ' ', '');
    
    -- Check length
    IF LENGTH(cleaned_nip) != 10 THEN
        RETURN FALSE;
    END IF;
    
    -- Check if all characters are digits
    IF cleaned_nip !~ '^[0-9]+$' THEN
        RETURN FALSE;
    END IF;
    
    -- Calculate checksum
    FOR i IN 1..9 LOOP
        checksum := checksum + (CAST(SUBSTR(cleaned_nip, i, 1) AS INTEGER) * weights[i]);
    END LOOP;
    
    -- Verify checksum
    RETURN (checksum % 11) % 10 = CAST(SUBSTR(cleaned_nip, 10, 1) AS INTEGER);
END;
$$ LANGUAGE plpgsql;

-- Function to validate Polish REGON
CREATE OR REPLACE FUNCTION validate_regon(regon_number TEXT) 
RETURNS BOOLEAN AS $$
DECLARE
    cleaned_regon TEXT;
    weights9 INTEGER[] := ARRAY[8, 9, 2, 3, 4, 5, 6, 7];
    weights14 INTEGER[] := ARRAY[2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8];
    checksum INTEGER := 0;
    i INTEGER;
BEGIN
    -- Clean REGON
    cleaned_regon := REPLACE(REPLACE(regon_number, '-', ''), ' ', '');
    
    -- Check length (9 or 14 digits)
    IF LENGTH(cleaned_regon) NOT IN (9, 14) THEN
        RETURN FALSE;
    END IF;
    
    -- Check if all characters are digits
    IF cleaned_regon !~ '^[0-9]+$' THEN
        RETURN FALSE;
    END IF;
    
    IF LENGTH(cleaned_regon) = 9 THEN
        -- 9-digit REGON
        FOR i IN 1..8 LOOP
            checksum := checksum + (CAST(SUBSTR(cleaned_regon, i, 1) AS INTEGER) * weights9[i]);
        END LOOP;
        RETURN checksum % 11 = CAST(SUBSTR(cleaned_regon, 9, 1) AS INTEGER);
    ELSE
        -- 14-digit REGON
        FOR i IN 1..13 LOOP
            checksum := checksum + (CAST(SUBSTR(cleaned_regon, i, 1) AS INTEGER) * weights14[i]);
        END LOOP;
        RETURN checksum % 11 = CAST(SUBSTR(cleaned_regon, 14, 1) AS INTEGER);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_customer_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_customer_updated_at ON customers;
CREATE TRIGGER trg_update_customer_updated_at
BEFORE UPDATE ON customers
FOR EACH ROW
EXECUTE FUNCTION update_customer_updated_at();

-- Trigger to validate NIP and REGON before insert/update
CREATE OR REPLACE FUNCTION validate_customer_tax_numbers()
RETURNS TRIGGER AS $$
BEGIN
    -- Validate NIP if provided and customer is a company
    IF NEW.customer_type = 'company' AND NEW.nip IS NOT NULL AND NEW.nip != '' THEN
        IF NOT validate_nip(NEW.nip) THEN
            RAISE EXCEPTION 'Invalid NIP number: %', NEW.nip;
        END IF;
    END IF;
    
    -- Validate REGON if provided
    IF NEW.regon IS NOT NULL AND NEW.regon != '' THEN
        IF NOT validate_regon(NEW.regon) THEN
            RAISE EXCEPTION 'Invalid REGON number: %', NEW.regon;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validate_customer_tax_numbers ON customers;
CREATE TRIGGER trg_validate_customer_tax_numbers
BEFORE INSERT OR UPDATE ON customers
FOR EACH ROW
EXECUTE FUNCTION validate_customer_tax_numbers();

-- View for customer statistics
CREATE OR REPLACE VIEW v_customer_statistics AS
SELECT 
    c.id,
    c.name,
    c.short_name,
    COUNT(DISTINCT o.id) AS order_count,
    COALESCE(SUM(o.price_pln), 0) AS total_revenue,
    COALESCE(AVG(o.price_pln), 0) AS avg_order_value,
    MAX(o.created_at) AS last_order_date,
    c.credit_limit,
    COALESCE(SUM(CASE WHEN o.status != 'INVOICED' THEN o.price_pln ELSE 0 END), 0) AS outstanding_amount,
    c.is_active
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
GROUP BY c.id, c.name, c.short_name, c.credit_limit, c.is_active;

-- View for customer contact list
CREATE OR REPLACE VIEW v_customer_contacts AS
SELECT 
    c.id,
    c.name,
    c.short_name,
    c.nip,
    c.email AS company_email,
    c.phone AS company_phone,
    c.contact_person,
    c.contact_position,
    c.contact_email,
    c.contact_phone,
    c.city,
    c.is_active
FROM customers c
WHERE c.is_active = TRUE
ORDER BY c.name;

-- Function to search customers
CREATE OR REPLACE FUNCTION search_customers(
    search_term TEXT DEFAULT NULL,
    search_city TEXT DEFAULT NULL,
    search_nip TEXT DEFAULT NULL,
    include_inactive BOOLEAN DEFAULT FALSE
)
RETURNS TABLE(
    id UUID,
    name TEXT,
    short_name TEXT,
    nip TEXT,
    city TEXT,
    email TEXT,
    contact_person TEXT,
    is_active BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.name,
        c.short_name,
        c.nip,
        c.city,
        c.email,
        c.contact_person,
        c.is_active
    FROM customers c
    WHERE 
        (include_inactive OR c.is_active = TRUE)
        AND (search_term IS NULL OR (
            c.name ILIKE '%' || search_term || '%' OR
            c.short_name ILIKE '%' || search_term || '%' OR
            c.email ILIKE '%' || search_term || '%' OR
            c.contact_person ILIKE '%' || search_term || '%'
        ))
        AND (search_city IS NULL OR c.city ILIKE '%' || search_city || '%')
        AND (search_nip IS NULL OR c.nip ILIKE '%' || search_nip || '%')
    ORDER BY c.name;
END;
$$ LANGUAGE plpgsql;

-- Update orders table to work with new customer structure
-- (This assumes orders table exists as per original schema)

-- Migration: Restore data from backup if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'customers_backup') THEN
        -- Insert old data into new structure
        INSERT INTO customers (id, name, email, phone, created_at)
        SELECT 
            id,
            name,
            CASE WHEN contact ~ '@' THEN contact ELSE NULL END as email,
            CASE WHEN contact !~ '@' THEN contact ELSE NULL END as phone,
            created_at
        FROM customers_backup
        ON CONFLICT (id) DO NOTHING;
        
        RAISE NOTICE 'Data migrated from customers_backup';
    END IF;
END $$;

-- Sample data for testing (only if table is empty)
INSERT INTO customers (
    name, short_name, nip, regon, krs, email, phone, website,
    address, city, postal_code, contact_person, contact_position,
    contact_phone, contact_email, credit_limit, payment_terms, notes
)
SELECT * FROM (VALUES
    ('Przykładowa Firma Sp. z o.o.', 'Przykładowa', '5252248481', '140517018', '0000123456', 
     'biuro@przykladowa.pl', '+48 22 123 45 67', 'www.przykladowa.pl',
     'ul. Przemysłowa 10', 'Warszawa', '00-001', 'Jan Kowalski', 'Kierownik Zakupów',
     '+48 501 234 567', 'j.kowalski@przykladowa.pl', 50000.00, 30, 'Klient strategiczny'),
    
    ('Metalex Industries S.A.', 'Metalex', '7811767696', '273339110', '0000234567',
     'info@metalex.com', '+48 12 345 67 89', 'www.metalex.com',
     'ul. Stalowa 25', 'Kraków', '30-002', 'Anna Nowak', 'Dyrektor Handlowy',
     '+48 502 345 678', 'a.nowak@metalex.com', 100000.00, 14, 'Partner od 2020'),
    
    ('TechCut Solutions', 'TechCut', '9542742927', '364425570', NULL,
     'orders@techcut.eu', '+48 71 234 56 78', 'www.techcut.eu',
     'ul. Technologiczna 15', 'Wrocław', '50-003', 'Piotr Wiśniewski', 'Specjalista ds. Zakupów',
     '+48 503 456 789', 'p.wisniewski@techcut.eu', 25000.00, 21, NULL)
) AS v(name, short_name, nip, regon, krs, email, phone, website,
       address, city, postal_code, contact_person, contact_position,
       contact_phone, contact_email, credit_limit, payment_terms, notes)
WHERE NOT EXISTS (SELECT 1 FROM customers LIMIT 1);

-- Grant permissions for anon role (MVP)
GRANT SELECT, INSERT, UPDATE, DELETE ON customers TO anon;
GRANT SELECT ON v_customer_statistics TO anon;
GRANT SELECT ON v_customer_contacts TO anon;
GRANT EXECUTE ON FUNCTION search_customers TO anon;
GRANT EXECUTE ON FUNCTION validate_nip TO anon;
GRANT EXECUTE ON FUNCTION validate_regon TO anon;

-- Enable RLS
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;

-- Create permissive policy for MVP (anon role)
DROP POLICY IF EXISTS customers_anon_all ON customers;
CREATE POLICY customers_anon_all ON customers
    FOR ALL 
    TO anon
    USING (true)
    WITH CHECK (true);

-- For production, you would create more restrictive policies:
-- CREATE POLICY customers_authenticated ON customers
--     FOR ALL
--     TO authenticated
--     USING (auth.uid() IS NOT NULL)
--     WITH CHECK (auth.uid() IS NOT NULL);

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Enhanced customers table created successfully with all new fields!';
END $$;
