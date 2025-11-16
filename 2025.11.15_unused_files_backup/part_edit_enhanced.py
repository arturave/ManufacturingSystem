#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Part Edit Dialog - Wrapper for V4
This module provides backward compatibility by importing the latest version
"""

# Import the enhanced V4 version
from part_edit_enhanced_v4 import EnhancedPartEditDialogV4 as EnhancedPartEditDialog

# For backward compatibility
__all__ = ['EnhancedPartEditDialog']