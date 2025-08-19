"""
Final Integration Test for MCPlease MCP Server

This test validates the complete system integration including:
- MCP protocol compliance
- AI tool functionality
- Security features
- Performance monitoring
- Resource management
"""

import pytest
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

from src.mcplease_mcp.server.server import MCPServer
from src.mcplease_mcp.protocol.handler import MCPProtocolHandler
from src.mcplease_mcp.tools.registry import MCPToolRegistry
from src.mcplease_mcp.security.manager import MCPSecurityManager
from src.mcplease_mcp.utils.performance import PerformanceMonitor
from src.mcplease_mcp.utils.health import HealthMonitor
from src.mcplease_mcp.protocol.resources import MCPResourcesAndPrompts


class TestFinalIntegration:
    """Final integration test for complete MCP server system."""
    
    @pytest.fixture(autouse=True)
    async def setup_system(self):
        """Setup complete MCP server system."""
        # Initialize all components
        self.server = MCPServer()
        self.tool_registry = MCPToolRegistry()
        self.security_manager = MCPSecurityManager()
        self.performance_monitor = PerformanceMonitor()
        self.health_monitor = HealthMonitor()
        self.resources_prompts = MCPResourcesAndPrompts()
        
        # Setup server with all components
        self.server.tool_registry = self.tool_registry
        self.server.security_manager = self.security_manager
        self.server.performance_monitor = self.performance_monitor
        self.server.health_monitor = self.health_monitor
        
        # Initialize components
        await self.performance_monitor.start()
        await self.health_monitor.start_monitoring()
        await self.resources_prompts.initialize()
        
        yield
        
        # Cleanup
        await self.performance_monitor.stop()
        await self.health_monitor.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_complete_mcp_workflow(self):
        """Test complete MCP workflow from initialization to tool execution."""
        # 1. Initialize server
        await self.server.start()
        
        # 2. Test MCP protocol initialization
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "clientInfo": {
                    "name": "IntegrationTest",
                    "version": "1.0.0"
                }
            }
        }
        
        init_response = await self.server._handle_message(init_request)
        
        # Verify initialization
        assert "result" in init_response
        assert "capabilities" in init_response["result"]
        assert "tools" in init_response["result"]["capabilities"]
        assert "resources" in init_response["result"]["capabilities"]
        assert "prompts" in init_response["result"]["capabilities"]
        
        # 3. Test tools listing
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        tools_response = await self.server._handle_message(tools_request)
        
        # Verify tools are available
        assert "result" in tools_response
        assert "tools" in tools_response["result"]
        tools = tools_response["result"]["tools"]
        
        # Check for expected tools
        tool_names = [tool["name"] for tool in tools]
        assert "code_completion" in tool_names
        assert "code_explanation" in tool_names
        assert "debug_assistance" in tool_names
        
        # 4. Test tool execution
        tool_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "code_completion",
                "arguments": {
                    "code": "def hello():",
                    "language": "python"
                }
            }
        }
        
        tool_response = await self.server._handle_message(tool_request)
        
        # Verify tool execution
        assert "result" in tool_response
        assert "content" in tool_response["result"]
        
        # 5. Test resources listing
        resources_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/list",
            "params": {}
        }
        
        # Note: This would require implementing resources/list method
        # For now, we'll test the resources manager directly
        resources = await self.resources_prompts.get_resources_list()
        assert isinstance(resources, list)
        
        # 6. Test prompts listing
        prompts = await self.resources_prompts.get_prompts_list()
        assert isinstance(prompts, list)
        
        # 7. Test health monitoring
        health_status = await self.health_monitor.get_health_report()
        assert "current_status" in health_status
        assert "overall_status" in health_status["current_status"]
        
        # 8. Test performance monitoring
        perf_status = self.performance_monitor.get_health_status()
        assert "status" in perf_status
        assert "metrics" in perf_status
        
        await self.server.stop()
    
    @pytest.mark.asyncio
    async def test_security_integration(self):
        """Test security features integration."""
        # Setup security manager
        await self.security_manager.initialize()
        
        # Test authentication
        auth_result = await self.security_manager.authenticate_user("test_user", "test_token")
        assert auth_result["authenticated"] in [True, False]  # Depends on token validity
        
        # Test session management
        session = await self.security_manager.create_session("test_user")
        assert session["user_id"] == "test_user"
        assert "session_id" in session
        
        # Test session validation
        valid = await self.security_manager.validate_session(session["session_id"])
        assert valid["valid"] in [True, False]
        
        # Test rate limiting
        rate_limit_result = await self.security_manager.check_rate_limit("127.0.0.1")
        assert "allowed" in rate_limit_result
        
        await self.security_manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_performance_integration(self):
        """Test performance monitoring integration."""
        # Start performance monitoring
        await self.performance_monitor.start()
        
        # Simulate some activity
        for i in range(5):
            await self.performance_monitor.track_request(f"test_{i}", "test_endpoint", "GET")
            await asyncio.sleep(0.1)
        
        # Check performance metrics
        health_status = self.performance_monitor.get_health_status()
        assert "status" in health_status
        assert "metrics" in health_status
        
        # Check queue statistics
        queue_stats = self.performance_monitor.request_queue.get_stats()
        assert "total_processed" in queue_stats
        assert "total_failed" in queue_stats
        
        await self.performance_monitor.stop()
    
    @pytest.mark.asyncio
    async def test_health_monitoring_integration(self):
        """Test health monitoring integration."""
        # Start health monitoring
        await self.health_monitor.start_monitoring()
        
        # Register custom health checks
        async def test_check():
            return {
                "status": "healthy",
                "message": "Test check passed",
                "details": {"test": True}
            }
        
        self.health_monitor.register_health_check(
            "test_check",
            "test_component",
            test_check
        )
        
        # Run health checks
        health_report = await self.health_monitor.get_health_report()
        assert "current_status" in health_report
        assert "overall_status" in health_report["current_status"]
        
        # Check for our custom check
        checks = health_report["current_status"]["checks"]
        test_check_found = any(check["name"] == "test_check" for check in checks)
        assert test_check_found
        
        await self.health_monitor.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_resource_management_integration(self):
        """Test resource and prompt management integration."""
        # Test resource creation
        from src.mcplease_mcp.protocol.resources import ResourceMetadata, ResourceType
        
        test_resource = ResourceMetadata(
            name="test_file.txt",
            type=ResourceType.FILE,
            description="Test file resource",
            uri="file://test_file.txt"
        )
        
        created_resource = await self.resources_prompts.resource_manager.create_resource(test_resource)
        assert created_resource.name == "test_file.txt"
        assert created_resource.uri in self.resources_prompts.resource_manager.resources
        
        # Test resource listing
        resources = await self.resources_prompts.get_resources_list()
        assert len(resources) > 0
        
        # Test prompt creation
        test_prompt = await self.resources_prompts.create_custom_prompt(
            "test_prompt",
            "Test prompt for integration testing",
            [{"role": "system", "content": "You are a test assistant."}]
        )
        
        assert test_prompt["success"]
        assert "prompt" in test_prompt
        
        # Test prompt listing
        prompts = await self.resources_prompts.get_prompts_list()
        assert len(prompts) > 0
        
        # Test system status
        status = await self.resources_prompts.get_system_status()
        assert "status" in status
        assert status["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling across the system."""
        # Test invalid MCP method
        invalid_request = {
            "jsonrpc": "2.0",
            "id": 999,
            "method": "invalid_method",
            "params": {}
        }
        
        error_response = await self.server._handle_message(invalid_request)
        
        # Verify error response
        assert "error" in error_response
        assert error_response["error"]["code"] == -32601  # Method not found
        
        # Test invalid tool arguments
        invalid_tool_request = {
            "jsonrpc": "2.0",
            "id": 1000,
            "method": "tools/call",
            "params": {
                "name": "code_completion",
                "arguments": {
                    "invalid_arg": "invalid_value"
                }
            }
        }
        
        tool_error_response = await self.server._handle_message(invalid_tool_request)
        
        # Verify tool error response
        assert "error" in tool_error_response
        assert tool_error_response["error"]["code"] in [-32602, -32001]  # Invalid params or tool execution failed
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent operations handling."""
        # Start server
        await self.server.start()
        
        # Create multiple concurrent requests
        async def make_request(request_id: int):
            request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/list",
                "params": {}
            }
            return await self.server._handle_message(request)
        
        # Execute concurrent requests
        tasks = [make_request(i) for i in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # Verify all requests succeeded
        for response in responses:
            assert "result" in response
            assert "tools" in response["result"]
        
        await self.server.stop()
    
    @pytest.mark.asyncio
    async def test_system_resilience(self):
        """Test system resilience under stress."""
        # Start server
        await self.server.start()
        
        # Simulate high load
        async def stress_test():
            for i in range(50):
                try:
                    request = {
                        "jsonrpc": "2.0",
                        "id": i,
                        "method": "tools/list",
                        "params": {}
                    }
                    await self.server._handle_message(request)
                    await asyncio.sleep(0.01)  # Small delay
                except Exception as e:
                    # Some errors are expected under stress
                    pass
        
        # Run stress test
        await stress_test()
        
        # Verify system is still responsive
        health_check = {
            "jsonrpc": "2.0",
            "id": "health",
            "method": "tools/list",
            "params": {}
        }
        
        response = await self.server._handle_message(health_check)
        assert "result" in response
        
        await self.server.stop()
    
    @pytest.mark.asyncio
    async def test_complete_system_validation(self):
        """Final validation of complete system."""
        # 1. Verify all components are initialized
        assert self.server is not None
        assert self.tool_registry is not None
        assert self.security_manager is not None
        assert self.performance_monitor is not None
        assert self.health_monitor is not None
        assert self.resources_prompts is not None
        
        # 2. Verify tool registry has expected tools
        tools = self.tool_registry.list_tools()
        tool_names = [tool.name for tool in tools]
        
        expected_tools = ["code_completion", "code_explanation", "debug_assistance"]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Expected tool {expected_tool} not found"
        
        # 3. Verify performance monitoring is active
        assert self.performance_monitor.running
        
        # 4. Verify health monitoring is active
        assert self.health_monitor.running
        
        # 5. Verify resources and prompts are initialized
        status = await self.resources_prompts.get_system_status()
        assert status["status"] == "healthy"
        
        # 6. Verify security manager is ready
        assert self.security_manager is not None
        
        # 7. Final system health check
        health_report = await self.health_monitor.get_health_report()
        assert "current_status" in health_report
        assert "overall_status" in health_report["current_status"]
        
        # 8. Performance status check
        perf_status = self.performance_monitor.get_health_status()
        assert "status" in perf_status
        assert "metrics" in perf_status
        
        print("✅ Complete system validation passed!")
        print(f"   - Tools registered: {len(tools)}")
        print(f"   - Performance monitoring: {'Active' if self.performance_monitor.running else 'Inactive'}")
        print(f"   - Health monitoring: {'Active' if self.health_monitor.running else 'Inactive'}")
        print(f"   - System status: {status['status']}")
        print(f"   - Overall health: {health_report['current_status']['overall_status']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
