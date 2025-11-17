-- =====================================================
-- Polityki RLS dla Supabase Storage Buckets
-- =====================================================
-- Autor: System Manufacturing
-- Data: 2025-11-17
-- Opis: Konfiguracja polityk bezpieczeństwa dla bucketów
-- =====================================================

-- =====================================================
-- UWAGA: Najpierw utwórz buckety w Supabase Dashboard!
-- =====================================================
-- 1. Przejdź do Storage w Supabase Dashboard
-- 2. Utwórz bucket o nazwie 'attachments' (prywatny)
-- 3. Opcjonalnie utwórz bucket 'products' (publiczny)
-- 4. RLS jest już włączony domyślnie dla storage.objects
-- =====================================================

-- =====================================================
-- USUŃ ISTNIEJĄCE POLITYKI (jeśli istnieją)
-- =====================================================

-- Usuń istniejące polityki dla bucketu 'attachments'
DROP POLICY IF EXISTS "Authenticated users can view attachments" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can upload attachments" ON storage.objects;
DROP POLICY IF EXISTS "Users can update own attachments" ON storage.objects;
DROP POLICY IF EXISTS "Users can delete own attachments" ON storage.objects;
DROP POLICY IF EXISTS "Public access to thumbnails" ON storage.objects;
DROP POLICY IF EXISTS "Service role full access" ON storage.objects;
DROP POLICY IF EXISTS "Public can view product images" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated can upload product images" ON storage.objects;

-- =====================================================
-- POLITYKI DLA BUCKETU 'attachments'
-- =====================================================

-- Polityka: Odczyt plików przez uwierzytelnionych użytkowników
CREATE POLICY "Authenticated users can view attachments"
ON storage.objects
FOR SELECT
USING (
    bucket_id = 'attachments'
    AND auth.role() = 'authenticated'
);

-- Polityka: Upload plików przez uwierzytelnionych użytkowników
CREATE POLICY "Authenticated users can upload attachments"
ON storage.objects
FOR INSERT
WITH CHECK (
    bucket_id = 'attachments'
    AND auth.role() = 'authenticated'
);

-- Polityka: Aktualizacja plików przez uwierzytelnionych użytkowników
CREATE POLICY "Users can update own attachments"
ON storage.objects
FOR UPDATE
USING (
    bucket_id = 'attachments'
    AND auth.role() = 'authenticated'
)
WITH CHECK (
    bucket_id = 'attachments'
    AND auth.role() = 'authenticated'
);

-- Polityka: Usuwanie plików przez uwierzytelnionych użytkowników
CREATE POLICY "Users can delete own attachments"
ON storage.objects
FOR DELETE
USING (
    bucket_id = 'attachments'
    AND auth.role() = 'authenticated'
);

-- =====================================================
-- POLITYKI SPECJALNE
-- =====================================================

-- Polityka: Publiczny dostęp do thumbnails
CREATE POLICY "Public access to thumbnails"
ON storage.objects
FOR SELECT
USING (
    bucket_id = 'attachments'
    AND storage.filename(name) LIKE 'thumb_%'
);

-- Polityka: Service role ma pełny dostęp
CREATE POLICY "Service role full access"
ON storage.objects
FOR ALL
USING (
    auth.role() = 'service_role'
)
WITH CHECK (
    auth.role() = 'service_role'
);

-- =====================================================
-- POLITYKI DLA BUCKETU 'products' (opcjonalne)
-- =====================================================

-- Polityka: Publiczny dostęp do obrazów produktów
CREATE POLICY "Public can view product images"
ON storage.objects
FOR SELECT
USING (
    bucket_id = 'products'
);

-- Polityka: Upload obrazów produktów przez uwierzytelnionych
CREATE POLICY "Authenticated can upload product images"
ON storage.objects
FOR INSERT
WITH CHECK (
    bucket_id = 'products'
    AND auth.role() = 'authenticated'
    -- Tylko obrazy
    AND (
        storage.extension(name) IN ('jpg', 'jpeg', 'png', 'gif', 'svg', 'webp')
    )
);

-- =====================================================
-- FUNKCJE POMOCNICZE
-- =====================================================

