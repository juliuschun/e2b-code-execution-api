"""
Test script for E2B Code Execution API
"""

import asyncio
import httpx
import json

async def test_api():
    """Test the E2B API endpoints"""
    
    base_url = "http://localhost:8001"
    
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        print("Testing health endpoint...")
        response = await client.get(f"{base_url}/health")
        print(f"Health: {response.status_code} - {response.json()}")
        
        # Test root endpoint
        print("\nTesting root endpoint...")
        response = await client.get(f"{base_url}/")
        print(f"Root: {response.status_code} - {response.json()}")
        
        # Test code execution
        print("\nTesting code execution...")
        code_request = {
            "code": """
print("Hello from E2B!")
import math
result = math.sqrt(16)
print(f"Square root of 16 is: {result}")

# Test with some data processing
data = [1, 2, 3, 4, 5]
squared = [x**2 for x in data]
print(f"Squared numbers: {squared}")
""",
            "timeout": 10
        }
        
        response = await client.post(f"{base_url}/execute", json=code_request)
        result = response.json()
        print(f"Execute: {response.status_code}")
        print(f"Success: {result.get('success')}")
        print(f"Output: {result.get('output')}")
        if result.get('error'):
            print(f"Error: {result.get('error')}")
        print(f"Execution time: {result.get('execution_time')} seconds")

if __name__ == "__main__":
    asyncio.run(test_api())