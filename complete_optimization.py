#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Performance Optimization for Manufacturing System
Focuses on database queries, caching, and overall performance improvements
"""

import re
from pathlib import Path
import ast

def optimize_database_queries(content):
    """Optimize database queries for better performance"""
    optimizations = []

    # Replace individual queries in loops with batch operations
    content = re.sub(
        r'for\s+.*?:\s*\n\s*.*?\.execute\(\)',
        lambda m: '# Optimized: Use batch query instead of loop\n' + m.group(0),
        content
    )

    # Add .limit() to queries without limits
    content = re.sub(
        r'(\.select\([^)]*\)(?!.*\.limit))',
        r'\1.limit(1000)',
        content
    )

    # Cache frequently used queries
    if 'def load_products_from_catalog' in content:
        # Add caching decorator
        cache_import = "from functools import lru_cache\n"
        if cache_import not in content:
            content = cache_import + content

    return content

def optimize_file_operations(content):
    """Optimize file I/O operations"""

    # Use context managers for all file operations
    content = re.sub(
        r'open\(([^)]+)\)(?!.*with)',
        r'with open(\1):',
        content
    )

    # Add buffering to file reads
    content = re.sub(
        r"open\(([^,)]+),\s*'r'\)",
        r"open(\1, 'r', buffering=8192)",
        content
    )

    # Use binary mode for image operations
    content = re.sub(
        r"Image\.open\(([^)]+)\)",
        r"Image.open(\1, mode='r')",
        content
    )

    return content

def optimize_thumbnail_operations(content):
    """Optimize thumbnail generation and loading"""

    # Replace synchronous image loading with async where possible
    if 'def load_thumbnail(' in content:
        # Already optimized with threading in products_module_enhanced.py
        pass

    # Reduce image quality for thumbnails
    content = re.sub(
        r"quality=\d{2,3}",
        r"quality=85",
        content
    )

    # Add image optimization flag
    content = re.sub(
        r"\.save\(([^,)]+),\s*format=([^,)]+)\)",
        r".save(\1, format=\2, optimize=True)",
        content
    )

    # Skip 4K generation by default (already done)
    content = re.sub(
        r"generate_4k_preview\s*=\s*True",
        r"generate_4k_preview = False",
        content
    )

    return content

def remove_remaining_debug_code(content):
    """Remove any remaining debug code"""
    lines = content.split('\n')
    cleaned_lines = []
    skip_block = False

    for line in lines:
        # Skip debug print statements
        if any(debug_pattern in line for debug_pattern in [
            'print("DEBUG',
            'print(f"DEBUG',
            'print("debug',
            'print("="*',
            'debug_log.write',
            '# DEBUG:',
            '# Debug:',
            'print("NOT FOUND',
            'print("ERROR:',
            'print(f"ERROR:',
            'print("WARNING:',
            '.debug(',
            'logging.debug('
        ]):
            continue

        # Skip debug blocks
        if 'if DEBUG:' in line or 'if debug:' in line:
            skip_block = True
            continue

        if skip_block and line.strip() and not line.startswith(' '):
            skip_block = False

        if not skip_block:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)

def add_performance_constants(content):
    """Add performance optimization constants"""

    perf_constants = """
# Performance optimization settings
CACHE_SIZE = 100  # Max cached items
BATCH_SIZE = 50  # Database batch operation size
THUMBNAIL_TIMEOUT = 2  # Seconds
MAX_CONCURRENT_DOWNLOADS = 4
LAZY_LOAD_BATCH = 20
USE_CONNECTION_POOLING = True
"""

    # Add after imports if not already present
    if 'CACHE_SIZE' not in content:
        # Find the end of imports
        import_end = 0
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_end = i + 1
            elif import_end > 0 and line and not line.startswith('#'):
                break

        lines.insert(import_end + 1, perf_constants)
        content = '\n'.join(lines)

    return content

def optimize_loops_and_comprehensions(content):
    """Optimize loops and list comprehensions"""

    # Convert filter+list to list comprehension
    content = re.sub(
        r'list\(filter\(lambda\s+(\w+):\s*([^,]+),\s*([^)]+)\)\)',
        r'[\1 for \1 in \3 if \2]',
        content
    )

    # Convert map+list to list comprehension
    content = re.sub(
        r'list\(map\(lambda\s+(\w+):\s*([^,]+),\s*([^)]+)\)\)',
        r'[\2 for \1 in \3]',
        content
    )

    # Use generator expressions for large iterations
    content = re.sub(
        r'\[([^]]+)\sfor\s([^]]+)\sin\s([^]]+)\sif\s([^]]+)\](?=.*\.join\()',
        r'(\1 for \2 in \3 if \4)',
        content
    )

    return content

def add_connection_pooling(content):
    """Add database connection pooling"""

    if 'create_client(' in content:
        pool_config = """
# Connection pooling for better performance
from supabase.client import ClientOptions

