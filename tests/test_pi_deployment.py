"""Tests for Raspberry Pi deployment functionality."""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
import platform

from src.mcplease_mcp.utils.hardware import HardwareDetector, HardwareInfo
from src.mcplease_mcp.utils.ngrok_tunnel import NgrokManager, NgrokTunnel


class TestHardwareDetector:
    """Test hardware detection functionality."""
    
    @pytest.fixture
    def hardware_detector(self):
        """Create hardware detector for testing."""
        return HardwareDetector()
    
    def test_hardware_detection_x86(self, hardware_detector):
        """Test hardware detection on x86_64."""
        with patch('platform.machine', return_value='x86_64'), \
             patch('psutil.cpu_count', return_value=8), \
             patch('psutil.virtual_memory') as mock_memory:
            
            mock_memory.return_value.total = 16 * 1024**3  # 16GB
            
            hardware = hardware_detector.detect_hardware()
            
            assert hardware.architecture == 'x86_64'
            assert hardware.cpu_count == 8
            assert hardware.memory_gb == 16.0
            assert hardware.is_x86_64 is True
            assert hardware.is_arm64 is False
            assert hardware.is_raspberry_pi is False
            assert hardware.optimization_profile == 'x86_standard'
    
    def test_hardware_detection_arm64(self, hardware_detector):
        """Test hardware detection on ARM64."""
        with patch('platform.machine', return_value='aarch64'), \
             patch('psutil.cpu_count', return_value=4), \
             patch('psutil.virtual_memory') as mock_memory:
            
            mock_memory.return_value.total = 8 * 1024**3  # 8GB
            
            hardware = hardware_detector.detect_hardware()
            
            assert hardware.architecture == 'aarch64'
            assert hardware.cpu_count == 4
            assert hardware.memory_gb == 8.0
            assert hardware.is_x86_64 is False
            assert hardware.is_arm64 is True
            assert hardware.optimization_profile == 'arm64_standard'
    
    @patch('builtins.open')
    @patch('os.path.exists')
    def test_raspberry_pi_detection(self, mock_exists, mock_open, hardware_detector):
        """Test Raspberry Pi detection."""
        # Mock /proc/cpuinfo content
        mock_open.return_value.__enter__.return_value.read.return_value = \
            "processor\t: 0\nmodel name\t: ARMv8 Processor rev 4 (v8l)\nBogoMIPS\t: 108.00\n" \
            "Features\t: fp asimd evtstrm crc32 cpuid\nCPU implementer\t: 0x41\n" \
            "CPU architecture: 8\nCPU variant\t: 0x0\nCPU part\t: 0xd08\n" \
            "CPU revision\t: 3\n\nHardware\t: BCM2835\nRevision\t: c03111\nSerial\t\t: 10000000e8d2a0d4\n" \
            "Model\t\t: Raspberry Pi 4 Model B Rev 1.1"
        
        mock_exists.return_value = True
        
        is_pi = hardware_detector._detect_raspberry_pi()
        assert is_pi is True
    
    def test_optimization_config_pi(self, hardware_detector):
        """Test optimization configuration for Raspberry Pi."""
        with patch('platform.machine', return_value='aarch64'), \
             patch('psutil.cpu_count', return_value=4), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch.object(hardware_detector, '_detect_raspberry_pi', return_value=True):
            
            mock_memory.return_value.total = 4 * 1024**3  # 4GB
            
            config = hardware_detector.get_optimization_config()
            
            assert config['hardware_profile'] == 'pi5_standard'
            assert config['model_quantization'] == 'int8'
            assert config['context_length'] == 2048
            assert config['batch_size'] == 1
            assert config['workers'] <= 2
    
    def test_optimization_config_x86(self, hardware_detector):
        """Test optimization configuration for x86_64."""
        with patch('platform.machine', return_value='x86_64'), \
             patch('psutil.cpu_count', return_value=8), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch.object(hardware_detector, '_detect_raspberry_pi', return_value=False):
            
            mock_memory.return_value.total = 32 * 1024**3  # 32GB
            
            config = hardware_detector.get_optimization_config()
            
            assert config['hardware_profile'] == 'x86_high_performance'
            assert config['model_quantization'] == 'fp32'
            assert config['context_length'] == 8192
            assert config['batch_size'] == 4
    
    def test_worker_calculation(self, hardware_detector):
        """Test worker count calculation."""
        # Test Pi (conservative)
        workers = hardware_detector._calculate_recommended_workers(4, 4.0, True)
        assert workers <= 2
        
        # Test x86 (aggressive)
        workers = hardware_detector._calculate_recommended_workers(8, 16.0, False)
        assert workers > 2
        assert workers <= 8
    
    def test_memory_limit_calculation(self, hardware_detector):
        """Test memory limit calculation."""
        # Test Pi (60% of memory)
        limit = hardware_detector._calculate_memory_limit(4.0, True)
        assert limit == "2GB"
        
        # Test x86 (80% of memory)
        limit = hardware_detector._calculate_memory_limit(16.0, False)
        assert limit == "12GB"


