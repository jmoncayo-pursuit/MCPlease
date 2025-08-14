"""Tests for memory management and optimization functionality."""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.models.memory import (
    MemoryMonitor, MemoryStats, MemoryPressure, 
    QuantizationSelector, QuantizationOption,
    GracefulDegradation, MemoryOptimizer
)
from src.config.hardware import HardwareProfile


class TestMemoryMonitor:
    """Test memory monitoring functionality."""
    
    def test_memory_monitor_initialization(self):
        """Test memory monitor initializes correctly."""
        monitor = MemoryMonitor(check_interval=0.5)
        
        assert monitor.check_interval == 0.5
        assert not monitor._monitoring
        assert monitor._monitor_thread is None
        assert len(monitor._callbacks) == 0
    
    def test_get_current_stats(self):
        """Test getting current memory statistics."""
        monitor = MemoryMonitor()
        stats = monitor.get_current_stats()
        
        assert isinstance(stats, MemoryStats)
        assert stats.total_gb > 0
        assert stats.available_gb > 0
        assert 0 <= stats.used_percent <= 1
        assert isinstance(stats.pressure_level, MemoryPressure)
        assert stats.timestamp > 0
    
    def test_pressure_level_calculation(self):
        """Test memory pressure level calculation."""
        monitor = MemoryMonitor()
        
        # Test different pressure levels
        assert monitor._calculate_pressure_level(0.5) == MemoryPressure.LOW
        assert monitor._calculate_pressure_level(0.7) == MemoryPressure.MODERATE
        assert monitor._calculate_pressure_level(0.8) == MemoryPressure.HIGH
        assert monitor._calculate_pressure_level(0.9) == MemoryPressure.CRITICAL
    
    def test_callback_management(self):
        """Test callback addition and removal."""
        monitor = MemoryMonitor()
        callback = Mock()
        
        # Add callback
        monitor.add_callback(callback)
        assert callback in monitor._callbacks
        
        # Remove callback
        monitor.remove_callback(callback)
        assert callback not in monitor._callbacks
    
    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self):
        """Test starting and stopping monitoring."""
        monitor = MemoryMonitor(check_interval=0.1)
        callback = Mock()
        monitor.add_callback(callback)
        
        # Start monitoring
        monitor.start_monitoring()
        assert monitor._monitoring
        assert monitor._monitor_thread is not None
        
        # Wait for a few callbacks
        await asyncio.sleep(0.3)
        
        # Stop monitoring
        monitor.stop_monitoring()
        assert not monitor._monitoring
        
        # Verify callbacks were called
        assert callback.call_count > 0


class TestQuantizationSelector:
    """Test quantization selection functionality."""
    
    def test_quantization_selector_initialization(self):
        """Test quantization selector initializes with options."""
        selector = QuantizationSelector()
        
        assert len(selector.quantization_options) > 0
        assert all(isinstance(opt, QuantizationOption) for opt in selector.quantization_options)
    
    @patch('src.models.memory.HardwareProfile.detect')
    def test_select_optimal_quantization_high_memory(self, mock_detect):
        """Test quantization selection for high memory systems."""
        # Mock high memory system
        mock_profile = Mock()
        mock_profile.is_apple_silicon = True
        mock_profile.has_gpu = True
        mock_profile.gpu_type = "Apple Silicon"
        mock_detect.return_value = mock_profile
        
        selector = QuantizationSelector()
        
        # Test with 32GB available
        option = selector.select_optimal_quantization(
            available_memory_gb=32.0,
            prefer_quality=True
        )
        
        assert option is not None
        assert option.name in ["bf16", "fp16"]  # Should select high quality option
    
    @patch('src.models.memory.HardwareProfile.detect')
    def test_select_optimal_quantization_low_memory(self, mock_detect):
        """Test quantization selection for low memory systems."""
        # Mock low memory system
        mock_profile = Mock()
        mock_profile.is_apple_silicon = True
        mock_profile.has_gpu = True
        mock_profile.gpu_type = "Apple Silicon"
        mock_detect.return_value = mock_profile
        
        selector = QuantizationSelector()
        
        # Test with 12GB available
        option = selector.select_optimal_quantization(
            available_memory_gb=12.0,
            prefer_quality=False
        )
        
        assert option is not None
        assert option.name in ["int4", "gptq"]  # Should select memory-efficient option
    
    @patch('src.models.memory.HardwareProfile.detect')
    def test_select_optimal_quantization_insufficient_memory(self, mock_detect):
        """Test quantization selection with insufficient memory."""
        # Mock system
        mock_profile = Mock()
        mock_profile.is_apple_silicon = True
        mock_profile.has_gpu = True
        mock_profile.gpu_type = "Apple Silicon"
        mock_detect.return_value = mock_profile
        
        selector = QuantizationSelector()
        
        # Test with very low memory
        option = selector.select_optimal_quantization(
            available_memory_gb=4.0
        )
        
        assert option is None  # No compatible option
    
    @patch('src.models.memory.HardwareProfile.detect')
    def test_get_all_compatible_options(self, mock_detect):
        """Test getting all compatible quantization options."""
        # Mock system
        mock_profile = Mock()
        mock_profile.is_apple_silicon = True
        mock_profile.has_gpu = True
        mock_profile.gpu_type = "Apple Silicon"
        mock_detect.return_value = mock_profile
        
        selector = QuantizationSelector()
        
        # Test with moderate memory
        options = selector.get_all_compatible_options(available_memory_gb=20.0)
        
        assert len(options) > 0
        assert all(opt.memory_requirement_gb <= 20.0 for opt in options)
        # Should be sorted by quality score (descending)
        quality_scores = [opt.quality_score for opt in options]
        assert quality_scores == sorted(quality_scores, reverse=True)


