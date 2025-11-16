#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase Storage Utilities
Centralized module for file storage operations using Supabase Object Storage (S3-like)
"""

import os
import uuid
from typing import Optional, Tuple
from pathlib import Path
from supabase import Client


# Default bucket name for product files
DEFAULT_BUCKET = "product_files"

# Folder structure within bucket
STORAGE_FOLDERS = {
    "thumbnail_100": "thumbnails/100",
    "preview_800": "thumbnails/800",
    "preview_4k": "thumbnails/4k",
    "cad_2d": "cad/2d",
    "cad_3d": "cad/3d",
    "user_image": "images",
    "documentation": "docs"
}

# MIME type mapping
MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".dxf": "application/dxf",
    ".dwg": "application/acad",
    ".step": "application/step",
    ".stp": "application/step",
    ".stl": "model/stl",
    ".iges": "model/iges",
    ".igs": "model/iges",
    ".zip": "application/zip",
    ".7z": "application/x-7z-compressed",
    ".pdf": "application/pdf",
}


def get_mime_type(filename: str) -> str:
    """Get MIME type based on file extension"""
    ext = Path(filename).suffix.lower()
    return MIME_TYPES.get(ext, "application/octet-stream")


def generate_storage_path(product_id: str, file_type: str, filename: str) -> str:
    """
    Generate a unique storage path for a file.

    Args:
        product_id: UUID of the product
        file_type: Type of file (thumbnail_100, cad_2d, etc.)
        filename: Original filename

    Returns:
        Storage path like: thumbnails/100/product_id/filename
    """
    folder = STORAGE_FOLDERS.get(file_type, "misc")
    # Add UUID to ensure uniqueness even if same filename
    unique_suffix = str(uuid.uuid4())[:8]
    name_parts = Path(filename).stem, unique_suffix, Path(filename).suffix
    unique_filename = f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
    return f"{folder}/{product_id}/{unique_filename}"


def upload_to_storage(
    client: Client,
    bucket: str,
    path: str,
    data: bytes,
    content_type: str = "application/octet-stream",
    upsert: bool = False
) -> Tuple[bool, str]:
    """
    Upload file to Supabase Storage.

    Args:
        client: Supabase client instance
        bucket: Bucket name (default: product_files)
        path: Storage path within bucket
        data: Binary data to upload
        content_type: MIME type of the file
        upsert: If True, overwrite existing file

    Returns:
        Tuple of (success: bool, url_or_error: str)
    """
    try:
        # Upload to storage
        result = client.storage.from_(bucket).upload(
            path=path,
            file=data,
            file_options={
                "content-type": content_type,
                "upsert": str(upsert).lower()
            }
        )

        # Get public URL
        public_url = client.storage.from_(bucket).get_public_url(path)

        return True, public_url

    except Exception as e:
        error_msg = str(e)
        # Handle duplicate file error
        if "Duplicate" in error_msg and not upsert:
            # Try again with upsert
            return upload_to_storage(client, bucket, path, data, content_type, upsert=True)
        return False, f"Upload error: {error_msg}"


def download_from_storage(client: Client, bucket: str, path: str) -> Tuple[bool, bytes]:
    """
    Download file from Supabase Storage.

    Args:
        client: Supabase client instance
        bucket: Bucket name
        path: Storage path within bucket

    Returns:
        Tuple of (success: bool, data_or_error: bytes/str)
    """
    try:
        data = client.storage.from_(bucket).download(path)
        return True, data
    except Exception as e:
        return False, f"Download error: {str(e)}"


def download_from_url(url: str) -> Tuple[bool, bytes]:
    """
    Download file from public URL.

    Args:
        url: Public URL to the file

    Returns:
        Tuple of (success: bool, data_or_error: bytes/str)
    """
    try:
        import requests
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return True, response.content
    except Exception as e:
        return False, f"Download error: {str(e)}"


def delete_from_storage(client: Client, bucket: str, path: str) -> Tuple[bool, str]:
    """
    Delete file from Supabase Storage.

    Args:
        client: Supabase client instance
        bucket: Bucket name
        path: Storage path within bucket

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        client.storage.from_(bucket).remove([path])
        return True, "File deleted successfully"
    except Exception as e:
        return False, f"Delete error: {str(e)}"


