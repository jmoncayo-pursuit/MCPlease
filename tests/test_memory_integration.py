"""Integration tests for memory management with AI model manager."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio

# Test memory management without torch dependencies
from src.models.memory import (
    MemoryMonitor, MemoryOptimizer, MemoryPressure, 
    QuantizationSelector, GracefulDegradation
)


class TestMemoryManagementIntegration:
    """Test memory management integration without torch dependencies."""
    
    def test_memory_monitor_basic_functionality(self):
        """Test basic memory monitoring functionality."""
        monitor = MemoryMonitor()
        
        # Test getting current stats
        stats = monitor.get_current_stats()
        assert stats.total_gb > 0
        assert stats.available_gb > 0
        assert isinstance(stats.pressure_level, MemoryPressure)
        
        # Test pressure level calculation
        assert monitor._calculate_pressure_level(0.5) == MemoryPressure.LOW
        assert monitor._calculate_pressure_level(0.7) == MemoryPressure.LOW  # 0.7 < 0.75 threshold
        assert monitor._calculate_pressure_level(0.8) == MemoryPressure.MODERATE  # 0.8 >= 0.75 but < 0.85
        assert monitor._calculate_pressure_level(0.9) == MemoryPressure.HIGH  # 0.9 >= 0.85 but < 0.95
        assert monitor._calculate_pressure_level(0.95) == MemoryPressure.CRITICAL
    
    def test_quantization_selector_functionality(self):
        """Test quantization selection logic."""
        selector = QuantizationSelector()
        
        # Test with high memory
        high_memory_option = selector.select_optimal_quantization(
            available_memory_gb=32.0,
            prefer_quality=True
        )
        if high_memory_option:
            assert high_memory_option.quality_score >= 0.8
        
        # Test with low memory
        low_memory_option = selector.select_optimal_quantization(
            available_memory_gb=10.0,
            prefer_quality=False
        )
        if low_memory_option:
            assert low_memory_option.memory_requirement_gb <= 10.0
        
        # Test with insufficient memory
        no_option = selector.select_optimal_quantization(
            available_memory_gb=2.0
        )
        assert no_option is None
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_strategies(self):
        """Test graceful degradation strategies."""
        mock_monitor = Mock()
        mock_stats = Mock()
        mock_stats.available_gb = 8.0
        mock_monitor.get_current_stats.return_value = mock_stats
        
        degradation = GracefulDegradation(mock_monitor)
        
        # Test context length reduction
        config = {"max_model_len": 8192}
        result = await degradation._reduce_context_length(config)
        assert result["max_model_len"] < 8192
        
        # Test batch size reduction
        config = {"max_num_batched_tokens": 8192}
        result = await degradation._reduce_batch_size(config)
        assert result["max_num_batched_tokens"] < 8192
        
        # Test CPU offload enablement
        config = {"cpu_offload": False, "gpu_memory_utilization": 0.8}
        result = await degradation._enable_cpu_offload(config)
        assert result["cpu_offload"] is True
        assert result["gpu_memory_utilization"] <= 0.6
    
    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self):
        """Test memory pressure handling."""
        mock_monitor = Mock()
        mock_stats = Mock()
        mock_stats.available_gb = 8.0
        mock_monitor.get_current_stats.return_value = mock_stats
        
        degradation = GracefulDegradation(mock_monitor)
        
        config = {
            "max_model_len": 8192,
            "quantization": "bf16",
            "gpu_memory_utilization": 0.9
        }
        
        # Test low pressure (no changes)
        result_low = await degradation.handle_memory_pressure(
            config, MemoryPressure.LOW
        )
        assert result_low == config
        
        # Test high pressure (some changes)
        result_high = await degradation.handle_memory_pressure(
            config, MemoryPressure.HIGH
        )
        # Should have some modifications
        changes = sum(1 for k, v in result_high.items() if config.get(k) != v)
        assert changes > 0
        
        # Test critical pressure (more changes)
        result_critical = await degradation.handle_memory_pressure(
            config, MemoryPressure.CRITICAL
        )
        # Should have more modifications than high pressure
        critical_changes = sum(1 for k, v in result_critical.items() if config.get(k) != v)
        assert critical_changes >= changes
    
    def test_memory_optimizer_coordination(self):
        """Test memory optimizer coordination."""
        optimizer = MemoryOptimizer()
        
        # Test optimal config generation
        base_config = {
            "model_name": "test-model",
            "max_model_len": 4096,
            "quantization": "auto"
        }
        
        optimal_config = optimizer.get_optimal_config(base_config)
        assert "quantization" in optimal_config
        assert optimal_config["quantization"] != "auto"
        
        # Test memory report generation
        report = optimizer.get_memory_report()
        assert "current_stats" in report
        assert "compatible_quantizations" in report
        assert "recommendations" in report
        
        # Verify report structure
        stats = report["current_stats"]
        required_stats = [
            "total_memory_gb", "available_memory_gb", "used_percent", 
            "pressure_level", "gpu_memory_gb"
        ]
        for stat in required_stats:
            assert stat in stats
    
    @pytest.mark.asyncio
    async def test_loading_failure_handling(self):
        """Test handling of loading failures."""
        optimizer = MemoryOptimizer()
        
        config = {"quantization": "bf16", "max_model_len": 8192}
        
        # Test memory-related error
        memory_error = Exception("CUDA out of memory")
        result = await optimizer.handle_loading_failure(config, memory_error)
        assert result is not None
        assert result != config  # Should be modified
        
        # Test non-memory error
        other_error = Exception("File not found")
        result = await optimizer.handle_loading_failure(config, other_error)
        assert result is None  # Should not modify config
    
    def test_callback_system(self):
        """Test callback system for memory monitoring."""
        optimizer = MemoryOptimizer()
        callback_calls = []
        
        def test_callback(pressure_level):
            callback_calls.append(pressure_level)
        
        # Add callback
        optimizer.add_pressure_callback(test_callback)
        
        # Simulate pressure change
        optimizer._on_memory_stats_update(Mock(pressure_level=MemoryPressure.HIGH))
        
        # Verify callback was called
        assert len(callback_calls) == 1
        assert callback_calls[0] == MemoryPressure.HIGH
    
    def test_monitoring_lifecycle(self):
        """Test monitoring start/stop lifecycle."""
        monitor = MemoryMonitor(check_interval=0.1)
        
        # Test start
        monitor.start_monitoring()
        assert monitor._monitoring is True
        assert monitor._monitor_thread is not None
        
        # Test stop
        monitor.stop_monitoring()
        assert monitor._monitoring is False
    
    @pytest.mark.asyncio
    async def test_memory_cleanup(self):
        """Test memory cleanup functionality."""
        mock_monitor = Mock()
        degradation = GracefulDegradation(mock_monitor)
        
        # Should not raise any exceptions
        await degradation.cleanup_memory()
    
    def test_hardware_compatibility(self):
        """Test hardware compatibility detection."""
        selector = QuantizationSelector()
        
        # Test hardware type detection
        hardware_type = selector._get_hardware_type()
        assert hardware_type in ["apple_silicon", "cuda", "cpu"]
        
        # Test compatibility filtering
        all_options = selector.quantization_options
        compatible_options = selector.get_all_compatible_options(20.0)
        
        # Compatible options should be a subset of all options
        assert len(compatible_options) <= len(all_options)
        
        # All compatible options should meet memory requirement
        for option in compatible_options:
            assert option.memory_requirement_gb <= 20.0


@pytest.mark.integration
class TestMemoryOptimizationFlow:
    """Integration tests for complete memory optimization flow."""
    
    @pytest.mark.asyncio
    async def test_complete_optimization_workflow(self):
        """Test complete memory optimization workflow."""
        # Initialize components
        optimizer = MemoryOptimizer()
        
        # Start monitoring
        optimizer.start_monitoring()
        
        try:
            # Get initial memory report
            initial_report = optimizer.get_memory_report()
            assert "current_stats" in initial_report
            
            initial_pressure = initial_report["current_stats"]["pressure_level"]
            
            # Test configuration optimization
            base_config = {
                "model_name": "test-model",
                "max_model_len": 4096,
                "quantization": "auto",
                "gpu_memory_utilization": 0.8
            }
            
            optimal_config = optimizer.get_optimal_config(base_config)
            
            # Verify optimization occurred
            assert optimal_config["quantization"] != "auto"
            assert "gpu_memory_utilization" in optimal_config
            
            # Test degradation under different pressure levels
            # Use a more aggressive config to test degradation
            aggressive_config = {
                "model_name": "test-model",
                "max_model_len": 8192,  # Higher than optimal
                "quantization": "bf16",  # Higher quality than optimal
                "gpu_memory_utilization": 0.9,
                "max_num_batched_tokens": 8192
            }
            
            for pressure in [MemoryPressure.MODERATE, MemoryPressure.HIGH, MemoryPressure.CRITICAL]:
                degraded_config = await optimizer.graceful_degradation.handle_memory_pressure(
                    aggressive_config, pressure
                )
                
                if pressure != MemoryPressure.MODERATE:
                    # Should have some modifications for high/critical pressure
                    # Check if any values were reduced
                    context_reduced = degraded_config.get("max_model_len", 8192) < aggressive_config["max_model_len"]
                    memory_reduced = degraded_config.get("gpu_memory_utilization", 0.9) < aggressive_config["gpu_memory_utilization"]
                    batch_reduced = degraded_config.get("max_num_batched_tokens", 8192) < aggressive_config["max_num_batched_tokens"]
                    
                    assert context_reduced or memory_reduced or batch_reduced, f"No degradation applied for {pressure}"
            
            # Test error handling
            memory_error = Exception("out of memory")
            fallback_config = await optimizer.handle_loading_failure(optimal_config, memory_error)
            assert fallback_config is not None
            
        finally:
            # Clean up
            optimizer.stop_monitoring()
    
    def test_memory_report_completeness(self):
        """Test that memory reports contain all expected information."""
        optimizer = MemoryOptimizer()
        report = optimizer.get_memory_report()
        
        # Check main sections
        assert "current_stats" in report
        assert "compatible_quantizations" in report
        assert "recommendations" in report
        
        # Check current stats completeness
        stats = report["current_stats"]
        expected_stats = [
            "total_memory_gb", "available_memory_gb", "used_memory_gb",
            "used_percent", "pressure_level", "gpu_memory_gb", "gpu_available_gb"
        ]
        for stat in expected_stats:
            assert stat in stats, f"Missing stat: {stat}"
        
        # Check quantization options format
        quantizations = report["compatible_quantizations"]
        if quantizations:  # Only check if there are compatible options
            for quant in quantizations:
                assert "name" in quant
                assert "memory_requirement_gb" in quant
                assert "quality_score" in quant
                assert "description" in quant
        
        # Check recommendations format
        recommendations = report["recommendations"]
        assert isinstance(recommendations, list)
        for rec in recommendations:
            assert isinstance(rec, str)
    
    @pytest.mark.asyncio
    async def test_pressure_level_transitions(self):
        """Test handling of memory pressure level transitions."""
        optimizer = MemoryOptimizer()
        pressure_changes = []
        
        def track_pressure_changes(pressure_level):
            pressure_changes.append(pressure_level)
        
        optimizer.add_pressure_callback(track_pressure_changes)
        
        # Simulate pressure level changes
        mock_stats_low = Mock(pressure_level=MemoryPressure.LOW)
        mock_stats_high = Mock(pressure_level=MemoryPressure.HIGH)
        mock_stats_critical = Mock(pressure_level=MemoryPressure.CRITICAL)
        
        # Initial state
        optimizer._on_memory_stats_update(mock_stats_low)
        
        # Pressure increase
        optimizer._on_memory_stats_update(mock_stats_high)
        assert MemoryPressure.HIGH in pressure_changes
        
        # Critical pressure
        optimizer._on_memory_stats_update(mock_stats_critical)
        assert MemoryPressure.CRITICAL in pressure_changes
        
        # Pressure decrease
        optimizer._on_memory_stats_update(mock_stats_low)
        assert pressure_changes[-1] == MemoryPressure.LOW