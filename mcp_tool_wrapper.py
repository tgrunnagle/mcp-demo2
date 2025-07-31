"""
LangChain tool wrapper for MCP clients

This module provides a wrapper that allows MCP tools to be used as LangChain tools.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field, create_model
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from typing import override
from mcp_base_client import MCPBaseClient
import logging

logger = logging.getLogger(__name__)

class MCPToolWrapper(BaseTool):
    """LangChain tool wrapper for MCP tools"""
    
    name: str = Field(..., description="Name of the MCP tool")
    description: str = Field(..., description="Description of the MCP tool")
    mcp_client: MCPBaseClient = Field(..., description="MCP client instance")

    def __init__(self, tool_config: Dict[str, Any], **kwargs):
        args_schema = self._get_tool_base_model(tool_config)
        super().__init__(args_schema=args_schema, **kwargs)
    
    def _get_tool_base_model(self, tool_config: Dict[str, Any]) -> Type[BaseModel]:
        """Create a Pydantic input model from the input schema."""
        fields = {}
        
        type_mapping = {
            'string': str,
            'str': str,
            'integer': int,
            'int': int,
            'number': float,
            'float': float,
            'boolean': bool,
            'bool': bool,
            'list': list,
            'array': list,
            'dict': dict,
            'object': dict,
            'any': Any,
        }

        for field_name, field_config in tool_config['inputSchema']['properties'].items():
            field_type = type_mapping.get(field_config.get('type', 'str'), str)
            default = field_config.get('default', ...)
            description = field_config.get('description', 'No description provided')
            
            if default == ...:
                fields[field_name] = (field_type, Field(description=description))
            else:
                fields[field_name] = (field_type, Field(default=default, description=description))
        
        return create_model(tool_config['name'], **fields)
    
    class Config:
        arbitrary_types_allowed = True

    @override
    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs,
    ) -> str:
        """Synchronous wrapper for the async MCP tool call"""
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
    
    @override
    async def _arun(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs,
    ) -> str:
        """Async version of the tool call"""
        # Parse the input based on the tool's schema
        return await self._async_run(**kwargs)

    async def _async_run(self, **kwargs) -> str:
        """Async implementation of the tool call"""
        try:
            result = await self.mcp_client.call_tool(self.name, **kwargs)
            return result
        except Exception as e:
            return f"Error calling MCP tool {self.name}: {str(e)}"

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
                tool_config=tool_info,
                name=tool_info['name'],
                description=tool_info['description'],
                mcp_client=mcp_client,
            )
            tools.append(wrapper)
            
    except Exception as e:
       logger.exception("Error discovering MCP tools")
        
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
        
        logger.info(f"Discovered {len(tools)} MCP tools:")
        for tool in tools:
            logger.info(f"- {tool.name}: {tool.description}")
        
        # Example: Use a tool
        if tools:
            weather_tool = tools[0]  # Assuming first tool is weather
            result = await weather_tool._arun("San Francisco")
            logger.info(f"Weather result: {result}")
            
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(example_usage())