def get_public_url(client: Client, bucket: str, path: str) -> str:
    """
    Get public URL for a file in storage.

    Args:
        client: Supabase client instance
        bucket: Bucket name
        path: Storage path within bucket

    Returns:
        Public URL string
    """
    return client.storage.from_(bucket).get_public_url(path)


def extract_path_from_url(url: str, bucket: str = DEFAULT_BUCKET) -> Optional[str]:
    """
    Extract storage path from public URL.

    Args:
        url: Public URL
        bucket: Bucket name to look for

    Returns:
        Storage path or None if not found
    """
    try:
        # URL format: https://xxx.supabase.co/storage/v1/object/public/bucket/path
        if f"/storage/v1/object/public/{bucket}/" in url:
            path = url.split(f"/storage/v1/object/public/{bucket}/")[1]
            return path
        return None
    except Exception:
        return None


def upload_product_file(
    client: Client,
    product_id: str,
    file_type: str,
    data: bytes,
    original_filename: str,
    bucket: str = DEFAULT_BUCKET
) -> Tuple[bool, str]:
    """
    Convenience function to upload a product file with proper path generation.

    Args:
        client: Supabase client instance
        product_id: UUID of the product
        file_type: Type of file (thumbnail_100, cad_2d, cad_3d, user_image, documentation)
        data: Binary data to upload
        original_filename: Original filename for MIME type detection
        bucket: Bucket name (default: product_files)

    Returns:
        Tuple of (success: bool, url_or_error: str)
    """
    # Generate storage path
    storage_path = generate_storage_path(product_id, file_type, original_filename)

    # Get MIME type
    content_type = get_mime_type(original_filename)

    # Upload
    return upload_to_storage(client, bucket, storage_path, data, content_type)


def delete_product_files(
    client: Client,
    product_id: str,
    bucket: str = DEFAULT_BUCKET
) -> Tuple[bool, str]:
    """
    Delete all files for a product from storage.

    Args:
        client: Supabase client instance
        product_id: UUID of the product
        bucket: Bucket name

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        deleted_count = 0
        errors = []

        # Delete files from each folder
        for folder in STORAGE_FOLDERS.values():
            product_folder = f"{folder}/{product_id}"
            try:
                # List files in product folder
                files = client.storage.from_(bucket).list(product_folder)
                if files:
                    paths = [f"{product_folder}/{f['name']}" for f in files]
                    client.storage.from_(bucket).remove(paths)
                    deleted_count += len(paths)
            except Exception as e:
                errors.append(f"{folder}: {str(e)}")

        if errors:
            return True, f"Deleted {deleted_count} files with some errors: {'; '.join(errors)}"
        return True, f"Deleted {deleted_count} files successfully"

    except Exception as e:
        return False, f"Delete error: {str(e)}"


# Bucket setup helper (for documentation purposes)
BUCKET_SETUP_SQL = """
-- Create bucket in Supabase Dashboard or via API
-- Bucket name: product_files
-- Public: Yes (for thumbnails) or No (for private files with signed URLs)

-- RLS Policy for public read access
CREATE POLICY "Public read access for product files"
ON storage.objects FOR SELECT
USING (bucket_id = 'product_files');

-- RLS Policy for authenticated upload
CREATE POLICY "Authenticated users can upload product files"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'product_files'
    AND auth.role() = 'authenticated'
);

-- RLS Policy for authenticated delete
CREATE POLICY "Authenticated users can delete product files"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'product_files'
    AND auth.role() = 'authenticated'
);
"""
