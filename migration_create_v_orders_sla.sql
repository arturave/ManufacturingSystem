-- =====================================================
-- Widok v_orders_sla dla monitorowania SLA zamówień
-- =====================================================
-- Autor: System Manufacturing
-- Data: 2025-11-17
-- Opis: Widok do analizy czasów realizacji i statusów
-- =====================================================

-- Usuń widok jeśli istnieje
DROP VIEW IF EXISTS v_orders_sla CASCADE;

-- Utwórz widok v_orders_sla
CREATE VIEW v_orders_sla AS
SELECT
    -- Podstawowe informacje o zamówieniu
    o.id AS order_id,
    o.process_no AS order_number,
    o.title AS order_name,
    o.status,
    o.price_pln,

    -- Klient
    c.name AS customer_name,
    c.short_name AS customer_short,

    -- Daty i czasy
    o.created_at,
    o.received_at,
    o.planned_at AS target_date,
    o.finished_at AS completion_date,

    -- Obliczenia SLA (w dniach)
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - o.created_at)) / 86400 AS days_in_progress,
    CASE
        WHEN o.planned_at IS NOT NULL THEN
            EXTRACT(EPOCH FROM (o.planned_at::timestamp - o.created_at)) / 86400
        ELSE NULL
    END AS days_to_target,
    CASE
        WHEN o.finished_at IS NOT NULL THEN
            EXTRACT(EPOCH FROM (o.finished_at::timestamp - o.created_at)) / 86400
        ELSE NULL
    END AS days_to_completion,

    -- Status realizacji
    CASE
        WHEN o.status = 'DONE' THEN 'Zakończone'
        WHEN o.status = 'INVOICED' THEN 'Wyfakturowane'
        WHEN o.status = 'RECEIVED' THEN 'Wpłynęło'
        WHEN o.status = 'CONFIRMED' THEN 'Potwierdzone'
        WHEN o.status = 'PLANNED' THEN 'Zaplanowane'
        WHEN o.status = 'IN_PROGRESS' THEN 'W realizacji'
        WHEN o.planned_at IS NULL THEN 'Brak terminu'
        WHEN o.planned_at < CURRENT_DATE THEN 'Po terminie'
        WHEN o.planned_at = CURRENT_DATE THEN 'Dziś'
        WHEN o.planned_at <= CURRENT_DATE + INTERVAL '3 days' THEN 'Pilne (3 dni)'
        WHEN o.planned_at <= CURRENT_DATE + INTERVAL '7 days' THEN 'W tym tygodniu'
        ELSE 'W terminie'
    END AS sla_status,

    -- Dni do/po terminie
    CASE
        WHEN o.planned_at IS NOT NULL AND o.status NOT IN ('DONE', 'INVOICED') THEN
            EXTRACT(EPOCH FROM (o.planned_at::timestamp - CURRENT_DATE::timestamp)) / 86400
        ELSE NULL
    END AS days_remaining,

    -- Wskaźniki opóźnienia
    CASE
        WHEN o.planned_at IS NOT NULL
             AND o.finished_at IS NOT NULL
             AND o.finished_at > o.planned_at THEN
            EXTRACT(EPOCH FROM (o.finished_at::timestamp - o.planned_at::timestamp)) / 86400
        WHEN o.planned_at IS NOT NULL
             AND o.finished_at IS NULL
             AND CURRENT_DATE > o.planned_at
             AND o.status NOT IN ('DONE', 'INVOICED') THEN
            EXTRACT(EPOCH FROM (CURRENT_DATE::timestamp - o.planned_at::timestamp)) / 86400
        ELSE 0
    END AS days_overdue,

    -- Wskaźnik statusu (dla sortowania)
    CASE o.status
        WHEN 'RECEIVED' THEN 1
        WHEN 'CONFIRMED' THEN 2
        WHEN 'PLANNED' THEN 3
        WHEN 'IN_PROGRESS' THEN 4
        WHEN 'DONE' THEN 5
        WHEN 'INVOICED' THEN 6
        ELSE 7
    END AS status_order,

    -- Dodatkowe informacje
    o.notes,

    -- Liczba części
    COALESCE(
        (SELECT COUNT(*)
         FROM parts p
         WHERE p.order_id = o.id),
        0
    ) AS parts_count,

    -- Liczba pozycji zamówienia (order_items)
    COALESCE(
        (SELECT COUNT(*)
         FROM order_items oi
         WHERE oi.order_id = o.id),
        0
    ) AS order_items_count,

    -- Flagi
    CASE
        WHEN o.planned_at IS NOT NULL
             AND o.planned_at < CURRENT_DATE
             AND o.status NOT IN ('DONE', 'INVOICED') THEN true
        ELSE false
    END AS is_overdue,

    CASE
        WHEN o.planned_at IS NOT NULL
             AND o.planned_at <= CURRENT_DATE + INTERVAL '7 days'
             AND o.status NOT IN ('DONE', 'INVOICED') THEN true
        ELSE false
    END AS is_urgent

