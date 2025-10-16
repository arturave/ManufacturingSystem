#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Processing Utilities
Handles image resizing, thumbnails, and clipboard operations
"""

import io
import os
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageGrab, ImageTk, ImageDraw, ImageFont
import tkinter as tk

# Constants
HIGH_RES_MAX_SIZE = (1920, 1080)  # HD resolution
LOW_RES_SIZE = (200, 200)  # Thumbnail size
SUPPORTED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp'}


class ImageProcessor:
    """Handles all image processing operations"""

    @staticmethod
    def is_image_file(file_path: str) -> bool:
        """Check if file is a supported image format"""
        ext = Path(file_path).suffix.lower()
        return ext in SUPPORTED_IMAGE_FORMATS

    @staticmethod
    def resize_image(
        image: Image.Image,
        max_size: Tuple[int, int],
        maintain_aspect: bool = True
    ) -> Image.Image:
        """
        Resize image to fit within max_size while maintaining aspect ratio

        Args:
            image: PIL Image object
            max_size: (width, height) maximum dimensions
            maintain_aspect: If True, maintain aspect ratio

        Returns:
            Resized PIL Image
        """
        if maintain_aspect:
            # Calculate aspect ratio
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            return image
        else:
            return image.resize(max_size, Image.Resampling.LANCZOS)

    @staticmethod
    def create_high_res(image: Image.Image) -> Image.Image:
        """Create high-resolution version (max HD)"""
        return ImageProcessor.resize_image(image, HIGH_RES_MAX_SIZE)

    @staticmethod
    def create_low_res(image: Image.Image) -> Image.Image:
        """Create low-resolution thumbnail (200x200)"""
        return ImageProcessor.resize_image(image, LOW_RES_SIZE)

    @staticmethod
    def load_image_from_file(file_path: str) -> Optional[Image.Image]:
        """
        Load image from file

        Args:
            file_path: Path to image file

        Returns:
            PIL Image or None if failed
        """
        try:
            img = Image.open(file_path)
            # Convert to RGB if necessary (handles RGBA, P, etc.)
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            return img
        except Exception as e:
            print(f"Error loading image from {file_path}: {e}")
            return None

    @staticmethod
    def load_image_from_clipboard() -> Optional[Image.Image]:
        """
        Load image from clipboard (Ctrl+V support)

        Returns:
            PIL Image or None if no image in clipboard
        """
        try:
            img = ImageGrab.grabclipboard()
            if img is None:
                return None

            # Convert to RGB if necessary
            if isinstance(img, Image.Image):
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                return img

            return None
        except Exception as e:
            print(f"Error loading image from clipboard: {e}")
            return None

    @staticmethod
    def save_image(image: Image.Image, output_path: str, quality: int = 95) -> bool:
        """
        Save image to file

        Args:
            image: PIL Image object
            output_path: Output file path
            quality: JPEG quality (1-100)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure parent directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Save with appropriate format
            ext = Path(output_path).suffix.lower()
            if ext in ['.jpg', '.jpeg']:
                image.save(output_path, 'JPEG', quality=quality, optimize=True)
            elif ext == '.png':
                image.save(output_path, 'PNG', optimize=True)
            else:
                image.save(output_path, quality=quality)

            return True
        except Exception as e:
            print(f"Error saving image to {output_path}: {e}")
            return False

    @staticmethod
    def process_and_save_both(
        image: Image.Image,
        base_path: str,
        filename_prefix: str = "image"
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Process image and save both high-res and low-res versions

        Args:
            image: PIL Image object
            base_path: Directory to save images
            filename_prefix: Prefix for filenames

        Returns:
            Tuple of (high_res_path, low_res_path) or (None, None) if failed
        """
        try:
            # Create directory if it doesn't exist
            Path(base_path).mkdir(parents=True, exist_ok=True)

            # Generate filenames
            high_res_path = os.path.join(base_path, f"{filename_prefix}_high_res.png")
            low_res_path = os.path.join(base_path, f"{filename_prefix}_low_res.png")

            # Create and save high-res version
            high_res_img = ImageProcessor.create_high_res(image.copy())
            if not ImageProcessor.save_image(high_res_img, high_res_path):
                return None, None

            # Create and save low-res version
            low_res_img = ImageProcessor.create_low_res(image.copy())
            if not ImageProcessor.save_image(low_res_img, low_res_path):
                return None, None

            return high_res_path, low_res_path

        except Exception as e:
            print(f"Error processing and saving images: {e}")
            return None, None

    @staticmethod
    def create_photoimage(image: Image.Image, max_size: Optional[Tuple[int, int]] = None) -> ImageTk.PhotoImage:
        """
        Create Tkinter PhotoImage from PIL Image

        Args:
            image: PIL Image object
            max_size: Optional maximum size to resize to

        Returns:
            ImageTk.PhotoImage for display in Tkinter
        """
        if max_size:
            image = ImageProcessor.resize_image(image.copy(), max_size)
        return ImageTk.PhotoImage(image)

    @staticmethod
    def create_placeholder_image(
        size: Tuple[int, int] = (200, 200),
        text: str = "Brak grafiki"
    ) -> Image.Image:
        """
        Create a placeholder image with text

        Args:
            size: Image size (width, height)
            text: Text to display

        Returns:
            PIL Image
        """
        img = Image.new('RGB', size, color='#2b2b2b')
        draw = ImageDraw.Draw(img)

        # Try to use a nice font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()

        # Calculate text position (center)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)

        # Draw text
        draw.text(position, text, fill='#666666', font=font)

        return img

    @staticmethod
    def get_image_info(image: Image.Image) -> dict:
        """
        Get information about an image

        Args:
            image: PIL Image object

        Returns:
            Dictionary with image information
        """
        return {
            'width': image.width,
            'height': image.height,
            'mode': image.mode,
            'format': image.format,
            'size_bytes': len(image.tobytes())
        }

    @staticmethod
    def determine_resolution_type(image: Image.Image) -> str:
        """
        Determine if image should be treated as high-res or low-res

        Args:
            image: PIL Image object

        Returns:
            'high_res' or 'low_res'
        """
        width, height = image.size

        # If either dimension is larger than low-res size, it's high-res
        if width > LOW_RES_SIZE[0] or height > LOW_RES_SIZE[1]:
            return 'high_res'
        else:
            return 'low_res'


class ImageCache:
    """Simple cache for loaded images to avoid repeated disk I/O"""

    def __init__(self, max_size: int = 50):
        self.cache = {}
        self.max_size = max_size

    def get(self, path: str) -> Optional[Image.Image]:
        """Get image from cache"""
        return self.cache.get(path)

    def put(self, path: str, image: Image.Image):
        """Put image in cache"""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry (simple FIFO)
            oldest = next(iter(self.cache))
            del self.cache[oldest]

        self.cache[path] = image

    def clear(self):
        """Clear all cached images"""
        self.cache.clear()


# Global image cache instance
_image_cache = ImageCache()


def get_cached_image(path: str) -> Optional[Image.Image]:
    """
    Get image from cache or load from disk

    Args:
        path: Path to image file

    Returns:
        PIL Image or None
    """
    # Check cache first
    img = _image_cache.get(path)
    if img is not None:
        return img

    # Load from disk
    img = ImageProcessor.load_image_from_file(path)
    if img is not None:
        _image_cache.put(path, img)

    return img


def clear_image_cache():
    """Clear the global image cache"""
    _image_cache.clear()
