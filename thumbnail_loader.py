#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thumbnail Loader Module
Handles loading thumbnails from various sources (base64, HTTP URLs, local files)
"""

import io
import base64
from typing import Optional, Union
from PIL import Image, ImageTk
import tkinter as tk
import urllib.request
import urllib.error
from functools import lru_cache
import hashlib
import tempfile
import os
from pathlib import Path

class ThumbnailLoader:
    """Universal thumbnail loader with caching support"""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize thumbnail loader

        Args:
            cache_dir: Directory for caching thumbnails. If None, uses temp directory
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(tempfile.gettempdir()) / "thumbnail_cache"

        self.cache_dir.mkdir(exist_ok=True)

        # In-memory cache for PhotoImage objects
        self._memory_cache = {}

    @staticmethod
    def fix_base64_padding(data: str) -> str:
        """Fix base64 string padding"""
        padding = len(data) % 4
        if padding:
            data += '=' * (4 - padding)
        return data

    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for URL"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.jpg"

    def _load_from_cache(self, url: str) -> Optional[bytes]:
        """Load thumbnail from cache if exists"""
        cache_path = self._get_cache_path(url)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    return f.read()
            except:
                pass
        return None

    def _save_to_cache(self, url: str, data: bytes):
        """Save thumbnail to cache"""
        try:
            cache_path = self._get_cache_path(url)
            with open(cache_path, 'wb') as f:
                f.write(data)
        except:
            pass

    def load_from_http_url(self, url: str, use_cache: bool = True) -> Optional[bytes]:
        """
        Load thumbnail from HTTP URL

        Args:
            url: HTTP URL to image
            use_cache: Whether to use disk cache

        Returns:
            Image data as bytes or None
        """
        try:
            # Check cache first
            if use_cache:
                cached = self._load_from_cache(url)
                if cached:
                    return cached

            # Download from URL
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read()

                # Save to cache
                if use_cache:
                    self._save_to_cache(url, data)

                return data

        except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
            print(f"Error loading thumbnail from {url}: {e}")
            return None

    def load_from_base64(self, data: str) -> Optional[bytes]:
        """
        Load thumbnail from base64 string or data URL

        Args:
            data: Base64 string or data URL

        Returns:
            Image data as bytes or None
        """
        try:
            # Handle data URL
            if data.startswith('data:image'):
                # Extract base64 part
                base64_data = data.split(',')[1] if ',' in data else data
            else:
                base64_data = data

            # Fix padding and decode
            base64_data = self.fix_base64_padding(base64_data)
            return base64.b64decode(base64_data)

        except Exception as e:
            print(f"Error decoding base64 thumbnail: {e}")
            return None

    def get_thumbnail(
        self,
        source: Union[str, bytes],
        size: tuple = (40, 40),
        as_photo_image: bool = True
    ) -> Optional[Union[ImageTk.PhotoImage, Image.Image]]:
        """
        Get thumbnail from various sources

        Args:
            source: Image source (URL, base64, or raw bytes)
            size: Target thumbnail size
            as_photo_image: Return as PhotoImage (True) or PIL Image (False)

        Returns:
            Thumbnail image or None
        """
        try:
            # Check memory cache for PhotoImage
            if as_photo_image and isinstance(source, str):
                cache_key = f"{source}_{size}"
                if cache_key in self._memory_cache:
                    return self._memory_cache[cache_key]

            # Get image data
            image_data = None

            if isinstance(source, bytes):
                # Already bytes
                image_data = source

            elif isinstance(source, str):
                if source.startswith('http://') or source.startswith('https://'):
                    # HTTP URL
                    image_data = self.load_from_http_url(source)

                elif source.startswith('data:image') or len(source) > 100:
                    # Likely base64 or data URL
                    image_data = self.load_from_base64(source)

                elif os.path.exists(source):
                    # Local file
                    with open(source, 'rb') as f:
                        image_data = f.read()

            if not image_data:
                return None

            # Create PIL Image
            image = Image.open(io.BytesIO(image_data))

            # Convert RGBA to RGB if needed (for JPEG compatibility)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                bg = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                bg.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = bg

            # Resize
            image.thumbnail(size, Image.Resampling.LANCZOS)

            # Return as requested format
            if as_photo_image:
                photo = ImageTk.PhotoImage(image)

                # Cache PhotoImage
                if isinstance(source, str):
                    cache_key = f"{source}_{size}"
                    self._memory_cache[cache_key] = photo

                return photo
            else:
                return image

        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return None

    def get_product_thumbnail(self, product: dict, size: tuple = (40, 40)) -> Optional[ImageTk.PhotoImage]:
        """
        Get thumbnail for product from various possible fields

        Args:
            product: Product dictionary
            size: Target thumbnail size

        Returns:
            PhotoImage or None
        """
        # Priority order for thumbnail sources
        sources = [
            product.get('thumbnail_data'),
            product.get('thumb_data'),
            product.get('preview_800_url'),
            product.get('thumbnail_100_url'),
            product.get('thumbnail_100'),
            product.get('preview_url'),
        ]

        # Also check nested product data
        if product.get('product') and isinstance(product['product'], dict):
            nested = product['product']
            sources.extend([
                nested.get('preview_800_url'),
                nested.get('thumbnail_100_url'),
            ])

        # Also check products_catalog
        if product.get('products_catalog') and isinstance(product['products_catalog'], dict):
            catalog = product['products_catalog']
            sources.extend([
                catalog.get('preview_800_url'),
                catalog.get('thumbnail_100_url'),
            ])

        # Try each source
        for source in sources:
            if source:
                thumbnail = self.get_thumbnail(source, size)
                if thumbnail:
                    return thumbnail

        return None

    def clear_cache(self):
        """Clear all caches"""
        # Clear memory cache
        self._memory_cache.clear()

        # Clear disk cache
        try:
            for file in self.cache_dir.glob("*.jpg"):
                file.unlink()
        except:
            pass


# Global instance
_thumbnail_loader: Optional[ThumbnailLoader] = None

def get_thumbnail_loader() -> ThumbnailLoader:
    """Get global thumbnail loader instance"""
    global _thumbnail_loader
    if _thumbnail_loader is None:
        _thumbnail_loader = ThumbnailLoader()
    return _thumbnail_loader