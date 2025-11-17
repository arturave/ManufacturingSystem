-- =====================================================
-- Funkcje pomocnicze dla Storage
-- =====================================================

-- Funkcja 1: Sprawdzanie dostępu
CREATE OR REPLACE FUNCTION check_entity_access(
    entity_type TEXT,
    entity_id TEXT,
    user_id UUID
)
RETURNS BOOLEAN AS $$
BEGIN
    -- Prosty dostęp dla wszystkich uwierzytelnionych
    RETURN auth.role() = 'authenticated';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Funkcja 2: Sprawdzanie właściciela (jeśli masz tabelę attachments)
CREATE OR REPLACE FUNCTION check_attachment_owner(
    attachment_id UUID,
    user_id UUID
)
RETURNS BOOLEAN AS $$
BEGIN
    -- Sprawdź czy tabela attachments istnieje
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'attachments'
    ) THEN
        RETURN EXISTS (
            SELECT 1 FROM attachments
            WHERE id = attachment_id
            AND created_by = user_id::text
        );
    ELSE
        -- Jeśli nie ma tabeli, zwróć true dla uwierzytelnionych
        RETURN auth.role() = 'authenticated';
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;