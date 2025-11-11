#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test CAD preview integration
Tests the complete flow from part_edit_enhanced dialog
"""

import customtkinter as ctk
from unittest.mock import MagicMock
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the dialog
from part_edit_enhanced import EnhancedPartEditDialog


def create_mock_db():
    """Create mock database object"""
    mock_db = MagicMock()
    mock_db.client = MagicMock()

    # Mock customers table
    mock_customers = MagicMock()
    mock_customers.select = MagicMock(return_value=mock_customers)
    mock_customers.order = MagicMock(return_value=mock_customers)
    mock_customers.execute = MagicMock(return_value=MagicMock(data=[
        {'id': '1', 'name': 'Test Customer 1'},
        {'id': '2', 'name': 'Test Customer 2'}
    ]))

    mock_db.client.table = MagicMock()
    mock_db.client.table.return_value = mock_customers

    return mock_db


def test_dialog():
    """Test the enhanced part edit dialog"""
    root = ctk.CTk()
    root.title("Test CAD Preview Integration")
    root.geometry("400x300")

    # Create mock database
    mock_db = create_mock_db()

    def open_new_part():
        """Open dialog for new part"""
        dialog = EnhancedPartEditDialog(
            root,
            mock_db,
            [],
            part_data=None
        )

    def open_edit_part():
        """Open dialog for editing existing part"""
        sample_data = {
            'id': 'test-123',
            'idx': 'TEST-001',
            'name': 'Test Part',
            'description': 'Test Description',
            'unit_id': 'szt',
            'material': 'Steel',
            'surface': 'Painted',
            'cad_2d_file': 'test_sample.dxf',
            'cad_3d_file': None,
            'user_image_file': None,
            'primary_graphic_source': '2D'
        }
        dialog = EnhancedPartEditDialog(
            root,
            mock_db,
            [],
            part_data=sample_data
        )

    # Info label
    info = ctk.CTkLabel(
        root,
        text="Test integracji podglądu CAD\n\nKliknij przycisk aby otworzyć dialog:",
        font=ctk.CTkFont(size=14)
    )
    info.pack(pady=20)

    # Buttons
    btn_frame = ctk.CTkFrame(root)
    btn_frame.pack(pady=20)

    ctk.CTkButton(
        btn_frame,
        text="➕ Nowy produkt",
        command=open_new_part,
        width=150
    ).pack(side="left", padx=10)

    ctk.CTkButton(
        btn_frame,
        text="✏️ Edytuj produkt",
        command=open_edit_part,
        width=150
    ).pack(side="left", padx=10)

    # Status
    status = ctk.CTkLabel(
        root,
        text="ℹ️ W dialogu możesz:\n• Wczytać pliki DXF/DWG/STEP/STL\n• Zobacz podgląd\n• Wygeneruj miniatury",
        font=ctk.CTkFont(size=11),
        text_color="gray60"
    )
    status.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    test_dialog()