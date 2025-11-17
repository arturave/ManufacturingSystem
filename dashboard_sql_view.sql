-- =====================================================
-- KROK 1: Usuń stary widok (jeśli istnieje)
-- =====================================================
DROP VIEW IF EXISTS v_orders_sla CASCADE;

-- =====================================================
-- KROK 2: Utwórz nowy widok v_orders_sla
-- =====================================================
CREATE VIEW v_orders_sla AS
SELECT
    -- Podstawowe informacje
    o.id AS order_id,
    o.process_no AS order_number,
    o.title AS order_name,
    o.status,
    o.price_pln,

    -- Klient
    c.name AS customer_name,
    c.short_name AS customer_short,

    -- Daty
    o.created_at,
    o.received_at,
    o.planned_at AS target_date,
    o.finished_at AS completion_date,

    -- Obliczenia dni
    EXTRACT(DAY FROM (CURRENT_TIMESTAMP - o.created_at)) AS days_in_progress,

    -- Status SLA
    CASE
        WHEN o.status = 'DONE' THEN 'Zakończone'
        WHEN o.status = 'INVOICED' THEN 'Wyfakturowane'
        WHEN o.status = 'RECEIVED' THEN 'Wpłynęło'
        WHEN o.status = 'CONFIRMED' THEN 'Potwierdzone'
        WHEN o.status = 'PLANNED' THEN 'Zaplanowane'
        WHEN o.status = 'IN_PROGRESS' THEN 'W realizacji'
        ELSE 'Nieznany status'
    END AS sla_status,

    -- Flagi
    CASE
        WHEN o.planned_at IS NOT NULL
             AND o.planned_at < CURRENT_DATE
             AND o.status NOT IN ('DONE', 'INVOICED')
        THEN true
        ELSE false
    END AS is_overdue,

    CASE
        WHEN o.planned_at IS NOT NULL
             AND o.planned_at <= CURRENT_DATE + INTERVAL '7 days'
             AND o.status NOT IN ('DONE', 'INVOICED')
        THEN true
        ELSE false
    END AS is_urgent,

    -- Notatki
    o.notes

FROM orders o
LEFT JOIN customers c ON o.customer_id = c.id;

-- =====================================================
-- KROK 3: Przyznaj uprawnienia
-- =====================================================
GRANT SELECT ON v_orders_sla TO authenticated;
GRANT SELECT ON v_orders_sla TO anon;

-- =====================================================
-- KROK 4: Dodaj komentarz
-- =====================================================
COMMENT ON VIEW v_orders_sla IS 'Widok do monitorowania SLA zamówień';