class TestGracefulDegradation:
    """Test graceful degradation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_monitor = Mock(spec=MemoryMonitor)
        self.degradation = GracefulDegradation(self.mock_monitor)
    
    @pytest.mark.asyncio
    async def test_handle_memory_pressure_low(self):
        """Test handling low memory pressure (no degradation)."""
        config = {"max_model_len": 4096, "quantization": "bf16"}
        
        result = await self.degradation.handle_memory_pressure(
            config, MemoryPressure.LOW
        )
        
        assert result == config  # No changes
    
    @pytest.mark.asyncio
    async def test_handle_memory_pressure_high(self):
        """Test handling high memory pressure."""
        config = {
            "max_model_len": 8192,
            "quantization": "bf16",
            "max_num_batched_tokens": 8192
        }
        
        # Mock memory stats
        mock_stats = Mock()
        mock_stats.available_gb = 10.0
        self.mock_monitor.get_current_stats.return_value = mock_stats
        
        result = await self.degradation.handle_memory_pressure(
            config, MemoryPressure.HIGH
        )
        
        # Should apply some degradation
        assert result["max_model_len"] <= config["max_model_len"]
    
    @pytest.mark.asyncio
    async def test_handle_memory_pressure_critical(self):
        """Test handling critical memory pressure."""
        config = {
            "max_model_len": 8192,
            "quantization": "bf16",
            "max_num_batched_tokens": 8192,
            "gpu_memory_utilization": 0.9
        }
        
        # Mock memory stats
        mock_stats = Mock()
        mock_stats.available_gb = 8.0
        self.mock_monitor.get_current_stats.return_value = mock_stats
        
        result = await self.degradation.handle_memory_pressure(
            config, MemoryPressure.CRITICAL
        )
        
        # Should apply aggressive degradation
        assert result["max_model_len"] <= config["max_model_len"]
        assert result["gpu_memory_utilization"] <= config["gpu_memory_utilization"]
    
    @pytest.mark.asyncio
    async def test_reduce_context_length(self):
        """Test context length reduction strategy."""
        config = {"max_model_len": 8192}
        
        result = await self.degradation._reduce_context_length(config)
        
        assert result["max_model_len"] < 8192
        assert result["max_model_len"] >= 2048
    
    @pytest.mark.asyncio
    async def test_reduce_batch_size(self):
        """Test batch size reduction strategy."""
        config = {"max_num_batched_tokens": 8192}
        
        result = await self.degradation._reduce_batch_size(config)
        
        assert result["max_num_batched_tokens"] < 8192
        assert result["max_num_batched_tokens"] >= 1024
    
    @pytest.mark.asyncio
    async def test_enable_cpu_offload(self):
        """Test CPU offload enablement strategy."""
        config = {"cpu_offload": False, "gpu_memory_utilization": 0.8}
        
        result = await self.degradation._enable_cpu_offload(config)
        
        assert result["cpu_offload"] is True
        assert result["gpu_memory_utilization"] <= 0.6
    
    @pytest.mark.asyncio
    async def test_cleanup_memory(self):
        """Test memory cleanup functionality."""
        # Should not raise any exceptions
        await self.degradation.cleanup_memory()


class TestMemoryOptimizer:
    """Test memory optimizer coordination."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.optimizer = MemoryOptimizer()
    
    def test_memory_optimizer_initialization(self):
        """Test memory optimizer initializes correctly."""
        assert self.optimizer.monitor is not None
        assert self.optimizer.quantization_selector is not None
        assert self.optimizer.graceful_degradation is not None
        assert self.optimizer._last_pressure_level == MemoryPressure.LOW
    
    def test_get_optimal_config(self):
        """Test getting optimal configuration."""
        base_config = {
            "model_name": "test-model",
            "max_model_len": 4096,
            "quantization": "auto"
        }
        
        optimized_config = self.optimizer.get_optimal_config(base_config)
        
        assert "quantization" in optimized_config
        assert optimized_config["quantization"] != "auto"  # Should be resolved
        assert "gpu_memory_utilization" in optimized_config
    
    @pytest.mark.asyncio
    async def test_handle_loading_failure_memory_error(self):
        """Test handling memory-related loading failures."""
        config = {"quantization": "bf16", "max_model_len": 8192}
        error = Exception("CUDA out of memory")
        
        result = await self.optimizer.handle_loading_failure(config, error)
        
        assert result is not None
        assert result != config  # Should be modified
    
    @pytest.mark.asyncio
    async def test_handle_loading_failure_non_memory_error(self):
        """Test handling non-memory-related loading failures."""
        config = {"quantization": "bf16", "max_model_len": 8192}
        error = Exception("Model file not found")
        
        result = await self.optimizer.handle_loading_failure(config, error)
        
        assert result is None  # Should not modify config
    
    def test_get_memory_report(self):
        """Test getting comprehensive memory report."""
        report = self.optimizer.get_memory_report()
        
        assert "current_stats" in report
        assert "compatible_quantizations" in report
        assert "recommendations" in report
        
        # Check current stats structure
        stats = report["current_stats"]
        assert "total_memory_gb" in stats
        assert "available_memory_gb" in stats
        assert "pressure_level" in stats
        
        # Check quantizations structure
        quantizations = report["compatible_quantizations"]
        assert isinstance(quantizations, list)
        
        # Check recommendations structure
        recommendations = report["recommendations"]
        assert isinstance(recommendations, list)
    
    def test_pressure_callback_management(self):
        """Test memory pressure callback management."""
        callback = Mock()
        
        # Add callback
        self.optimizer.add_pressure_callback(callback)
        assert callback in self.optimizer._pressure_callbacks
        
        # Simulate pressure change
        self.optimizer._on_memory_stats_update(Mock(pressure_level=MemoryPressure.HIGH))
        
        # Verify callback was called
        callback.assert_called_once_with(MemoryPressure.HIGH)
    
    def test_monitoring_lifecycle(self):
        """Test monitoring start/stop."""
        # Should not raise exceptions
        self.optimizer.start_monitoring()
        self.optimizer.stop_monitoring()


