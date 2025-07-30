#!/usr/bin/env python3
"""
Test runner script for MCP Weather Demo

This script provides an easy way to run tests for the MCP weather system.
It can run tests with or without pytest, and provides clear instructions.

Usage:
    python run_tests.py              # Run basic tests without pytest
    python run_tests.py --pytest     # Run full pytest suite
    python run_tests.py --help       # Show help
"""

import asyncio
import sys
import subprocess
import os
from pathlib import Path

def check_server_running():
    """Check if the MCP server is running on localhost:8000 by connecting to SSE endpoint"""
    import httpx
    import asyncio
    
    async def _check_sse_endpoint():
        """Async function to check SSE endpoint"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Make a streaming request to the SSE endpoint
                async with client.stream('GET', 'http://localhost:8000/sse') as response:
                    # Check if we get a 200 response
                    if response.status_code != 200:
                        print("Status code: " + str(response.status_code))
                        return False
                    
                    # Check if response has SSE headers
                    content_type = response.headers.get('content-type', '')
                    if 'text/event-stream' not in content_type:
                        print("Content type: " + content_type)
                        return False
                    
                    print("waiting for data...")
                    # Try to read a small amount of data to confirm SSE format
                    async for chunk in response.aiter_bytes(chunk_size=1):
                        print("data received: " + str(chunk))
                        # If we get any data, the SSE endpoint is working
                        # We don't need to parse the full MCP protocol, just confirm SSE is active
                        if chunk:
                            return True
                        break
                    
                    return True  # Connection successful even if no immediate data
                    
        except Exception as e:
            print(e)
            return False
    
    try:
        # Run the async check
        return asyncio.run(_check_sse_endpoint())
    except Exception:
        return False

def print_help():
    """Print help information"""
    print("""
MCP Weather Demo Test Runner

Usage:
    python run_tests.py              # Run basic tests without pytest
    python run_tests.py --pytest     # Run full pytest suite  
    python run_tests.py --help       # Show this help

Prerequisites:
1. Install dependencies:
   pip install -r requirements.txt

2. Start the MCP server in a separate terminal:
   python mcp_weather_server.py

3. Run the tests:
   python run_tests.py

Test Coverage:
- MCP client connection to server
- Tool discovery and listing
- Weather tool functionality (get, set, list cities)
- Error handling for invalid inputs
- Multiple operation sequences
""")

async def run_basic_tests():
    """Run the basic test suite without pytest"""
    # Import the test module
    sys.path.insert(0, str(Path(__file__).parent))
    from tests.test_mcp_weather_client import run_basic_tests
    
    await run_basic_tests()

def run_pytest_tests():
    """Run the full pytest suite"""
    tests_dir = Path(__file__).parent / "tests"
    
    print("Running pytest test suite...")
    print("=" * 60)
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(tests_dir), 
            "-v", 
            "--tb=short",
            "--asyncio-mode=auto"
        ], capture_output=False, text=True)
        
        return result.returncode == 0
    except FileNotFoundError:
        print("❌ ERROR: pytest not found. Install it with: pip install pytest pytest-asyncio")
        return False

def main():
    """Main entry point"""
    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
        return
    
    print("MCP Weather Demo Test Runner")
    print("=" * 40)
    
    # Check if server is running
    print("Checking if MCP server is running...")
    if not check_server_running():
        print("❌ ERROR: MCP server is not running on http://localhost:8000")
        print("\nTo start the server, run in a separate terminal:")
        print("   python mcp_weather_server.py")
        print("\nThen run the tests again.")
        return
    
    print("✅ MCP server is running")
    
    if "--pytest" in sys.argv:
        # Run pytest suite
        success = run_pytest_tests()
        if success:
            print("\n✅ All pytest tests passed!")
        else:
            print("\n❌ Some pytest tests failed.")
    else:
        # Run basic tests
        print("\nRunning basic test suite...")
        print("(Use --pytest for full test suite)")
        print()
        
        try:
            asyncio.run(run_basic_tests())
        except KeyboardInterrupt:
            print("\n\nTests interrupted by user.")
        except Exception as e:
            print(f"\n❌ ERROR: Tests failed with exception: {e}")

if __name__ == "__main__":
    main()
