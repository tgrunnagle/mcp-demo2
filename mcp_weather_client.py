# MCP SSE Client Example
# File: mcp_sse_client.py

import asyncio
import json
import logging
from typing import Dict, Any, List

from mcp.client import Client
from mcp.client.sse import SseClientTransport
from mcp.types import CallToolRequest, ListToolsRequest, GetPromptRequest, ListPromptsRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeatherMCPClient:
    """Example MCP Client that connects to the weather server via SSE"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.sse_url = f"{server_url}/sse"
        self.client = None
        self.transport = None
    
    async def connect(self):
        """Connect to the MCP server via SSE"""
        try:
            logger.info(f"Connecting to MCP server at {self.sse_url}")
            
            # Create SSE transport
            self.transport = SseClientTransport(self.sse_url)
            
            # Create MCP client
            self.client = Client()
            
            # Connect to the server
            await self.client.connect(self.transport)
            
            # Initialize the session
            init_result = await self.client.initialize()
            logger.info(f"Connected to server: {init_result.serverInfo.name} v{init_result.serverInfo.version}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.client:
            await self.client.close()
        if self.transport:
            await self.transport.close()
        logger.info("Disconnected from MCP server")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the server"""
        try:
            result = await self.client.list_tools()
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
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on the server"""
        try:
            result = await self.client.call_tool(name, arguments)
            
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
            result = await self.client.list_prompts()
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
            
            result = await self.client.get_prompt(name, arguments)
            
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

async def demo_client():
    """Demonstrate the MCP client functionality"""
    client = WeatherMCPClient()
    
    # Connect to server
    if not await client.connect():
        return
    
    try:
        print("=" * 50)
        print("MCP Weather Client Demo")
        print("=" * 50)
        
        # List available tools
        print("\n1. Available Tools:")
        print("-" * 20)
        tools = await client.list_tools()
        for tool in tools:
            print(f"• {tool['name']}: {tool['description']}")
        
        # List available cities
        print("\n2. Available Cities:")
        print("-" * 20)
        cities_result = await client.call_tool("list_cities", {})
        print(cities_result)
        
        # Get weather for a specific city
        print("\n3. Weather for New York:")
        print("-" * 25)
        weather_result = await client.call_tool("get_weather", {"city": "new_york"})
        print(weather_result)
        
        # Update weather data
        print("\n4. Updating Weather for Paris:")
        print("-" * 30)
        update_result = await client.call_tool("update_weather", {
            "city": "paris",
            "temp": 64,
            "humidity": 71,
            "condition": "cloudy"
        })
        print(update_result)
        
        # Get weather for the new city
        print("\n5. Weather for Paris (after update):")
        print("-" * 35)
        paris_weather = await client.call_tool("get_weather", {"city": "paris"})
        print(paris_weather)
        
        # List available prompts
        print("\n6. Available Prompts:")
        print("-" * 20)
        prompts = await client.list_prompts()
        for prompt in prompts:
            print(f"• {prompt['name']}: {prompt['description']}")
            if prompt['arguments']:
                print(f"  Arguments: {[arg['name'] + (' (required)' if arg['required'] else ' (optional)') for arg in prompt['arguments']]}")
        
        # Get a weather report prompt
        print("\n7. Weather Report Prompt for London:")
        print("-" * 35)
        prompt_result = await client.get_prompt("weather_report", {"city": "london"})
        print(prompt_result)
        
        # Get weather summary prompt
        print("\n8. Weather Summary Prompt:")
        print("-" * 25)
        summary_prompt = await client.get_prompt("weather_summary")
        print(summary_prompt)
        
    finally:
        # Always disconnect
        await client.disconnect()

async def interactive_client():
    """Interactive client for testing"""
    client = WeatherMCPClient()
    
    if not await client.connect():
        return
    
    print("Interactive MCP Weather Client")
    print("Commands: tools, prompts, weather <city>, update <city> <temp> <humidity> <condition>, prompt <name> [args], quit")
    
    try:
        while True:
            try:
                command = input("\n> ").strip().split()
                if not command:
                    continue
                
                if command[0] == "quit":
                    break
                
                elif command[0] == "tools":
                    tools = await client.list_tools()
                    for tool in tools:
                        print(f"• {tool['name']}: {tool['description']}")
                
                elif command[0] == "prompts":
                    prompts = await client.list_prompts()
                    for prompt in prompts:
                        print(f"• {prompt['name']}: {prompt['description']}")
                
                elif command[0] == "weather" and len(command) > 1:
                    city = command[1]
                    result = await client.call_tool("get_weather", {"city": city})
                    print(result)
                
                elif command[0] == "update" and len(command) > 4:
                    city, temp, humidity, condition = command[1], float(command[2]), float(command[3]), command[4]
                    result = await client.call_tool("update_weather", {
                        "city": city,
                        "temp": temp,
                        "humidity": humidity,
                        "condition": condition
                    })
                    print(result)
                
                elif command[0] == "prompt" and len(command) > 1:
                    prompt_name = command[1]
                    args = {}
                    if len(command) > 2:
                        # Simple argument parsing: prompt weather_report city=london
                        for arg in command[2:]:
                            if "=" in arg:
                                key, value = arg.split("=", 1)
                                args[key] = value
                    
                    result = await client.get_prompt(prompt_name, args)
                    print(result)
                
                else:
                    print("Unknown command or missing arguments")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        # Run interactive mode
        asyncio.run(interactive_client())
    else:
        # Run demo
        asyncio.run(demo_client())