@pytest.mark.integration
class TestMemoryIntegration:
    """Integration tests for memory management components."""
    
    @pytest.mark.asyncio
    async def test_full_memory_optimization_flow(self):
        """Test complete memory optimization workflow."""
        optimizer = MemoryOptimizer()
        
        # Start monitoring
        optimizer.start_monitoring()
        
        try:
            # Get initial report
            initial_report = optimizer.get_memory_report()
            assert "current_stats" in initial_report
            
            # Get optimal config
            base_config = {
                "model_name": "test-model",
                "max_model_len": 4096,
                "quantization": "auto"
            }
            
            optimal_config = optimizer.get_optimal_config(base_config)
            assert optimal_config["quantization"] != "auto"
            
            # Simulate memory pressure handling
            if initial_report["current_stats"]["pressure_level"] != "critical":
                # Test degradation
                degraded_config = await optimizer.graceful_degradation.handle_memory_pressure(
                    optimal_config, MemoryPressure.HIGH
                )
                assert degraded_config is not None
            
        finally:
            # Stop monitoring
            optimizer.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_memory_monitoring_with_callbacks(self):
        """Test memory monitoring with real callbacks."""
        monitor = MemoryMonitor(check_interval=0.1)
        callback_results = []
        
        def test_callback(stats: MemoryStats):
            callback_results.append(stats.pressure_level)
        
        monitor.add_callback(test_callback)
        
        # Start monitoring briefly
        monitor.start_monitoring()
        await asyncio.sleep(0.3)
        monitor.stop_monitoring()
        
        # Should have received some callbacks
        assert len(callback_results) > 0
        assert all(isinstance(level, MemoryPressure) for level in callback_results)