FROM
    orders o
    LEFT JOIN customers c ON o.customer_id = c.id;

-- Przyznaj uprawnienia
GRANT SELECT ON v_orders_sla TO authenticated;
GRANT SELECT ON v_orders_sla TO anon;

-- Komentarz do widoku
COMMENT ON VIEW v_orders_sla IS 'Widok do monitorowania SLA i terminów realizacji zamówień';

-- Komentarze do kolumn
COMMENT ON COLUMN v_orders_sla.order_id IS 'ID zamówienia';
COMMENT ON COLUMN v_orders_sla.order_number IS 'Numer procesu (process_no)';
COMMENT ON COLUMN v_orders_sla.order_name IS 'Tytuł zamówienia';
COMMENT ON COLUMN v_orders_sla.sla_status IS 'Status realizacji względem terminu';
COMMENT ON COLUMN v_orders_sla.days_remaining IS 'Dni pozostałe do terminu (ujemne = po terminie)';
COMMENT ON COLUMN v_orders_sla.days_overdue IS 'Dni opóźnienia względem terminu docelowego';
COMMENT ON COLUMN v_orders_sla.is_overdue IS 'Flaga: czy zamówienie jest po terminie';
COMMENT ON COLUMN v_orders_sla.is_urgent IS 'Flaga: czy zamówienie wymaga pilnej uwagi (7 dni)';
COMMENT ON COLUMN v_orders_sla.status_order IS 'Kolejność statusu do sortowania';

-- =====================================================
-- Przykłady użycia widoku:
-- =====================================================

-- 1. Zamówienia po terminie:
-- SELECT * FROM v_orders_sla WHERE is_overdue = true ORDER BY days_overdue DESC;

-- 2. Zamówienia wymagające pilnej uwagi:
-- SELECT * FROM v_orders_sla WHERE is_urgent = true ORDER BY days_remaining;

-- 3. Statystyki SLA według statusów:
-- SELECT
--     sla_status,
--     COUNT(*) as count,
--     AVG(days_in_progress) as avg_days
-- FROM v_orders_sla
-- GROUP BY sla_status
-- ORDER BY status_order;

-- 4. Zamówienia w trakcie realizacji:
-- SELECT * FROM v_orders_sla
-- WHERE status IN ('RECEIVED', 'CONFIRMED', 'PLANNED', 'IN_PROGRESS')
-- ORDER BY days_remaining;

-- 5. Podsumowanie statusów zamówień:
-- SELECT
--     status,
--     COUNT(*) as liczba_zamowien,
--     COUNT(CASE WHEN is_overdue THEN 1 END) as liczba_po_terminie,
--     COUNT(CASE WHEN is_urgent THEN 1 END) as liczba_pilnych
-- FROM v_orders_sla
-- GROUP BY status
-- ORDER BY status_order;