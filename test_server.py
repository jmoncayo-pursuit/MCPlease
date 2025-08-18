#!/usr/bin/env python3
"""Test script for the HTTP server."""

import requests
import json

def test_server():
    """Test the HTTP server endpoints."""
    
    # Test health endpoint
    print("Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Health status: {response.status_code}")
        print(f"Health response: {response.json()}")
    except Exception as e:
        print(f"Health test failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test chat completions
    print("Testing chat completions...")
    try:
        data = {
            "messages": [
                {"role": "user", "content": "Complete this function: def fibonacci(n):"}
            ],
            "model": "gpt-3.5-turbo"
        }
        
        response = requests.post(
            "http://localhost:8000/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json=data
        )
        
        print(f"Chat status: {response.status_code}")
        print(f"Chat response: {response.text}")
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                print(f"Parsed JSON: {json.dumps(json_response, indent=2)}")
            except Exception as e:
                print(f"JSON parsing failed: {e}")
                
    except Exception as e:
        print(f"Chat test failed: {e}")

if __name__ == "__main__":
    test_server()
