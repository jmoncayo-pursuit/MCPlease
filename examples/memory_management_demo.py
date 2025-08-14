#!/usr/bin/env python3
"""
Memory Management Demo for MCPlease MVP

This script demonstrates the memory management and optimization capabilities
of the AI model system, including:
- Real-time memory monitoring
- Automatic quantization selection
- Graceful degradation under memory pressure
- Memory optimization recommendations
"""

import asyncio
import time
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.models.memory import (
    MemoryMonitor, MemoryOptimizer, MemoryPressure,
    QuantizationSelector, GracefulDegradation
)


def print_separator(title: str):
    """Print a formatted separator."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_memory_stats(stats):
    """Print formatted memory statistics."""
    print(f"Total Memory:     {stats.total_gb:.1f} GB")
    print(f"Available Memory: {stats.available_gb:.1f} GB")
    print(f"Used Memory:      {stats.used_gb:.1f} GB ({stats.used_percent:.1%})")
    print(f"GPU Memory:       {stats.gpu_total_gb:.1f} GB")
    print(f"GPU Available:    {stats.gpu_available_gb:.1f} GB")
    print(f"Pressure Level:   {stats.pressure_level.value.upper()}")


def print_quantization_options(options):
    """Print formatted quantization options."""
    if not options:
        print("No compatible quantization options found!")
        return
    
    print(f"{'Name':<8} {'Memory':<10} {'Quality':<8} {'Description'}")
    print("-" * 60)
    for opt in options:
        print(f"{opt.name:<8} {opt.memory_requirement_gb:<10.1f} {opt.quality_score:<8.2f} {opt.description}")


async def demonstrate_memory_monitoring():
    """Demonstrate real-time memory monitoring."""
    print_separator("Memory Monitoring Demo")
    
    monitor = MemoryMonitor(check_interval=0.5)
    
    # Get initial stats
    stats = monitor.get_current_stats()
    print("Current Memory Status:")
    print_memory_stats(stats)
    
    # Set up callback to track changes
    pressure_changes = []
    
    def track_pressure(stats):
        if not pressure_changes or pressure_changes[-1] != stats.pressure_level:
            pressure_changes.append(stats.pressure_level)
            print(f"\n[{time.strftime('%H:%M:%S')}] Memory pressure: {stats.pressure_level.value}")
    
    monitor.add_callback(track_pressure)
    
    print("\nStarting memory monitoring for 3 seconds...")
    monitor.start_monitoring()
    
    await asyncio.sleep(3.0)
    
    monitor.stop_monitoring()
    print(f"Monitoring stopped. Detected {len(pressure_changes)} pressure level changes.")


def demonstrate_quantization_selection():
    """Demonstrate automatic quantization selection."""
    print_separator("Quantization Selection Demo")
    
    selector = QuantizationSelector()
    
    # Test different memory scenarios
    memory_scenarios = [
        ("High Memory System (32GB)", 32.0),
        ("Medium Memory System (16GB)", 16.0),
        ("Low Memory System (8GB)", 8.0),
        ("Very Low Memory System (4GB)", 4.0)
    ]
    
    for scenario_name, available_memory in memory_scenarios:
        print(f"\n{scenario_name}:")
        print(f"Available Memory: {available_memory:.1f} GB")
        
        # Get optimal quantization
        optimal = selector.select_optimal_quantization(
            available_memory_gb=available_memory,
            prefer_quality=True
        )
        
        if optimal:
            print(f"Recommended: {optimal.name} (Quality: {optimal.quality_score:.2f}, Memory: {optimal.memory_requirement_gb:.1f}GB)")
        else:
            print("No compatible quantization found!")
        
        # Show all compatible options
        compatible = selector.get_all_compatible_options(available_memory)
        if compatible:
            print(f"All compatible options ({len(compatible)}):")
            print_quantization_options(compatible)


async def demonstrate_graceful_degradation():
    """Demonstrate graceful degradation under memory pressure."""
    print_separator("Graceful Degradation Demo")
    
    monitor = MemoryMonitor()
    degradation = GracefulDegradation(monitor)
    
    # Start with an aggressive configuration
    original_config = {
        "model_name": "openai/gpt-oss-20b",
        "max_model_len": 8192,
        "quantization": "bf16",
        "gpu_memory_utilization": 0.9,
        "max_num_batched_tokens": 8192,
        "cpu_offload": False
    }
    
    print("Original Configuration:")
    for key, value in original_config.items():
        print(f"  {key}: {value}")
    
    # Test degradation under different pressure levels
    pressure_levels = [
        MemoryPressure.MODERATE,
        MemoryPressure.HIGH,
        MemoryPressure.CRITICAL
    ]
    
    current_config = original_config.copy()
    
    for pressure in pressure_levels:
        print(f"\nApplying degradation for {pressure.value.upper()} memory pressure:")
        
        degraded_config = await degradation.handle_memory_pressure(
            current_config, pressure
        )
        
        # Show changes
        changes = []
        for key, new_value in degraded_config.items():
            old_value = current_config.get(key)
            if old_value != new_value:
                changes.append(f"  {key}: {old_value} → {new_value}")
        
        if changes:
            print("Changes applied:")
            for change in changes:
                print(change)
        else:
            print("No changes needed.")
        
        current_config = degraded_config


def demonstrate_memory_optimization():
    """Demonstrate complete memory optimization workflow."""
    print_separator("Memory Optimization Demo")
    
    optimizer = MemoryOptimizer()
    
    # Get memory report
    report = optimizer.get_memory_report()
    
    print("Current System Status:")
    stats = report["current_stats"]
    print(f"Memory: {stats['available_memory_gb']:.1f}GB available / {stats['total_memory_gb']:.1f}GB total")
    print(f"Usage: {stats['used_percent']:.1%}")
    print(f"Pressure: {stats['pressure_level'].upper()}")
    
    print(f"\nCompatible Quantizations ({len(report['compatible_quantizations'])}):")
    if report['compatible_quantizations']:
        for quant in report['compatible_quantizations']:
            print(f"  {quant['name']}: {quant['memory_requirement_gb']:.1f}GB, Quality: {quant['quality_score']:.2f}")
    else:
        print("  None found!")
    
    print(f"\nRecommendations ({len(report['recommendations'])}):")
    for rec in report['recommendations']:
        print(f"  • {rec}")
    
    # Test configuration optimization
    print("\nConfiguration Optimization:")
    base_config = {
        "model_name": "openai/gpt-oss-20b",
        "max_model_len": 4096,
        "quantization": "auto",
        "gpu_memory_utilization": 0.8
    }
    
    print("Base configuration:")
    for key, value in base_config.items():
        print(f"  {key}: {value}")
    
    optimized_config = optimizer.get_optimal_config(base_config)
    
    print("\nOptimized configuration:")
    for key, value in optimized_config.items():
        print(f"  {key}: {value}")
    
    # Show what changed
    changes = []
    for key, new_value in optimized_config.items():
        old_value = base_config.get(key)
        if old_value != new_value:
            changes.append(f"  {key}: {old_value} → {new_value}")
    
    if changes:
        print("\nOptimizations applied:")
        for change in changes:
            print(change)


async def main():
    """Run all memory management demonstrations."""
    print("MCPlease MVP - Memory Management Demo")
    print("====================================")
    
    try:
        # Run demonstrations
        await demonstrate_memory_monitoring()
        demonstrate_quantization_selection()
        await demonstrate_graceful_degradation()
        demonstrate_memory_optimization()
        
        print_separator("Demo Complete")
        print("All memory management features demonstrated successfully!")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())