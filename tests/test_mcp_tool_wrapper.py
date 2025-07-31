"""
Test suite for MCP Tool Wrapper (LangChain integration)

This module tests the MCPToolWrapper class and related functions that provide
LangChain integration for MCP tools.
"""

import pytest
from typing import Dict, Any, List

# Import the modules we're testing
from mcp_tool_wrapper import MCPToolWrapper, discover_mcp_tools
from mcp_client import MCPClient


class TestMCPToolWrapper:
    """Test suite for MCPToolWrapper class"""
    
    @pytest.fixture
    async def real_client(self):
        """Create a real MCP client for testing (requires server)"""
        client = MCPClient("http://localhost:8000")
        connected = await client.connect()
        if not connected:
            pytest.skip("Could not connect to MCP server at http://localhost:8000. Make sure the server is running.")
        
        yield client
        
        await client.disconnect()
    
    @pytest.fixture
    async def weather_tool_wrapper(self, real_client):
        """Create a weather tool wrapper for testing"""
        tool_config = {
            "name": "get_weather_tool",
            "description": "Get current weather for a city",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                },
                "required": ["city"]
            }
        }
        return MCPToolWrapper(
            tool_config=tool_config,
            name="get_weather_tool",
            description="Get current weather for a city",
            mcp_client=real_client
        )
    
    @pytest.mark.asyncio
    async def test_tool_wrapper_creation(self, real_client):
        """Test that we can create a tool wrapper"""
        tool_config = {
            "name": "get_weather_tool",
            "description": "Get current weather for a city",
            "inputSchema": {
                "properties": {
                    "city": {
                        "title": "City",
                        "type": "string"
                    }
                },
                "required": [
                    "city"
                ],
                "title": "get_weather_toolArguments",
                "type": "object"
            }
        }
        wrapper = MCPToolWrapper(
            tool_config=tool_config,
            name="test_tool",
            description="Test tool",
            mcp_client=real_client
        )
        
        assert wrapper.name == "test_tool"
        assert wrapper.description == "Test tool"
        assert wrapper.mcp_client == real_client


class TestToolDiscovery:
    """Test suite for tool discovery functions"""
    
    @pytest.fixture
    async def real_client(self):
        """Create a real MCP client for testing (requires server)"""
        client = MCPClient("http://localhost:8000")
        connected = await client.connect()
        if not connected:
            pytest.skip("Could not connect to MCP server at http://localhost:8000. Make sure the server is running.")
        
        yield client
        
        await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_discover_mcp_tools(self, real_client):
        """Test discovering tools from MCP client"""
        tools = await discover_mcp_tools(real_client)
        
        assert len(tools) >= 3  # Should have at least our 3 weather tools
        assert all(isinstance(tool, MCPToolWrapper) for tool in tools)
        
        tool_names = [tool.name for tool in tools]
        assert "get_weather_tool" in tool_names
        assert "set_weather_tool" in tool_names
        assert "list_cities_tool" in tool_names
    
    @pytest.mark.asyncio
    async def test_discovered_tools_are_functional(self, real_client):
        """Test that discovered tools actually work"""
        tools = await discover_mcp_tools(real_client)
        
        # Find the weather tool
        weather_tool = next(tool for tool in tools if tool.name == "get_weather_tool")
        
        # Test it works
        result = await weather_tool._arun(city="New York")
        assert "Weather in New York" in result
        
        # Find the list cities tool
        list_tool = next(tool for tool in tools if tool.name == "list_cities_tool")
        
        # Test it works (should handle empty input)
        result = await list_tool._arun()
        assert "Available cities" in result


class TestIntegrationScenarios:
    """Test suite for integration scenarios"""
    
    @pytest.fixture
    async def real_client(self):
        """Create a real MCP client for testing (requires server)"""
        client = MCPClient("http://localhost:8000")
        connected = await client.connect()
        if not connected:
            pytest.skip("Could not connect to MCP server at http://localhost:8000. Make sure the server is running.")
        
        yield client
        
        await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, real_client):
        """Test the complete workflow: discover tools, create wrappers, use them"""
        # Discover tools
        tools = await discover_mcp_tools(real_client)
        assert len(tools) > 0
        
        # Use each tool
        for tool in tools:
            if tool.name == "get_weather_tool":
                result = await tool._arun(city="New York")
                assert "Weather in New York" in result
            elif tool.name == "list_cities_tool":
                result = await tool._arun()
                assert "Available cities" in result
    
    @pytest.mark.asyncio
    async def test_langchain_compatibility(self, real_client):
        """Test that our wrapper is compatible with LangChain BaseTool interface"""
        tool_config = {
            "name": "get_weather_tool",
            "description": "Get current weather for a city",
            "inputSchema": {
                "properties": {
                    "city": {
                        "title": "City",
                        "type": "string"
                    }
                },
                "required": [
                    "city"
                ],
                "title": "get_weather_toolArguments",
                "type": "object"
            }
        }
        wrapper = MCPToolWrapper(
            tool_config=tool_config,
            name="test_tool",
            description="Test tool",
            mcp_client=real_client
        )
        
        # Check that it has the required LangChain BaseTool attributes
        assert hasattr(wrapper, 'name')
        assert hasattr(wrapper, 'description')
        assert hasattr(wrapper, '_run')
        assert hasattr(wrapper, '_arun')
        
        # Check that name and description are strings
        assert isinstance(wrapper.name, str)
        assert isinstance(wrapper.description, str)

