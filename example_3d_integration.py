#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example integration of render3d module with part management
Shows how to use auto_thumbnail_on_part_create hook
"""

import os
from render3d import auto_thumbnail_on_part_create

# Get Supabase credentials from environment
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

def example_part_creation(model_path: str, part_id: str, order_process_no: str):
    """
    Example function showing how to integrate 3D rendering
    after creating a new part in the database
    """

    # Step 1: Create part in database (your existing code)
    # ... existing part creation code ...
    # part_id = create_part_in_database(...)

    # Step 2: Define callback for updating database with URLs
    def on_success_update_db(meta: dict):
        """
        This callback will be called after successful rendering and upload.
        Update your part record with the generated URLs.
        """
        # Example using Supabase client
        from supabase import create_client

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Update part record with generated URLs
        supabase.table("parts").update({
            "thumb_url": meta["thumb_png_url"],
            "image_url": meta["full_png_url"],
            "thumb_storage_path": meta["thumb_png_storage_path"],
            "image_storage_path": meta["full_png_storage_path"],
            "bounding_box": meta.get("bounding_box")  # Store dimensions if available
        }).eq("id", part_id).execute()

        print(f"✓ Part {part_id} updated with 3D preview URLs")

    # Step 3: Define error handler (optional)
    def on_error_log(msg: str):
        """Log errors to your logging system"""
        print(f"❌ Error generating 3D preview: {msg}")
        # You could also store this in a log table or file

    # Step 4: Call the auto thumbnail hook
    result = auto_thumbnail_on_part_create(
        model_path=model_path,
        part_id=part_id,
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY,
        order_process_no=order_process_no,
        on_success_update_db=on_success_update_db,
        on_error_log=on_error_log
    )

    return result


def example_integration_in_part_edit_dialog():
    """
    Example of how to integrate in EnhancedPartEditDialog
    """

    # In your save_part method of EnhancedPartEditDialog:

    # After saving the part to database and getting the part_id:
    """
    if self.documentation_path and CADProcessor.is_3d_file(self.documentation_path):
        # Process 3D file and upload
        from render3d import auto_thumbnail_on_part_create

        def update_part_urls(meta):
            # Update the part record with URLs
            self.db.update_part(part_id, {
                'thumb_url': meta['thumb_png_url'],
                'image_url': meta['full_png_url']
            })

        auto_thumbnail_on_part_create(
            model_path=self.documentation_path,
            part_id=part_id,
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY,
            order_process_no=self.order_id,
            on_success_update_db=update_part_urls,
            on_error_log=lambda msg: print(f"3D render error: {msg}")
        )
    """


# Example usage
if __name__ == "__main__":
    import sys

    print("3D Rendering Integration Example")
    print("=" * 60)

    if len(sys.argv) < 2:
        print("Usage: python example_3d_integration.py <path_to_step_or_iges_file>")
        sys.exit(1)

    model_file = sys.argv[1]

    if not os.path.exists(model_file):
        print(f"Error: File not found: {model_file}")
        sys.exit(1)

    # Example part data
    part_id = "EXAMPLE-001"
    order_process_no = "2025-00001"

    print(f"\nProcessing 3D file: {model_file}")
    print(f"Part ID: {part_id}")
    print(f"Order Process No: {order_process_no}")
    print()

    # Run the example
    result = example_part_creation(model_file, part_id, order_process_no)

    if result:
        print("\n✅ Success! 3D preview generated and uploaded")
        print(f"   Full URL: {result['full_png_url']}")
        print(f"   Thumb URL: {result['thumb_png_url']}")
        if result.get('bounding_box'):
            bbox = result['bounding_box']
            print(f"\n   Dimensions:")
            print(f"   - Width: {bbox['width']:.2f} mm")
            print(f"   - Height: {bbox['height']:.2f} mm")
            print(f"   - Depth: {bbox['depth']:.2f} mm")
    else:
        print("\n❌ Failed to generate 3D preview")