-- Funkcja do sprawdzania właściciela załącznika (jeśli tabela attachments istnieje)
CREATE OR REPLACE FUNCTION check_attachment_owner(attachment_id UUID, user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    -- Sprawdź czy tabela attachments istnieje
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'attachments'
    ) THEN
        RETURN EXISTS (
            SELECT 1 FROM attachments
            WHERE id = attachment_id
            AND created_by = user_id::text
        );
    ELSE
        -- Jeśli tabela nie istnieje, zwróć true dla uwierzytelnionych
        RETURN auth.role() = 'authenticated';
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Funkcja do sprawdzania uprawnień do entity
CREATE OR REPLACE FUNCTION check_entity_access(entity_type TEXT, entity_id TEXT, user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    -- Dla uproszczenia, wszyscy uwierzytelnieni użytkownicy mają dostęp
    -- W przyszłości można rozbudować o bardziej szczegółowe uprawnienia
    RETURN auth.role() = 'authenticated';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- UTWORZENIE BUCKETU (alternatywa do Dashboard)
-- =====================================================
-- UWAGA: Poniższe polecenia działają tylko z service_role key
-- Lepiej utworzyć buckety przez Dashboard

-- Sprawdź czy bucket 'attachments' istnieje
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM storage.buckets WHERE id = 'attachments'
    ) THEN
        INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
        VALUES (
            'attachments',
            'attachments',
            false,
            52428800, -- 50MB
            ARRAY['image/jpeg', 'image/png', 'image/gif', 'image/svg+xml',
                  'application/pdf', 'application/msword',
                  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                  'application/vnd.ms-excel',
                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
        );
    END IF;
END $$;

-- Sprawdź czy bucket 'products' istnieje (opcjonalny)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM storage.buckets WHERE id = 'products'
    ) THEN
        INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
        VALUES (
            'products',
            'products',
            true,  -- publiczny
            10485760, -- 10MB
            ARRAY['image/jpeg', 'image/png', 'image/gif', 'image/svg+xml', 'image/webp']
        );
    END IF;
END $$;

-- =====================================================
-- KOMENTARZE I DOKUMENTACJA
-- =====================================================

COMMENT ON POLICY "Authenticated users can view attachments" ON storage.objects
IS 'Pozwala uwierzytelnionym użytkownikom na odczyt załączników';

COMMENT ON POLICY "Authenticated users can upload attachments" ON storage.objects
IS 'Pozwala uwierzytelnionym użytkownikom na upload plików';

COMMENT ON POLICY "Users can update own attachments" ON storage.objects
IS 'Pozwala użytkownikom na aktualizację załączników';

COMMENT ON POLICY "Users can delete own attachments" ON storage.objects
IS 'Pozwala użytkownikom na usuwanie załączników';

-- =====================================================
-- WERYFIKACJA INSTALACJI
-- =====================================================

-- Sprawdź czy buckety zostały utworzone
SELECT id, name, public, file_size_limit
FROM storage.buckets
WHERE id IN ('attachments', 'products');

-- Sprawdź polityki RLS
SELECT schemaname, tablename, policyname, permissive, roles, cmd
FROM pg_policies
WHERE schemaname = 'storage' AND tablename = 'objects';

-- Sprawdź czy RLS jest włączony (informacyjnie - nie możemy tego zmienić)
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'storage' AND tablename = 'objects';

-- =====================================================
-- PRZYKŁADY UŻYCIA (do testowania)
-- =====================================================

-- Test 1: Sprawdź czy authenticated user może odczytać pliki
-- SET ROLE authenticated;
-- SELECT * FROM storage.objects WHERE bucket_id = 'attachments' LIMIT 1;

-- Test 2: Sprawdź limity rozmiaru
-- SELECT pg_size_pretty(52428800::bigint); -- Should show 50 MB
-- SELECT pg_size_pretty(10485760::bigint); -- Should show 10 MB

-- =====================================================
-- UWAGI IMPLEMENTACYJNE
-- =====================================================

-- 1. Bucket 'attachments' jest prywatny - wymaga uwierzytelnienia
-- 2. Bucket 'products' jest publiczny - obrazy produktów są dostępne publicznie
-- 3. RLS jest włączony domyślnie dla storage.objects w Supabase
-- 4. Użytkownicy muszą być uwierzytelnieni aby uploadować pliki
-- 5. Service role key jest wymagany dla operacji administracyjnych
-- 6. Signed URLs powinny być generowane dla prywatnych plików
-- 7. Publiczne pliki można pobierać bezpośrednio przez URL

-- =====================================================
-- JEŚLI POTRZEBUJESZ WYŁĄCZYĆ STARE POLITYKI
-- =====================================================
-- Jeśli masz problemy z konfliktami polityk, możesz najpierw
-- wylistować wszystkie istniejące polityki:
/*
SELECT policyname
FROM pg_policies
WHERE schemaname = 'storage'
AND tablename = 'objects';
*/
-- I następnie usunąć je ręcznie używając:
-- DROP POLICY "nazwa_polityki" ON storage.objects;