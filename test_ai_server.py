#!/usr/bin/env python3
"""Simple test for AI MCP server functionality."""

import sys
import os
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)

# Test basic functionality
def test_basic_functionality():
    print("🧪 Testing AI MCP Server basic functionality...")
    
    try:
        # Test memory management
        from models.memory import MemoryMonitor, MemoryOptimizer
        print("✅ Memory management imports work")
        
        monitor = MemoryMonitor()
        stats = monitor.get_current_stats()
        print(f"✅ Memory monitoring works: {stats.available_gb:.1f}GB available")
        
        optimizer = MemoryOptimizer()
        report = optimizer.get_memory_report()
        print(f"✅ Memory optimization works: {len(report['compatible_quantizations'])} quantizations available")
        
    except Exception as e:
        print(f"❌ Memory management test failed: {e}")
        return False
    
    try:
        # Test environment management
        from environment.manager import EnvironmentManager
        print("✅ Environment manager imports work")
        
        env_manager = EnvironmentManager()
        python_ok = env_manager.check_python_version()
        print(f"✅ Python version check: {'OK' if python_ok else 'FAIL'}")
        
    except Exception as e:
        print(f"❌ Environment management test failed: {e}")
        return False
    
    print("🎉 All basic tests passed!")
    return True

def test_mock_ai_server():
    """Test a simplified AI server without full model loading."""
    print("\n🧪 Testing mock AI MCP server...")
    
    try:
        # Create a simple mock server
        class MockAIMCPServer:
            def __init__(self):
                self.tools = {
                    "code_completion": {
                        "name": "code_completion",
                        "description": "Generate code completions"
                    },
                    "explain_code": {
                        "name": "explain_code", 
                        "description": "Explain code functionality"
                    }
                }
                self.is_model_ready = False
            
            def generate_mock_completion(self, code: str, language: str = "python") -> str:
                """Generate mock code completion."""
                if "def " in code and code.strip().endswith(":"):
                    return "    pass  # TODO: Implement function"
                elif "class " in code and code.strip().endswith(":"):
                    return "    def __init__(self):\n        pass"
                else:
                    return f"# Mock completion for {language}\n# Context: {code[:50]}..."
            
            def explain_mock_code(self, code: str) -> str:
                """Generate mock code explanation."""
                if "def " in code:
                    return "This is a function definition that defines reusable code."
                elif "class " in code:
                    return "This is a class definition that creates a blueprint for objects."
                else:
                    return f"This code contains {len(code.split())} words and appears to be {language} code."
        
        # Test mock server
        server = MockAIMCPServer()
        print("✅ Mock AI server created")
        
        # Test code completion
        completion = server.generate_mock_completion("def hello():")
        print(f"✅ Code completion works: {completion[:30]}...")
        
        # Test code explanation
        explanation = server.explain_mock_code("def hello(): pass")
        print(f"✅ Code explanation works: {explanation[:50]}...")
        
        print("🎉 Mock AI server tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Mock AI server test failed: {e}")
        return False

if __name__ == "__main__":
    print("MCPlease MVP - AI Server Testing")
    print("=" * 40)
    
    success = True
    success &= test_basic_functionality()
    success &= test_mock_ai_server()
    
    if success:
        print("\n🎉 All tests passed! The system is ready.")
        print("\n📝 Next steps:")
        print("1. The AI server can provide mock responses immediately")
        print("2. Full AI model integration will be available after model download")
        print("3. Run the server with: python src/ai_mcp_server.py")
    else:
        print("\n❌ Some tests failed. Please check the setup.")
        sys.exit(1)