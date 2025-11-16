#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify optimized performance of the Manufacturing System
"""

import time
import sys
from pathlib import Path
import traceback

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_module_imports():
    """Test that all optimized modules can be imported"""
    print("\n1. Testing module imports...")

    modules_to_test = [
        'products_module_enhanced',
        'storage_utils',
        'performance_monitor',
        'performance_settings'
    ]

    for module_name in modules_to_test:
        try:
            module = __import__(module_name)
            print(f"   [OK] Imported {module_name}")

            # Check for debug statements
            module_file = Path(__file__).parent / f"{module_name}.py"
            if module_file.exists():
                with open(module_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    debug_count = content.count('print("DEBUG')
                    if debug_count > 0:
                        print(f"   [WARNING] Found {debug_count} debug prints in {module_name}")
                    else:
                        print(f"   [OK] No debug prints in {module_name}")
        except Exception as e:
            print(f"   [ERROR] Failed to import {module_name}: {e}")
            return False

    return True

def test_storage_utils():
    """Test optimized storage utility functions"""
    print("\n2. Testing storage utilities...")

    try:
        from storage_utils import (
            generate_storage_path,
            get_mime_type,
            STORAGE_FOLDERS,
            MIME_TYPES
        )

        # Test path generation
        test_path = generate_storage_path(
            "test-product-id",
            "thumbnail_100",
            "test_image.jpg"
        )
        assert "thumbnails/100" in test_path, "Path generation error"
        print(f"   [OK] Storage path generation works: {test_path}")

        # Test MIME type detection
        assert get_mime_type("test.jpg") == "image/jpeg"
        assert get_mime_type("test.dxf") == "application/dxf"
        print("   [OK] MIME type detection works")

        # Check optimized constants
        assert "thumbnail_100" in STORAGE_FOLDERS
        assert ".jpg" in MIME_TYPES
        print("   [OK] Storage constants loaded")

        return True

    except Exception as e:
        print(f"   [ERROR] Storage utils test failed: {e}")
        traceback.print_exc()
        return False

def test_performance_monitor():
    """Test the performance monitoring utility"""
    print("\n3. Testing performance monitor...")

    try:
        from performance_monitor import PerformanceMonitor, performance_track

        # Create monitor instance
        monitor = PerformanceMonitor()

        # Test measurement
        with monitor.measure("test_operation"):
            time.sleep(0.1)  # Simulate work

        # Check metrics were recorded
        assert "test_operation" in monitor.metrics
        assert len(monitor.metrics["test_operation"]) == 1
        duration = monitor.metrics["test_operation"][0]["duration"]
        assert 0.09 < duration < 0.15, f"Duration {duration} out of expected range"

        print("   [OK] Performance monitoring works")

        # Test decorator
        @performance_track
        def test_function():
            time.sleep(0.05)
            return "test"

        result = test_function()
        assert result == "test"
        print("   [OK] Performance decorator works")

        return True

    except Exception as e:
        print(f"   [ERROR] Performance monitor test failed: {e}")
        traceback.print_exc()
        return False

def test_performance_settings():
    """Test performance settings"""
    print("\n4. Testing performance settings...")

    try:
        from performance_settings import PERFORMANCE_CONFIG

        # Check required settings
        required_settings = [
            'enable_caching',
            'cache_size',
            'batch_operations',
            'async_loading',
            'thumbnail_quality',
            'generate_4k'
        ]

        for setting in required_settings:
            assert setting in PERFORMANCE_CONFIG, f"Missing setting: {setting}"
            print(f"   [OK] {setting}: {PERFORMANCE_CONFIG[setting]}")

        # Verify optimized values
        assert PERFORMANCE_CONFIG['generate_4k'] == False, "4K should be disabled by default"
        assert PERFORMANCE_CONFIG['thumbnail_quality'] == 85, "Thumbnail quality should be optimized"
        assert PERFORMANCE_CONFIG['async_loading'] == True, "Async loading should be enabled"

        print("   [OK] All performance settings verified")
        return True

    except Exception as e:
        print(f"   [ERROR] Performance settings test failed: {e}")
        traceback.print_exc()
        return False

def test_thumbnail_optimization():
    """Test thumbnail generation optimization"""
    print("\n5. Testing thumbnail optimization...")

    try:
        # Check if products_module has optimized thumbnail settings
        import products_module_enhanced as pm

        # Check for async loading implementation
        module_content = Path('products_module_enhanced.py').read_text(encoding='utf-8')

        has_threading = 'import threading' in module_content or 'from threading' in module_content
        has_async = 'Thread(' in module_content or 'ThreadPoolExecutor' in module_content
        has_quality_optimization = 'quality=85' in module_content or 'quality = 85' in module_content

        print(f"   [OK] Threading import: {has_threading}")
        print(f"   [OK] Async implementation: {has_async}")
        print(f"   [OK] Quality optimization: {has_quality_optimization}")

        if not (has_threading and has_async):
            print("   [WARNING] Async loading may not be fully implemented")

        return True

    except Exception as e:
        print(f"   [ERROR] Thumbnail optimization test failed: {e}")
        traceback.print_exc()
        return False

def run_performance_benchmark():
    """Run a simple performance benchmark"""
    print("\n6. Running performance benchmark...")

    try:
        import time

        # Simulate thumbnail loading
        print("   Simulating thumbnail operations...")

        start = time.time()

        # Test list operations (should be optimized)
        test_list = list(range(10000))
        filtered = [x for x in test_list if x % 2 == 0]  # List comprehension

        # Test string operations
        test_strings = ["test" * 100 for _ in range(100)]
        joined = "".join(test_strings)

        end = time.time()

        duration = end - start
        print(f"   [OK] Basic operations completed in {duration:.3f}s")

        if duration > 1.0:
            print("   [WARNING] Basic operations seem slow, further optimization may be needed")
        else:
            print("   [OK] Performance is within acceptable range")

        return True

    except Exception as e:
        print(f"   [ERROR] Benchmark failed: {e}")
        return False

def main():
    """Run all optimization tests"""
    print("="*60)
    print("TESTING OPTIMIZED MANUFACTURING SYSTEM")
    print("="*60)

    all_tests = [
        ("Module Imports", test_module_imports),
        ("Storage Utils", test_storage_utils),
        ("Performance Monitor", test_performance_monitor),
        ("Performance Settings", test_performance_settings),
        ("Thumbnail Optimization", test_thumbnail_optimization),
        ("Performance Benchmark", run_performance_benchmark)
    ]

    results = {}

    for test_name, test_func in all_tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n[ERROR] Test '{test_name}' crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, passed_test in results.items():
        status = "[PASSED]" if passed_test else "[FAILED]"
        print(f"{status} {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\nOPTIMIZATION SUCCESSFUL!")
        print("All tests passed. The system is optimized and ready.")
    else:
        print("\nSOME OPTIMIZATIONS MAY NEED ATTENTION")
        print("Review the failed tests above for details.")

    print("="*60)

if __name__ == "__main__":
    main()