class TestNgrokManager:
    """Test ngrok tunnel management."""
    
    @pytest.fixture
    def ngrok_manager(self):
        """Create ngrok manager for testing."""
        return NgrokManager(auth_token="test_token")
    
    @pytest.mark.asyncio
    async def test_ngrok_manager_init(self, ngrok_manager):
        """Test ngrok manager initialization."""
        assert ngrok_manager.auth_token == "test_token"
        assert ngrok_manager.region == "us"
        assert ngrok_manager.tunnels == {}
    
    @pytest.mark.asyncio
    async def test_create_tunnel_success(self, ngrok_manager):
        """Test successful tunnel creation."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "name": "test-tunnel",
            "public_url": "https://abc123.ngrok.io",
            "proto": "http"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=Mock(status_code=200))
            
            tunnel = await ngrok_manager.create_tunnel("test", 8000)
            
            assert tunnel is not None
            assert tunnel.name == "test"
            assert tunnel.public_url == "https://abc123.ngrok.io"
            assert tunnel.local_port == 8000
            assert "test" in ngrok_manager.tunnels
    
    @pytest.mark.asyncio
    async def test_create_tunnel_failure(self, ngrok_manager):
        """Test tunnel creation failure."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=Mock(status_code=200))
            
            tunnel = await ngrok_manager.create_tunnel("test", 8000)
            
            assert tunnel is None
            assert "test" not in ngrok_manager.tunnels
    
    @pytest.mark.asyncio
    async def test_delete_tunnel(self, ngrok_manager):
        """Test tunnel deletion."""
        # Add a tunnel first
        tunnel = NgrokTunnel(
            name="test",
            public_url="https://test.ngrok.io",
            local_port=8000,
            protocol="http",
            tunnel_id="test-id",
            created_at=1234567890
        )
        ngrok_manager.tunnels["test"] = tunnel
        
        mock_response = Mock()
        mock_response.status_code = 204
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.delete = AsyncMock(return_value=mock_response)
            
            result = await ngrok_manager.delete_tunnel("test")
            
            assert result is True
            assert "test" not in ngrok_manager.tunnels
    
    @pytest.mark.asyncio
    async def test_setup_mcp_tunnels(self, ngrok_manager):
        """Test MCP tunnel setup."""
        mock_response = Mock()
        mock_response.status_code = 201
        
        def mock_json():
            if "sse" in mock_response.call_count_tracker:
                return {
                    "name": "mcp-sse",
                    "public_url": "https://sse.ngrok.io",
                    "proto": "http"
                }
            else:
                return {
                    "name": "mcp-websocket", 
                    "public_url": "https://ws.ngrok.io",
                    "proto": "http"
                }
        
        mock_response.json = mock_json
        mock_response.call_count_tracker = []
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=Mock(status_code=200))
            
            # Mock the individual tunnel creation calls
            with patch.object(ngrok_manager, 'create_tunnel') as mock_create:
                mock_create.side_effect = [
                    NgrokTunnel("mcp-sse", "https://sse.ngrok.io", 8000, "http", "sse-id", 123),
                    NgrokTunnel("mcp-websocket", "https://ws.ngrok.io", 8001, "http", "ws-id", 123)
                ]
                
                tunnels = await ngrok_manager.setup_mcp_tunnels()
                
                assert len(tunnels) == 2
                assert "sse" in tunnels
                assert "websocket" in tunnels
                assert tunnels["sse"].public_url == "https://sse.ngrok.io"
                assert tunnels["websocket"].public_url == "https://ws.ngrok.io"
    
    @pytest.mark.asyncio
    async def test_health_check(self, ngrok_manager):
        """Test ngrok health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tunnels": [
                {
                    "name": "test-tunnel",
                    "public_url": "https://test.ngrok.io",
                    "proto": "http"
                }
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            health = await ngrok_manager.health_check()
            
            assert health["api_accessible"] is True
            assert health["tunnel_count"] == 1
            assert len(health["tunnels"]) == 1
            assert health["tunnels"][0]["name"] == "test-tunnel"


class TestPiDeploymentIntegration:
    """Test Pi deployment integration."""
    
    @pytest.mark.asyncio
    async def test_pi_optimization_detection(self):
        """Test Pi-specific optimization detection."""
        detector = HardwareDetector()
        
        with patch('platform.machine', return_value='aarch64'), \
             patch('psutil.cpu_count', return_value=4), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch.object(detector, '_detect_raspberry_pi', return_value=True):
            
            mock_memory.return_value.total = 8 * 1024**3  # 8GB Pi 5
            
            hardware = detector.detect_hardware()
            config = detector.get_optimization_config()
            
            assert hardware.is_raspberry_pi is True
            assert hardware.optimization_profile == 'pi5_high_memory'
            assert config['model_quantization'] == 'int8'
            assert config['temperature_monitoring'] is True
            assert config['cpu_governor'] == 'ondemand'
    
    @pytest.mark.asyncio
    async def test_ngrok_pi_tunnel_setup(self):
        """Test ngrok tunnel setup for Pi deployment."""
        from src.mcplease_mcp.utils.ngrok_tunnel import setup_pi_tunnels
        
        with patch('src.mcplease_mcp.utils.ngrok_tunnel.ngrok_manager') as mock_manager:
            mock_manager.setup_mcp_tunnels = AsyncMock(return_value={
                "sse": NgrokTunnel("mcp-sse", "https://pi-sse.ngrok.io", 8000, "http", "sse-id", 123),
                "websocket": NgrokTunnel("mcp-websocket", "https://pi-ws.ngrok.io", 8001, "http", "ws-id", 123)
            })
            
            tunnels = await setup_pi_tunnels(auth_token="test_token")
            
            assert len(tunnels) == 2
            assert "sse" in tunnels
            assert "websocket" in tunnels
            mock_manager.setup_mcp_tunnels.assert_called_once_with(
                sse_port=8000,
                ws_port=8001,
                subdomain_prefix="mcplease-pi"
            )


if __name__ == "__main__":
    pytest.main([__file__])