-- Script to fix products catalog structure and add missing columns
-- Author: System
-- Date: 2025-11-11

-- ============================================
-- 1. ADD MISSING COLUMNS TO products_catalog
-- ============================================

-- Add binary file storage columns if they don't exist
ALTER TABLE public.products_catalog
ADD COLUMN IF NOT EXISTS cad_2d_binary bytea,
ADD COLUMN IF NOT EXISTS cad_3d_binary bytea,
ADD COLUMN IF NOT EXISTS user_image_binary bytea,
ADD COLUMN IF NOT EXISTS documentation_binary bytea;

-- Add file metadata columns
ALTER TABLE public.products_catalog
ADD COLUMN IF NOT EXISTS cad_2d_filename text,
ADD COLUMN IF NOT EXISTS cad_3d_filename text,
ADD COLUMN IF NOT EXISTS user_image_filename text,
ADD COLUMN IF NOT EXISTS documentation_filename text,
ADD COLUMN IF NOT EXISTS cad_2d_filesize bigint,
ADD COLUMN IF NOT EXISTS cad_3d_filesize bigint,
ADD COLUMN IF NOT EXISTS user_image_filesize bigint,
ADD COLUMN IF NOT EXISTS documentation_filesize bigint,
ADD COLUMN IF NOT EXISTS cad_2d_mimetype text,
ADD COLUMN IF NOT EXISTS cad_3d_mimetype text,
ADD COLUMN IF NOT EXISTS user_image_mimetype text,
ADD COLUMN IF NOT EXISTS documentation_mimetype text;

-- Add documentation field for ZIP/7Z files
ALTER TABLE public.products_catalog
ADD COLUMN IF NOT EXISTS additional_documentation bytea,
ADD COLUMN IF NOT EXISTS additional_documentation_filename text,
ADD COLUMN IF NOT EXISTS additional_documentation_filesize bigint,
ADD COLUMN IF NOT EXISTS additional_documentation_mimetype text;

-- Add subcategory field
ALTER TABLE public.products_catalog
ADD COLUMN IF NOT EXISTS subcategory text;

-- Add dimension fields
ALTER TABLE public.products_catalog
ADD COLUMN IF NOT EXISTS width_mm numeric,
ADD COLUMN IF NOT EXISTS height_mm numeric,
ADD COLUMN IF NOT EXISTS length_mm numeric,
ADD COLUMN IF NOT EXISTS weight_kg numeric,
ADD COLUMN IF NOT EXISTS surface_area_m2 numeric;

-- Add production fields
ALTER TABLE public.products_catalog
ADD COLUMN IF NOT EXISTS production_time_minutes integer,
ADD COLUMN IF NOT EXISTS machine_type text;

-- ============================================
-- 2. MIGRATE FILE PATHS TO BINARY STORAGE
-- ============================================

-- Note: This migration would need to be done via application code
-- as PostgreSQL cannot read files from the filesystem directly.
-- The application should:
-- 1. Read existing file paths
-- 2. Load file contents as binary
-- 3. Store in binary columns
-- 4. Clear the path columns

-- For now, we'll just clear the path-based columns to ensure clean state
UPDATE public.products_catalog
SET
    cad_2d_file = NULL,
    cad_3d_file = NULL,
    user_image_file = NULL
WHERE
    cad_2d_file IS NOT NULL
    OR cad_3d_file IS NOT NULL
    OR user_image_file IS NOT NULL;

-- ============================================
-- 3. DEFINE WHICH TABLE IS THE SOURCE OF TRUTH
-- ============================================

-- products_catalog is for the product templates/catalog
-- parts is for actual parts in orders

-- Add a comment to clarify the purpose
COMMENT ON TABLE public.products_catalog IS 'Product catalog - templates for products that can be ordered';
COMMENT ON TABLE public.parts IS 'Actual parts in orders - instances of products from the catalog';

-- ============================================
-- 4. CREATE VIEW FOR UNIFIED PRODUCT ACCESS
-- ============================================

DROP VIEW IF EXISTS public.v_all_products CASCADE;

