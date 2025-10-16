-- ============================================
-- FIX dla problemu z dodawaniem danych do Supabase
-- Rozwiązanie ostrzeżeń SECURITY DEFINER
-- ============================================

-- 1. USUŃ SECURITY DEFINER z widoku v_customer_contacts
-- Widok będzie działał z uprawnieniami użytkownika, nie twórcy
DROP VIEW IF EXISTS v_customer_contacts;
CREATE VIEW v_customer_contacts
SECURITY INVOKER  -- Używa uprawnień użytkownika, nie twórcy widoku
AS
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

-- 2. To samo dla v_customer_statistics
DROP VIEW IF EXISTS v_customer_statistics;
CREATE VIEW v_customer_statistics
SECURITY INVOKER  -- Używa uprawnień użytkownika
AS
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

-- 3. Upewnij się, że uprawnienia są prawidłowe
GRANT SELECT, INSERT, UPDATE, DELETE ON customers TO anon;
GRANT SELECT ON v_customer_statistics TO anon;
GRANT SELECT ON v_customer_contacts TO anon;
GRANT EXECUTE ON FUNCTION search_customers TO anon;
GRANT EXECUTE ON FUNCTION validate_nip TO anon;
GRANT EXECUTE ON FUNCTION validate_regon TO anon;

-- 4. Sprawdź i napraw politykę RLS
DROP POLICY IF EXISTS customers_anon_all ON customers;
CREATE POLICY customers_anon_all ON customers
    FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);

-- 5. OPCJONALNIE: Wyłącz walidację NIP/REGON jeśli powoduje problemy
-- (Odkomentuj poniższe linie jeśli walidacja blokuje dodawanie)

-- DROP TRIGGER IF EXISTS trg_validate_customer_tax_numbers ON customers;

-- Możesz też zmienić trigger, aby był mniej restrykcyjny:
-- CREATE OR REPLACE FUNCTION validate_customer_tax_numbers()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     -- Tylko ostrzeżenie zamiast błędu
--     IF NEW.customer_type = 'company' AND NEW.nip IS NOT NULL AND NEW.nip != '' THEN
--         IF NOT validate_nip(NEW.nip) THEN
--             RAISE WARNING 'Nieprawidłowy NIP: %', NEW.nip;
--             -- Nie blokuj operacji
--         END IF;
--     END IF;
--
--     RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql;

-- 6. Sprawdź czy są inne blokujące triggery
SELECT
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement
FROM information_schema.triggers
WHERE event_object_table = 'customers';

-- 7. Sprawdź aktywne polityki RLS
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE tablename = 'customers';

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Widoki zostały poprawione - używają teraz SECURITY INVOKER';
    RAISE NOTICE 'Uprawnienia i polityki RLS zostały zaktualizowane';
END $$;
