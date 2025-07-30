"""
LangChain tool wrapper for MCP clients

This module provides a wrapper that allows MCP tools to be used as LangChain tools.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun

from mcp_base_client import MCPBaseClient


class MCPToolWrapper(BaseTool):
    """LangChain tool wrapper for MCP tools"""
    
    name: str = Field(..., description="Name of the MCP tool")
    description: str = Field(..., description="Description of the MCP tool")
    mcp_client: MCPBaseClient = Field(..., description="MCP client instance")
    tool_name: str = Field(..., description="Name of the tool on the MCP server")
    input_schema: Dict[str, Any] = Field(..., description="Input schema for the tool")
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any,
    ) -> str:
        """Synchronous wrapper for the async MCP tool call"""
        # Parse the input based on the tool's schema
        try:
            # If query is a JSON string, parse it
            if query.strip().startswith('{'):
                arguments = json.loads(query)
            else:
                # For simple tools like weather, assume the query is the city parameter
                # This is a simplification - in a real implementation you'd want to
                # parse the schema more carefully
                if 'city' in str(self.input_schema):
                    arguments = {'city': query}
                else:
                    arguments = {'query': query}
        except json.JSONDecodeError:
            # Fallback: treat as simple string input
            if 'city' in str(self.input_schema):
                arguments = {'city': query}
            else:
                arguments = {'query': query}
        
        # Run the async call in a new event loop or existing one
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we need to handle this differently
                # For now, we'll use a simple approach - in production you might want
                # to use asyncio.create_task() or similar
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._async_run(arguments))
                    return future.result()
            else:
                return asyncio.run(self._async_run(arguments))
        except RuntimeError:
            # No event loop running, create a new one
            return asyncio.run(self._async_run(arguments))
    
    async def _async_run(self, arguments: Dict[str, Any]) -> str:
        """Async implementation of the tool call"""
        try:
            result = await self.mcp_client.call_tool(self.tool_name, arguments)
            return result
        except Exception as e:
            return f"Error calling MCP tool {self.tool_name}: {str(e)}"
    
    async def _arun(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any,
    ) -> str:
        """Async version of the tool call"""
        # Parse the input based on the tool's schema
        try:
            if query.strip().startswith('{'):
                arguments = json.loads(query)
            else:
                if 'city' in str(self.input_schema):
                    arguments = {'city': query}
                else:
                    arguments = {'query': query}
        except json.JSONDecodeError:
            if 'city' in str(self.input_schema):
                arguments = {'city': query}
            else:
                arguments = {'query': query}
        
        return await self._async_run(arguments)


async def discover_mcp_tools(mcp_client: MCPBaseClient) -> List[MCPToolWrapper]:
    """
    Discover available tools from an MCP client and return them as LangChain tools.
    
    Args:
        mcp_client: Connected MCP client instance
        
    Returns:
        List of MCPToolWrapper instances for each available tool
    """
    tools = []
    
    try:
        # Get the list of available tools from the MCP server
        available_tools = await mcp_client.list_tools()
        
        for tool_info in available_tools:
            # Create a LangChain tool wrapper for each MCP tool
            wrapper = MCPToolWrapper(
                name=tool_info['name'],
                description=tool_info['description'],
                mcp_client=mcp_client,
                tool_name=tool_info['name'],
                input_schema=tool_info['inputSchema']
            )
            tools.append(wrapper)
            
    except Exception as e:
        print(f"Error discovering MCP tools: {e}")
        
    return tools


def create_mcp_tool_from_client(mcp_client: MCPBaseClient) -> List[MCPToolWrapper]:
    """
    Synchronous helper function to create MCP tools from a client.
    
    Args:
        mcp_client: Connected MCP client instance
        
    Returns:
        List of MCPToolWrapper instances
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, we need to handle this carefully
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, discover_mcp_tools(mcp_client))
                return future.result()
        else:
            return asyncio.run(discover_mcp_tools(mcp_client))
    except RuntimeError:
        return asyncio.run(discover_mcp_tools(mcp_client))


# Example usage function
async def example_usage():
    """
    Example of how to use the MCP tool wrapper with LangChain
    """
    # Import here to avoid circular imports
    from mcp_weather_client import MCPWeatherClient
    
    # Create and connect MCP client
    client = MCPWeatherClient()
    await client.connect()
    
    try:
        # Discover available tools
        tools = await discover_mcp_tools(client)
        
        print(f"Discovered {len(tools)} MCP tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
        
        # Example: Use a tool
        if tools:
            weather_tool = tools[0]  # Assuming first tool is weather
            result = await weather_tool._arun("San Francisco")
            print(f"Weather result: {result}")
            
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(example_usage())