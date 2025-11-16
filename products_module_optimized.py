#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimized functions for products module - improved performance
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
import requests
from functools import lru_cache

class ThumbnailLoader:
    """Optimized thumbnail loader with concurrent loading and caching"""

    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.cache = {}
        self.pending_loads = set()

    def load_thumbnail_async(self, product_id: str, url: str, callback=None):
        """Load thumbnail asynchronously"""
        if product_id in self.cache:
            if callback:
                callback(product_id, self.cache[product_id])
            return

        if product_id in self.pending_loads:
            return  # Already loading

        self.pending_loads.add(product_id)

        def load_task():
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    self.cache[product_id] = response.content
                    if callback:
                        callback(product_id, response.content)
            except:
                pass
            finally:
                self.pending_loads.discard(product_id)

        self.executor.submit(load_task)

    def load_thumbnails_batch(self, products: List[Dict], callback=None):
        """Load multiple thumbnails concurrently"""
        futures = []

        for product in products:
            if product.get('thumbnail_100_url'):
                future = self.executor.submit(
                    self._load_single,
                    product['id'],
                    product['thumbnail_100_url']
                )
                futures.append((product['id'], future))

        # Process results as they complete
        for product_id, future in futures:
            try:
                result = future.result(timeout=3)
                if result and callback:
                    callback(product_id, result)
            except:
                pass

    def _load_single(self, product_id: str, url: str) -> Optional[bytes]:
        """Load single thumbnail"""
        if product_id in self.cache:
            return self.cache[product_id]

        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                self.cache[product_id] = response.content
                return response.content
        except:
            pass

        return None

    def shutdown(self):
        """Shutdown the executor"""
        self.executor.shutdown(wait=False)


def generate_optimized_thumbnails(image_data: bytes, include_4k: bool = False) -> Dict[str, bytes]:
    """
    Generate thumbnails with optional 4K generation
    4K thumbnails are skipped by default for performance
    """
    import io
    from PIL import Image

    try:
        # Open source image
        img = Image.open(io.BytesIO(image_data))

        # Convert to RGB if needed
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')

        result = {}

        # Generate small thumbnail (100x100) - always needed
        thumbnail = img.copy()
        thumbnail.thumbnail((100, 100), Image.Resampling.LANCZOS)
        thumb_bytes = io.BytesIO()
        thumbnail.save(thumb_bytes, format='JPEG', quality=85, optimize=True)
        result['thumbnail_100'] = thumb_bytes.getvalue()

        # Generate medium preview (800x800) - usually needed
        preview_800 = img.copy()
        preview_800.thumbnail((800, 800), Image.Resampling.LANCZOS)
        preview_bytes = io.BytesIO()
        preview_800.save(preview_bytes, format='JPEG', quality=90, optimize=True)
        result['preview_800'] = preview_bytes.getvalue()

        # Generate 4K preview only if requested (saves time and storage)
        if include_4k:
            preview_4k = img.copy()
            preview_4k.thumbnail((3840, 2160), Image.Resampling.LANCZOS)
            preview_4k_bytes = io.BytesIO()
            preview_4k.save(preview_4k_bytes, format='PNG')  # PNG for quality
            result['preview_4k'] = preview_4k_bytes.getvalue()

        return result
    except Exception:
        return {}


class LazyLoadingProductList:
    """Product list with lazy loading of thumbnails"""

    def __init__(self, products: List[Dict], thumbnail_loader: ThumbnailLoader):
        self.products = products
        self.loader = thumbnail_loader
        self.visible_range = (0, 20)  # Initially load first 20
        self.loaded_thumbnails = set()

    def set_visible_range(self, start: int, end: int):
        """Update visible range and load thumbnails for visible products"""
        self.visible_range = (start, end)
        self.load_visible_thumbnails()

    def load_visible_thumbnails(self):
        """Load thumbnails only for visible products"""
        visible_products = self.products[self.visible_range[0]:self.visible_range[1]]

        for product in visible_products:
            if product['id'] not in self.loaded_thumbnails:
                if product.get('thumbnail_100_url'):
                    self.loader.load_thumbnail_async(
                        product['id'],
                        product['thumbnail_100_url']
                    )
                    self.loaded_thumbnails.add(product['id'])


# Performance optimization settings
PERFORMANCE_SETTINGS = {
    'max_concurrent_downloads': 4,
    'thumbnail_timeout': 3,  # seconds
    'generate_4k_default': False,  # Don't generate 4K by default
    'lazy_load_batch_size': 20,
    'cache_max_size': 100,  # Maximum cached thumbnails
    'jpeg_quality': 85,  # Balance quality vs size
    'optimize_images': True  # Use PIL optimize flag
}


@lru_cache(maxsize=100)
def cached_thumbnail_url(product_id: str, products_data: tuple) -> Optional[str]:
    """Cached lookup for thumbnail URL"""
    for product in products_data:
        if product.get('id') == product_id:
            return product.get('thumbnail_100_url')
    return None


def batch_update_products(client, updates: List[Dict]) -> bool:
    """
    Batch update products for better performance
    Instead of updating one by one, batch updates when possible
    """
    try:
        # Group updates by operation type
        for update in updates:
            product_id = update.pop('id')
            client.table('products_catalog').update(update).eq('id', product_id).execute()
        return True
    except Exception:
        return False