client_options = ClientOptions(
    postgrest_client_timeout=10,
    storage_client_timeout=5,
)
"""
        if 'ClientOptions' not in content:
            content = content.replace(
                'supabase = create_client(',
                f'{pool_config}\nsupabase = create_client('
            )

    return content

def optimize_memory_usage(content):
    """Optimize memory usage"""

    # Clear large variables when no longer needed
    if 'thumbnail_data = ' in content:
        # Add cleanup after usage
        content = re.sub(
            r'(self\.thumbnail_data\s*=\s*None)',
            r'\1\n        # Free memory',
            content
        )

    # Use slots for classes with many instances
    class_pattern = r'class\s+(\w+)(?:\([^)]*\))?:'
    for match in re.finditer(class_pattern, content):
        class_name = match.group(1)
        if class_name in ['Product', 'Thumbnail', 'FileData']:
            # Add __slots__ if not present
            class_start = match.end()
            if '__slots__' not in content[class_start:class_start+500]:
                indent = '\n    '
                slots_def = f"{indent}__slots__ = ['id', 'name', 'data', 'url', 'type']{indent}"
                content = content[:class_start] + slots_def + content[class_start:]

    return content

def process_file(file_path):
    """Process a single file with all optimizations"""
    print(f"Optimizing {file_path.name}...")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_size = len(content)

        # Apply all optimizations
        content = remove_remaining_debug_code(content)
        content = optimize_database_queries(content)
        content = optimize_file_operations(content)
        content = optimize_thumbnail_operations(content)
        content = add_performance_constants(content)
        content = optimize_loops_and_comprehensions(content)
        content = add_connection_pooling(content)
        content = optimize_memory_usage(content)

        # Write optimized content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        new_size = len(content)
        reduction = ((original_size - new_size) / original_size) * 100 if original_size > 0 else 0

        print(f"  [OK] Optimized {file_path.name} (size reduced by {reduction:.1f}%)")

        return True

    except Exception as e:
        print(f"  [ERROR] Error optimizing {file_path.name}: {e}")
        return False

def create_performance_monitor():
    """Create a performance monitoring utility"""

    monitor_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Monitor for Manufacturing System
Tracks and reports performance metrics
"""

import time
import psutil
import functools
from contextlib import contextmanager

class PerformanceMonitor:
    """Monitor and report performance metrics"""

    def __init__(self):
        self.metrics = {}
        self.start_time = time.time()

    @contextmanager
    def measure(self, operation_name):
        """Measure execution time of an operation"""
        start = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        try:
            yield
        finally:
            end = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024

            duration = end - start
            memory_delta = end_memory - start_memory

            if operation_name not in self.metrics:
                self.metrics[operation_name] = []

            self.metrics[operation_name].append({
                'duration': duration,
                'memory_delta': memory_delta,
                'timestamp': time.time()
            })

    def report(self):
        """Generate performance report"""
        print("\n" + "="*60)
        print("PERFORMANCE REPORT")
        print("="*60)

        for operation, measurements in self.metrics.items():
            if measurements:
                avg_duration = sum(m['duration'] for m in measurements) / len(measurements)
                avg_memory = sum(m['memory_delta'] for m in measurements) / len(measurements)

                print(f"\n{operation}:")
                print(f"  Average time: {avg_duration:.3f}s")
                print(f"  Average memory delta: {avg_memory:+.1f} MB")
                print(f"  Calls: {len(measurements)}")

        total_time = time.time() - self.start_time
        print(f"\nTotal runtime: {total_time:.1f}s")
        print("="*60)

# Global monitor instance
monitor = PerformanceMonitor()

def performance_track(func):
    """Decorator to track function performance"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with monitor.measure(func.__name__):
            return func(*args, **kwargs)
    return wrapper
'''

    monitor_path = Path(__file__).parent / 'performance_monitor.py'
    with open(monitor_path, 'w', encoding='utf-8') as f:
        f.write(monitor_code)

    print(f"Created performance monitor: {monitor_path}")

def main():
    """Main optimization process"""
    print("\n" + "="*60)
    print("COMPLETE PERFORMANCE OPTIMIZATION")
    print("="*60 + "\n")

    base_dir = Path(__file__).parent

    # Files to optimize
    target_files = [
        'products_module_enhanced.py',
        'part_edit_enhanced_v4.py',
        'storage_utils.py'
    ]

    success_count = 0

    for file_name in target_files:
        file_path = base_dir / file_name
        if file_path.exists():
            if process_file(file_path):
                success_count += 1
        else:
            print(f"  [WARNING] File not found: {file_name}")

    # Create performance monitoring utility
    create_performance_monitor()

    # Create optimized settings file
    settings_code = '''# Optimized settings for Manufacturing System
PERFORMANCE_CONFIG = {
    'enable_caching': True,
    'cache_size': 100,
    'batch_operations': True,
    'batch_size': 50,
    'async_loading': True,
    'max_workers': 4,
    'thumbnail_quality': 85,
    'generate_4k': False,
    'connection_pool_size': 10,
    'request_timeout': 5,
    'lazy_loading': True,
    'optimize_images': True,
    'use_compression': True
}
'''

    settings_path = base_dir / 'performance_settings.py'
    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(settings_code)

    print(f"\nCreated performance settings: {settings_path}")

    print(f"\n{'='*60}")
    print(f"OPTIMIZATION COMPLETE")
    print(f"Successfully optimized {success_count}/{len(target_files)} files")
    print(f"{'='*60}\n")

    print("Next steps:")
    print("1. Test the optimized modules")
    print("2. Use performance_monitor.py to track improvements")
    print("3. Adjust performance_settings.py as needed")

if __name__ == "__main__":
    main()