"""
Test cases for MCP Weather Client functionality.

This test module verifies that the MCP weather client can successfully:
- Connect to the MCP weather server
- List available tools
- Call tools with various parameters
- Handle errors gracefully
- Disconnect properly

Prerequisites:
- MCP weather server should be running on http://localhost:8000
- Run: python mcp_weather_server.py (in a separate terminal)
"""

import asyncio
import pytest
import sys
import os
from typing import List, Dict, Any

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_weather_client import MCPWeatherClient


class TestMCPWeatherClient:
    """Test cases for MCP Weather Client"""
    
    @pytest.fixture
    async def client(self):
        """Create and connect a client for testing"""
        client = MCPWeatherClient("http://localhost:8000")
        connected = await client.connect()
        if not connected:
            pytest.skip("Could not connect to MCP server at http://localhost:8000. Make sure the server is running.")
        
        yield client
        
        # Cleanup: disconnect the client
        await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_connection(self):
        """Test that we can connect to the MCP server"""
        client = MCPWeatherClient("http://localhost:8000")
        
        # Test connection
        connected = await client.connect()
        assert connected, "Should be able to connect to MCP server"
        
        # Test disconnection
        await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_list_tools(self, client):
        """Test listing available tools"""
        tools = await client.list_tools()
        
        # Verify we get a list of tools
        assert isinstance(tools, list), "list_tools should return a list"
        assert len(tools) > 0, "Should have at least one tool available"
        
        # Check for expected tools
        tool_names = [tool['name'] for tool in tools]
        expected_tools = ['get_weather_tool', 'set_weather_tool', 'list_cities_tool']
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Expected tool '{expected_tool}' not found in {tool_names}"
        
        # Verify tool structure
        for tool in tools:
            assert 'name' in tool, "Each tool should have a 'name' field"
            assert 'description' in tool, "Each tool should have a 'description' field"
            assert isinstance(tool['name'], str), "Tool name should be a string"
            assert isinstance(tool['description'], str), "Tool description should be a string"
    
    @pytest.mark.asyncio
    async def test_list_cities_tool(self, client):
        """Test the list_cities_tool"""
        result = await client.call_tool("list_cities_tool", {})
        
        assert isinstance(result, str), "list_cities_tool should return a string"
        assert "Available cities:" in result, "Result should contain 'Available cities:'"
        
        # Check for expected cities
        expected_cities = ["New York", "London", "Tokyo", "Sydney"]
        for city in expected_cities:
            assert city in result, f"Expected city '{city}' not found in result: {result}"
    
    @pytest.mark.asyncio
    async def test_get_weather_tool_valid_city(self, client):
        """Test getting weather for a valid city"""
        result = await client.call_tool("get_weather_tool", {"city": "new_york"})
        
        assert isinstance(result, str), "get_weather_tool should return a string"
        assert "Weather in New York:" in result, "Result should contain weather information for New York"
        assert "°F" in result, "Result should contain temperature in Fahrenheit"
        assert "humidity" in result, "Result should contain humidity information"
    
    @pytest.mark.asyncio
    async def test_get_weather_tool_invalid_city(self, client):
        """Test getting weather for an invalid city"""
        result = await client.call_tool("get_weather_tool", {"city": "nonexistent_city"})
        
        assert isinstance(result, str), "get_weather_tool should return a string"
        assert "Weather data not available" in result, "Should indicate data not available"
        assert "Available cities:" in result, "Should list available cities"
    
    @pytest.mark.asyncio
    async def test_set_weather_tool(self, client):
        """Test setting weather for a city"""
        # Set weather for a new city
        result = await client.call_tool("set_weather_tool", {
            "city": "test_city",
            "temperature": 75.0,
            "condition": "sunny"
        })
        
        assert isinstance(result, str), "set_weather_tool should return a string"
        assert "Weather updated for Test City:" in result, "Should confirm weather update"
        assert "75" in result, "Should contain the temperature"
        assert "sunny" in result, "Should contain the condition"
        
        # Verify we can retrieve the weather we just set
        get_result = await client.call_tool("get_weather_tool", {"city": "test_city"})
        assert "Weather in Test City:" in get_result, "Should be able to get weather for the city we just set"
        assert "75°F" in get_result, "Should contain the temperature we set"
    
    @pytest.mark.asyncio
    async def test_tool_with_missing_parameters(self, client):
        """Test calling a tool with missing required parameters"""
        # This should handle the error gracefully
        result = await client.call_tool("get_weather_tool", {})
        
        # The result should indicate an error or handle missing parameters
        assert isinstance(result, str), "Should return a string even with missing parameters"
        # The exact error handling depends on the implementation
    
    @pytest.mark.asyncio
    async def test_nonexistent_tool(self, client):
        """Test calling a tool that doesn't exist"""
        result = await client.call_tool("nonexistent_tool", {})
        
        # Should handle unknown tools gracefully
        assert isinstance(result, str), "Should return a string for unknown tools"
    
    @pytest.mark.asyncio
    async def test_multiple_operations(self, client):
        """Test performing multiple operations in sequence"""
        # List tools
        tools = await client.list_tools()
        assert len(tools) > 0, "Should have tools available"
        
        # List cities
        cities_result = await client.call_tool("list_cities_tool", {})
        assert "Available cities:" in cities_result, "Should list cities"
        
        # Get weather for multiple cities
        for city in ["new_york", "london", "tokyo"]:
            weather_result = await client.call_tool("get_weather_tool", {"city": city})
            assert f"Weather in {city.replace('_', ' ').title()}:" in weather_result, f"Should get weather for {city}"
        
        # Set weather for a new city
        set_result = await client.call_tool("set_weather_tool", {
            "city": "test_multiple",
            "temperature": 68.0,
            "condition": "cloudy"
        })
        assert "Weather updated" in set_result, "Should update weather successfully"


