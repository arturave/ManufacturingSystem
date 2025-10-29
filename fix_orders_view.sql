-- ============================================
-- FIX: Widok v_orders_full - naprawa kolumn customers
-- Problem: Widok odwołuje się do nieistniejącej kolumny c.contact
-- Rozwiązanie: Użycie nowych kolumn z rozszerzonej tabeli customers
-- ============================================

-- Usuń stary widok
DROP VIEW IF EXISTS v_orders_full CASCADE;

-- Utwórz poprawiony widok z nowymi kolumnami z tabeli customers
CREATE OR REPLACE VIEW v_orders_full AS
SELECT
    o.*,
    c.name AS customer_name,
    c.short_name AS customer_short_name,
    c.nip AS customer_nip,
    c.email AS customer_email,
    c.phone AS customer_phone,
    c.contact_person AS customer_contact_person,
    c.contact_email AS customer_contact_email,
    c.contact_phone AS customer_contact_phone,
    c.city AS customer_city,
    c.address AS customer_address,
    c.postal_code AS customer_postal_code
FROM orders o
LEFT JOIN customers c ON c.id = o.customer_id;

-- Przyznaj uprawnienia dla roli anon (MVP)
GRANT SELECT ON v_orders_full TO anon;

-- Dodaj komentarz do widoku
COMMENT ON VIEW v_orders_full IS 'Widok zamówień z pełnymi danymi klientów (po rozszerzeniu tabeli customers)';

-- Sprawdź czy widok działa poprawnie
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count FROM v_orders_full;
    RAISE NOTICE 'Widok v_orders_full naprawiony. Znaleziono % zamówień.', v_count;
END $$;
