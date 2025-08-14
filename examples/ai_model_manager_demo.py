#!/usr/bin/env python3
"""
Demo script for AIModelManager functionality.

This script demonstrates how to use the AIModelManager class for:
- Loading AI models with memory optimization
- Generating code completions
- Explaining code
- Managing model lifecycle

Note: This demo requires vLLM and torch to be installed.
Run: pip install -r requirements.txt
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.ai_manager import AIModelManager


async def demo_ai_model_manager():
    """Demonstrate AIModelManager functionality."""
    print("🤖 AIModelManager Demo")
    print("=" * 50)
    
    # Initialize the AI model manager
    print("\n1. Initializing AIModelManager...")
    ai_manager = AIModelManager(max_memory_gb=12)
    
    # Check initial status
    print("\n2. Initial Status:")
    status = ai_manager.get_model_status()
    print(f"   Model Ready: {status['is_ready']}")
    print(f"   Hardware: {status['hardware']['total_memory_gb']:.1f}GB RAM")
    print(f"   Apple Silicon: {status['hardware']['is_apple_silicon']}")
    
    # Perform health check
    print("\n3. Health Check:")
    health = await ai_manager.health_check()
    print(f"   Overall Status: {health['overall_status']}")
    print(f"   Model Manager: {health['model_manager']}")
    print(f"   Inference Engine: {health['inference_engine']}")
    
    # Load the model
    print("\n4. Loading AI Model...")
    print("   This may take a few minutes on first run...")
    
    try:
        success = await ai_manager.load_model()
        if success:
            print("   ✅ Model loaded successfully!")
            
            # Show updated status
            status = ai_manager.get_model_status()
            print(f"   Load Time: {status.get('load_time', 0):.1f}s")
            print(f"   Quantization: {status['config']['quantization']}")
            print(f"   Max Context: {status['config']['max_model_len']} tokens")
            
        else:
            print("   ❌ Model loading failed!")
            return
            
    except Exception as e:
        print(f"   ❌ Error loading model: {e}")
        print("   Note: This demo requires vLLM and torch to be installed.")
        print("   Run: pip install -r requirements.txt")
        return
    
    # Test code completion
    print("\n5. Testing Code Completion:")
    code_context = """def fibonacci(n):
    if n <= 1:
        return n
    else:"""
    
    try:
        completion = await ai_manager.generate_code_completion(code_context)
        print(f"   Input: {code_context}")
        print(f"   Completion: {completion}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test code explanation
    print("\n6. Testing Code Explanation:")
    code_to_explain = """
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
"""
    
    try:
        explanation = await ai_manager.explain_code(code_to_explain)
        print(f"   Code: {code_to_explain.strip()}")
        print(f"   Explanation: {explanation}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test general text generation
    print("\n7. Testing General Text Generation:")
    try:
        response = await ai_manager.generate_text(
            "What are the key principles of clean code?",
            max_tokens=200
        )
        print(f"   Response: {response}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Show performance metrics
    print("\n8. Performance Metrics:")
    status = ai_manager.get_model_status()
    perf = status['performance']
    print(f"   Total Requests: {perf['total_requests']}")
    print(f"   Total Inference Time: {perf['total_inference_time']:.2f}s")
    print(f"   Average Time per Request: {perf['avg_inference_time']:.2f}s")
    
    # Final health check
    print("\n9. Final Health Check:")
    health = await ai_manager.health_check()
    print(f"   Overall Status: {health['overall_status']}")
    print(f"   Functionality: {health['functionality']}")
    
    # Cleanup
    print("\n10. Cleanup:")
    await ai_manager.unload_model()
    print("   ✅ Model unloaded successfully!")
    
    print("\n🎉 Demo completed!")


async def demo_without_loading():
    """Demonstrate AIModelManager functionality without actually loading the model."""
    print("🤖 AIModelManager Demo (No Model Loading)")
    print("=" * 50)
    
    # Initialize the AI model manager
    print("\n1. Initializing AIModelManager...")
    ai_manager = AIModelManager(max_memory_gb=8)
    
    # Check initial status
    print("\n2. Initial Status:")
    status = ai_manager.get_model_status()
    print(f"   Model Ready: {status['is_ready']}")
    print(f"   Hardware: {status['hardware']['total_memory_gb']:.1f}GB RAM")
    print(f"   Apple Silicon: {status['hardware']['is_apple_silicon']}")
    print(f"   Optimal Quantization: {status['config']['quantization']}")
    
    # Test prompt formatting
    print("\n3. Testing Prompt Formatting:")
    code_prompt = "def hello_world():"
    text_prompt = "What is Python?"
    
    formatted_code = ai_manager._format_prompt_with_context(code_prompt)
    formatted_text = ai_manager._format_prompt_with_context(text_prompt)
    
    print(f"   Code Prompt Detection: {ai_manager._is_code_prompt(code_prompt)}")
    print(f"   Text Prompt Detection: {ai_manager._is_code_prompt(text_prompt)}")
    print(f"   Code Formatting: {formatted_code[:100]}...")
    print(f"   Text Formatting: {formatted_text[:100]}...")
    
    # Test error handling
    print("\n4. Testing Error Handling:")
    try:
        await ai_manager.generate_text("test")
    except RuntimeError as e:
        print(f"   Expected Error: {e}")
    
    # Health check
    print("\n5. Health Check:")
    health = await ai_manager.health_check()
    print(f"   Overall Status: {health['overall_status']}")
    print(f"   Details: {health['details']}")
    
    print("\n🎉 Demo completed!")


if __name__ == "__main__":
    print("Choose demo mode:")
    print("1. Full demo (requires vLLM/torch installation)")
    print("2. Basic demo (no model loading)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(demo_ai_model_manager())
    else:
        asyncio.run(demo_without_loading())