#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Monitor for Manufacturing System
Tracks and reports performance metrics
"""

import time
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

        try:
            yield
        finally:
            end = time.time()

            duration = end - start
            memory_delta = 0  # Memory tracking removed (requires psutil)

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

                print(f"\n{operation}:")
                print(f"  Average time: {avg_duration:.3f}s")
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