# Standalone test functions for running without pytest
async def run_basic_tests():
    """Run basic tests without pytest framework"""
    print("=" * 60)
    print("MCP Weather Client Test Suite")
    print("=" * 60)
    
    client = MCPWeatherClient("http://localhost:8000")
    
    try:
        # Test 1: Connection
        print("\n1. Testing connection...")
        connected = await client.connect()
        if not connected:
            print("❌ FAILED: Could not connect to MCP server")
            print("   Make sure the server is running: python mcp_weather_server.py")
            return
        print("✅ PASSED: Successfully connected to MCP server")
        
        # Test 2: List tools
        print("\n2. Testing list_tools...")
        tools = await client.list_tools()
        expected_tools = ['get_weather_tool', 'set_weather_tool', 'list_cities_tool']
        tool_names = [tool['name'] for tool in tools]
        
        all_tools_found = all(tool in tool_names for tool in expected_tools)
        if all_tools_found:
            print(f"✅ PASSED: Found all expected tools: {tool_names}")
        else:
            print(f"❌ FAILED: Missing tools. Expected: {expected_tools}, Found: {tool_names}")
        
        # Test 3: List cities
        print("\n3. Testing list_cities_tool...")
        cities_result = await client.call_tool("list_cities_tool", {})
        if "Available cities:" in cities_result:
            print(f"✅ PASSED: {cities_result}")
        else:
            print(f"❌ FAILED: Unexpected result: {cities_result}")
        
        # Test 4: Get weather
        print("\n4. Testing get_weather_tool...")
        weather_result = await client.call_tool("get_weather_tool", {"city": "new_york"})
        if "Weather in New York:" in weather_result and "°F" in weather_result:
            print(f"✅ PASSED: {weather_result}")
        else:
            print(f"❌ FAILED: Unexpected result: {weather_result}")
        
        # Test 5: Set weather
        print("\n5. Testing set_weather_tool...")
        set_result = await client.call_tool("set_weather_tool", {
            "city": "test_city",
            "temperature": 72.0,
            "condition": "partly_cloudy"
        })
        if "Weather updated" in set_result:
            print(f"✅ PASSED: {set_result}")
            
            # Verify the weather was set
            verify_result = await client.call_tool("get_weather_tool", {"city": "test_city"})
            if "Weather in Test City:" in verify_result and "72.0°F" in verify_result:
                print(f"✅ PASSED: Verification successful: {verify_result}")
            else:
                print(f"❌ FAILED: Could not verify weather update: {verify_result}")
        else:
            print(f"❌ FAILED: Unexpected result: {set_result}")
        
        print("\n" + "=" * 60)
        print("Test Suite Completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ ERROR: Test failed with exception: {e}")
    
    finally:
        await client.disconnect()
        print("Disconnected from MCP server")


if __name__ == "__main__":
    # Run the basic tests
    asyncio.run(run_basic_tests())
