-- ============================================
-- Migracja: Dodanie obsługi Supabase Storage
-- ============================================
-- Ta migracja dodaje pole storage_type do tabeli attachments
-- aby umożliwić rozróżnienie między starymi załącznikami (BYTEA)
-- a nowymi w Supabase Storage

-- 1. Dodaj pole storage_type do tabeli attachments
ALTER TABLE attachments
ADD COLUMN IF NOT EXISTS storage_type VARCHAR(50) DEFAULT 'bytea';

-- 2. Ustaw archive_data jako nullable (dla nowych załączników w storage)
ALTER TABLE attachments
ALTER COLUMN archive_data DROP NOT NULL;

-- 3. Dodaj indeks dla szybszego wyszukiwania
CREATE INDEX IF NOT EXISTS idx_attachments_storage_type
ON attachments(storage_type);

-- 4. Dodaj indeks złożony dla szybkiego wyszukiwania załączników encji
CREATE INDEX IF NOT EXISTS idx_attachments_entity
ON attachments(entity_type, entity_id);

-- 5. Zaktualizuj istniejące rekordy aby miały poprawny storage_type
UPDATE attachments
SET storage_type = 'bytea'
WHERE storage_type IS NULL AND archive_data IS NOT NULL;

-- 6. Komentarz do tabeli
COMMENT ON COLUMN attachments.storage_type IS
'Typ przechowywania: bytea (stary sposób w bazie) lub supabase_storage (nowy w Object Storage)';

-- ============================================
-- Sprawdzenie struktury po migracji
-- ============================================
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'attachments'
-- ORDER BY ordinal_position;

-- ============================================
-- Polityki dla Storage Bucket (wykonaj osobno w Supabase Dashboard)
-- ============================================
-- Bucket: 'attachments' (utworzony już w setup_database.sql)
--
-- Jeśli bucket nie istnieje, utwórz go w Dashboard:
-- 1. Storage -> New Bucket
-- 2. Nazwa: attachments
-- 3. Public: false (dla bezpieczeństwa)
-- 4. File size limit: 50MB
-- 5. Allowed MIME types: pozostaw puste (wszystkie)