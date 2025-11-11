-- ============================================
-- SKRYPT CZYSZCZĄCY DANE W BAZIE DANYCH
-- Data: 2025-11-11
-- UWAGA: Ten skrypt USUWA WSZYSTKIE DANE!
-- ============================================

-- Wyłącz tymczasowo klucze obce
SET session_replication_role = 'replica';

-- ============================================
-- 1. USUŃ DANE Z TABEL ZALEŻNYCH (kolejność ważna!)
-- ============================================

-- Dokumenty WZ
TRUNCATE TABLE public.delivery_notes CASCADE;

-- Historia statusów
TRUNCATE TABLE public.order_status_history CASCADE;

-- Pozycje zamówień i ofert
TRUNCATE TABLE public.order_items CASCADE;
TRUNCATE TABLE public.quotation_items CASCADE;

-- Części (instancje produktów)
TRUNCATE TABLE public.parts CASCADE;

-- Główne tabele
TRUNCATE TABLE public.orders CASCADE;
TRUNCATE TABLE public.quotations CASCADE;

-- Katalog produktów
TRUNCATE TABLE public.products_catalog CASCADE;

-- Klienci (opcjonalnie - możesz zachować)
-- TRUNCATE TABLE public.customers CASCADE;

-- Słownik materiałów (opcjonalnie - możesz zachować)
-- TRUNCATE TABLE public.materials_dict CASCADE;

-- ============================================
-- 2. ZRESETUJ LICZNIKI
-- ============================================

-- Liczniki procesów
TRUNCATE TABLE public.process_counters CASCADE;

-- Liczniki ofert
TRUNCATE TABLE public.quote_counters CASCADE;

-- Dodaj początkowe liczniki dla bieżącego roku
INSERT INTO public.process_counters (year, last_no) VALUES (2025, 0);
INSERT INTO public.quote_counters (year, last_no) VALUES (2025, 0);

-- ============================================
-- 3. USUŃ TABELE NIEPOTRZEBNE
-- ============================================

-- Usuń backup
DROP TABLE IF EXISTS public.parts_backup_2025_11_03;

-- ============================================
-- 4. WŁĄCZ Z POWROTEM KLUCZE OBCE
-- ============================================

SET session_replication_role = 'origin';

-- ============================================
-- 5. DODAJ PRZYKŁADOWE DANE (OPCJONALNIE)
-- ============================================

-- Przykładowy materiał
INSERT INTO public.materials_dict (name, description, category, density, is_active)
VALUES
    ('Stal S235', 'Stal konstrukcyjna', 'STAL_NIERDDZEWNA', 7.85, true),
    ('Stal 1.4301 (304)', 'Stal nierdzewna', 'STAL_NIERDDZEWNA', 7.9, true),
    ('Aluminium 5754', 'Stop aluminium', 'ALUMINIUM', 2.67, true),
    ('Mosiądz CuZn37', 'Mosiądz', 'METALE_KOLOROWE', 8.44, true);

-- Przykładowy klient
INSERT INTO public.customers (name, short_name, customer_type, email, city, is_active)
VALUES
    ('Firma Testowa Sp. z o.o.', 'FIRMA TEST', 'company', 'kontakt@firma-test.pl', 'Warszawa', true),
    ('Jan Kowalski', 'JK', 'individual', 'jan.kowalski@example.pl', 'Kraków', true);

-- ============================================
-- 6. PODSUMOWANIE
-- ============================================

-- Sprawdź stan tabel
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM
    pg_tables
WHERE
    schemaname = 'public'
ORDER BY
    tablename;

-- Komunikat końcowy
SELECT 'Baza danych została wyczyszczona!' AS message;