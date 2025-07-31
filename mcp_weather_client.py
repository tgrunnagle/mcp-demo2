# MCP SSE Client Example
# File: mcp_sse_client.py

import asyncio
import json
import logging
from typing import Dict, Any, List
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.types import CallToolRequest, ListToolsRequest, GetPromptRequest, ListPromptsRequest

from mcp_base_client import MCPBaseClient

# Configure logging
logger = logging.getLogger(__name__)

class MCPWeatherClient(MCPBaseClient):
    """Example MCP Client that connects to the weather server via SSE"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.sse_url = f"{server_url}/sse"
        self.session = None
        self.exit_stack = AsyncExitStack()
    
    async def connect(self):
        """Connect to the MCP server via SSE"""
        try:
            logger.info(f"Connecting to MCP server at {self.sse_url}")
            
            # Create SSE transport using async context manager
            sse_transport = await self.exit_stack.enter_async_context(sse_client(self.sse_url))
            read_stream, write_stream = sse_transport
            
            # Create session using async context manager
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            # Initialize the session
            init_result = await self.session.initialize()
            logger.info(f"Connected to server: {init_result.serverInfo.name} v{init_result.serverInfo.version}")
            
            return True
            
        except Exception as e:
            logger.exception("Failed to connect to MCP server")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        try:
            await self.exit_stack.aclose()
            self.session = None
            logger.info("Disconnected from MCP server")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the server"""
        try:
            result = await self.session.list_tools()
            tools = []
            for tool in result.tools:
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                })
            return tools
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return []
    
    async def call_tool(self, name: str, **kwargs) -> str:
        """Call a tool on the server"""
        try:
            result = await self.session.call_tool(name, kwargs)
            
            # Extract text content from the result
            if result.content:
                text_parts = []
                for content in result.content:
                    if hasattr(content, 'text'):
                        text_parts.append(content.text)
                return "\n".join(text_parts)
            else:
                return "No content returned"
                
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            return f"Error: {str(e)}"
    
    async def list_prompts(self) -> List[Dict[str, Any]]:
        """List available prompts from the server"""
        try:
            result = await self.session.list_prompts()
            prompts = []
            for prompt in result.prompts:
                prompt_dict = {
                    "name": prompt.name,
                    "description": prompt.description,
                    "arguments": []
                }
                if prompt.arguments:
                    for arg in prompt.arguments:
                        prompt_dict["arguments"].append({
                            "name": arg.name,
                            "description": arg.description,
                            "required": arg.required
                        })
                prompts.append(prompt_dict)
            return prompts
        except Exception as e:
            logger.error(f"Error listing prompts: {e}")
            return []
    
    async def get_prompt(self, name: str, arguments: Dict[str, str] = None) -> str:
        """Get a prompt from the server"""
        try:
            if arguments is None:
                arguments = {}
            
            result = await self.session.get_prompt(name, arguments)
            
            # Extract messages from the prompt result
            if result.messages:
                message_texts = []
                for message in result.messages:
                    if hasattr(message.content, 'text'):
                        message_texts.append(f"{message.role}: {message.content.text}")
                return "\n".join(message_texts)
            else:
                return "No messages in prompt"
                
        except Exception as e:
            logger.error(f"Error getting prompt {name}: {e}")
            return f"Error: {str(e)}"
