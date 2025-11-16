-- Sprawdzenie struktury tabeli products_catalog
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM
    information_schema.columns
WHERE
    table_schema = 'public'
    AND table_name = 'products_catalog'
ORDER BY
    ordinal_position;

-- Sprawdzenie triggerów na tabeli
SELECT
    tgname as trigger_name,
    tgtype,
    tgfoid::regproc as trigger_function
FROM
    pg_trigger
WHERE
    tgrelid = 'products_catalog'::regclass
    AND NOT tgisinternal;

-- Sprawdzenie definicji funkcji triggerów
SELECT
    proname AS function_name,
    prosrc AS function_source
FROM
    pg_proc
WHERE
    proname IN (
        SELECT tgfoid::regproc::text
        FROM pg_trigger
        WHERE tgrelid = 'products_catalog'::regclass
    );

-- Sprawdzenie czy kolumny CAD istnieją
SELECT
    column_name
FROM
    information_schema.columns
WHERE
    table_schema = 'public'
    AND table_name = 'products_catalog'
    AND column_name IN (
        'cad_2d_file',
        'cad_3d_file',
        'cad_2d_binary',
        'cad_3d_binary',
        'cad_2d_filename',
        'cad_3d_filename',
        'cad_2d_filesize',
        'cad_3d_filesize'
    );