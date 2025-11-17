#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Settings Manager for Manufacturing System
Manages application settings including logos, company info, and report preferences
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, field
import shutil
from PIL import Image
import io

@dataclass
class ApplicationSettings:
    """Application settings data structure"""
    # Company Information
    company_name: str = "Manufacturing System"
    company_address: str = ""
    company_phone: str = ""
    company_email: str = ""
    company_nip: str = ""
    company_regon: str = ""

    # Logo settings
    manufacturer_logo_path: str = "logo.jpg"
    user_logo_path: str = ""
    use_user_logo: bool = False

    # Report settings
    report_include_thumbnails: bool = True
    report_thumbnail_size: tuple = field(default_factory=lambda: (60, 40))
    report_include_details: bool = True
    report_language: str = "pl"  # pl or en

    # PDF settings
    pdf_orientation: str = "portrait"  # portrait or landscape
    pdf_page_size: str = "A4"
    pdf_include_watermark: bool = False
    pdf_watermark_text: str = "DRAFT"

    # Email settings
    email_smtp_server: str = ""
    email_smtp_port: int = 587
    email_smtp_user: str = ""
    email_from_address: str = ""
    email_signature: str = ""

    # Display settings
    list_show_thumbnails: bool = True
    list_thumbnail_size: tuple = field(default_factory=lambda: (50, 50))
    theme_mode: str = "dark"  # dark, light, or system
    color_theme: str = "blue"  # blue, green, dark-blue

    # Export settings
    export_format: str = "xlsx"  # xlsx, pdf, docx
    export_include_attachments: bool = True
    export_compress_images: bool = True
    export_image_quality: int = 85  # 1-100

    # System settings
    auto_save_interval: int = 300  # seconds
    backup_enabled: bool = True
    backup_retention_days: int = 30
    log_level: str = "INFO"

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationSettings':
        """Create settings from dictionary"""
        # Filter out unknown keys
        valid_keys = cls.__dataclass_fields__.keys()
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)


class SettingsManager:
    """Manages application settings with persistence"""

    def __init__(self, app_dir: Optional[str] = None):
        """
        Initialize settings manager

        Args:
            app_dir: Application directory path. If None, uses current directory
        """
        if app_dir:
            self.app_dir = Path(app_dir)
        else:
            self.app_dir = Path.cwd()

        self.settings_dir = self.app_dir / "settings"
        self.settings_file = self.settings_dir / "app_settings.json"
        self.logos_dir = self.settings_dir / "logos"

        # Create directories if they don't exist
        self.settings_dir.mkdir(exist_ok=True)
        self.logos_dir.mkdir(exist_ok=True)

        # Load or create settings
        self.settings = self._load_settings()

        # Copy manufacturer logo if it exists in root
        self._setup_manufacturer_logo()

    def _load_settings(self) -> ApplicationSettings:
        """Load settings from file or create default"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return ApplicationSettings.from_dict(data)
            except Exception as e:
                print(f"Error loading settings: {e}")
                return ApplicationSettings()
        return ApplicationSettings()

    def save_settings(self) -> bool:
        """
        Save current settings to file

        Returns:
            bool: True if successful
        """
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def _setup_manufacturer_logo(self):
        """Copy manufacturer logo from root to settings directory if exists"""
        root_logo = self.app_dir / "logo.jpg"
        if root_logo.exists():
            dest_logo = self.logos_dir / "manufacturer_logo.jpg"
            if not dest_logo.exists():
                try:
                    shutil.copy2(root_logo, dest_logo)
                    self.settings.manufacturer_logo_path = str(dest_logo)
                    self.save_settings()
                except Exception as e:
                    print(f"Error copying manufacturer logo: {e}")

    def set_user_logo(self, logo_path: str) -> bool:
        """
        Set user logo by copying it to logos directory

        Args:
            logo_path: Path to user logo file

        Returns:
            bool: True if successful
        """
        try:
            source = Path(logo_path)
            if not source.exists():
                return False

            # Validate image
            try:
                img = Image.open(source)
                img.verify()
            except:
                return False

            # Copy to logos directory with unique name
            ext = source.suffix
            dest = self.logos_dir / f"user_logo{ext}"

            # Resize if too large (max 500x500)
            img = Image.open(source)
            if img.width > 500 or img.height > 500:
                img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                img.save(dest)
            else:
                shutil.copy2(source, dest)

            self.settings.user_logo_path = str(dest)
            self.settings.use_user_logo = True
            return self.save_settings()

        except Exception as e:
            print(f"Error setting user logo: {e}")
            return False

    def get_active_logo_path(self) -> Optional[str]:
        """
        Get path to currently active logo

        Returns:
            str: Path to logo file or None
        """
        if self.settings.use_user_logo and self.settings.user_logo_path:
            if Path(self.settings.user_logo_path).exists():
                return self.settings.user_logo_path

        if self.settings.manufacturer_logo_path:
            if Path(self.settings.manufacturer_logo_path).exists():
                return self.settings.manufacturer_logo_path

        # Fallback to root logo.jpg
        root_logo = self.app_dir / "logo.jpg"
        if root_logo.exists():
            return str(root_logo)

        return None

    def get_logo_image(self, size: Optional[tuple] = None) -> Optional[Image.Image]:
        """
        Get logo as PIL Image object

        Args:
            size: Optional (width, height) to resize

        Returns:
            PIL.Image or None
        """
        logo_path = self.get_active_logo_path()
        if not logo_path:
            return None

        try:
            img = Image.open(logo_path)
            if size:
                img.thumbnail(size, Image.Resampling.LANCZOS)
            return img
        except Exception as e:
            print(f"Error loading logo image: {e}")
            return None

    def reset_to_manufacturer_logo(self):
        """Reset to use manufacturer logo"""
        self.settings.use_user_logo = False
        self.save_settings()

    def update_company_info(self, **kwargs):
        """
        Update company information

        Args:
            **kwargs: Company info fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        self.save_settings()

    def update_report_settings(self, **kwargs):
        """
        Update report generation settings

        Args:
            **kwargs: Report settings to update
        """
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        self.save_settings()

    def export_settings(self, filepath: str) -> bool:
        """
        Export settings to file

        Args:
            filepath: Path to export file

        Returns:
            bool: True if successful
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.settings.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting settings: {e}")
            return False

    def import_settings(self, filepath: str) -> bool:
        """
        Import settings from file

        Args:
            filepath: Path to import file

        Returns:
            bool: True if successful
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.settings = ApplicationSettings.from_dict(data)
                return self.save_settings()
        except Exception as e:
            print(f"Error importing settings: {e}")
            return False


# Global settings instance
_settings_manager: Optional[SettingsManager] = None

def get_settings_manager() -> SettingsManager:
    """Get global settings manager instance"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager

def initialize_settings(app_dir: Optional[str] = None):
    """Initialize global settings manager"""
    global _settings_manager
    _settings_manager = SettingsManager(app_dir)
    return _settings_manager