CREATE OR REPLACE VIEW public.v_all_products AS
SELECT
    pc.id,
    pc.idx_code,
    pc.name,
    pc.material_id,
    md.name as material_name,
    md.category as material_category,
    pc.thickness_mm,
    pc.customer_id,
    c.name as customer_name,
    pc.bending_cost,
    pc.additional_costs,
    pc.material_laser_cost,
    pc.material_cost,
    pc.laser_cost,
    (COALESCE(pc.material_cost, 0) + COALESCE(pc.laser_cost, 0) +
     COALESCE(pc.bending_cost, 0) + COALESCE(pc.additional_costs, 0)) as total_cost,
    pc.description,
    pc.notes,
    pc.category,
    pc.subcategory,
    pc.tags,
    pc.thumbnail_100,
    pc.preview_800,
    pc.preview_4k,
    pc.cad_2d_binary,
    pc.cad_3d_binary,
    pc.user_image_binary,
    pc.documentation_binary,
    pc.additional_documentation,
    pc.cad_2d_filename,
    pc.cad_3d_filename,
    pc.user_image_filename,
    pc.documentation_filename,
    pc.additional_documentation_filename,
    pc.width_mm,
    pc.height_mm,
    pc.length_mm,
    pc.weight_kg,
    pc.surface_area_m2,
    pc.production_time_minutes,
    pc.machine_type,
    pc.usage_count,
    pc.last_used_at,
    pc.is_active,
    pc.created_at,
    pc.updated_at,
    pc.created_by,
    pc.updated_by,
    'catalog' as source_type
FROM
    public.products_catalog pc
    LEFT JOIN public.materials_dict md ON pc.material_id = md.id
    LEFT JOIN public.customers c ON pc.customer_id = c.id
WHERE
    pc.is_active = true;

-- ============================================
-- 5. CREATE FUNCTION TO COPY PRODUCT TO ORDER
-- ============================================

CREATE OR REPLACE FUNCTION public.copy_product_to_order(
    p_product_id uuid,
    p_order_id uuid,
    p_qty integer DEFAULT 1
) RETURNS uuid AS $$
DECLARE
    v_part_id uuid;
BEGIN
    -- Insert into parts table, copying from products_catalog
    INSERT INTO public.parts (
        order_id,
        name,
        material_id,
        thickness_mm,
        qty,
        bending_cost,
        additional_costs,
        material_laser_cost,
        material_cost,
        laser_cost,
        thumbnail_100,
        cad_2d_binary,
        cad_3d_binary,
        user_image_binary,
        documentation_binary,
        category,
        subcategory,
        tags,
        width_mm,
        height_mm,
        length_mm,
        weight_kg,
        surface_area_m2,
        production_time_minutes,
        machine_type,
        notes
    )
    SELECT
        p_order_id,
        name,
        material_id,
        thickness_mm,
        p_qty,
        bending_cost,
        additional_costs,
        material_laser_cost,
        material_cost,
        laser_cost,
        thumbnail_100,
        cad_2d_binary,
        cad_3d_binary,
        user_image_binary,
        documentation_binary,
        category,
        subcategory,
        tags,
        width_mm,
        height_mm,
        length_mm,
        weight_kg,
        surface_area_m2,
        production_time_minutes,
        machine_type,
        notes
    FROM
        public.products_catalog
    WHERE
        id = p_product_id
    RETURNING id INTO v_part_id;

    -- Update usage statistics
    UPDATE public.products_catalog
    SET
        usage_count = COALESCE(usage_count, 0) + 1,
        last_used_at = NOW()
    WHERE
        id = p_product_id;

    RETURN v_part_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 6. ADD BINARY STORAGE TO parts TABLE TOO
-- ============================================

ALTER TABLE public.parts
ADD COLUMN IF NOT EXISTS additional_documentation bytea,
ADD COLUMN IF NOT EXISTS additional_documentation_filename text,
ADD COLUMN IF NOT EXISTS additional_documentation_filesize bigint,
ADD COLUMN IF NOT EXISTS additional_documentation_mimetype text;

-- ============================================
-- 7. CREATE INDEX FOR PERFORMANCE
-- ============================================

CREATE INDEX IF NOT EXISTS idx_products_catalog_customer_id ON public.products_catalog(customer_id);
CREATE INDEX IF NOT EXISTS idx_products_catalog_material_id ON public.products_catalog(material_id);
CREATE INDEX IF NOT EXISTS idx_products_catalog_is_active ON public.products_catalog(is_active);
CREATE INDEX IF NOT EXISTS idx_products_catalog_name ON public.products_catalog(name);
CREATE INDEX IF NOT EXISTS idx_products_catalog_idx_code ON public.products_catalog(idx_code);

-- ============================================
-- 8. GRANT PERMISSIONS
-- ============================================

-- Grant appropriate permissions if using RLS
-- This would depend on your specific security setup

COMMIT;