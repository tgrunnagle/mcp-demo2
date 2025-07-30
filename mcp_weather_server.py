# MCP Server with SSE Endpoint Example
# File: mcp_sse_server.py

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.sse import SseServerTransport
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    Tool,
    TextContent,
    EmbeddedResource,
    GetPromptRequest,
    GetPromptResult,
    ListPromptsRequest,
    Prompt,
    PromptArgument,
    PromptMessage,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeatherMCPServer:
    """Example MCP Server that provides weather-related tools and prompts"""
    
    def __init__(self):
        self.server = Server("weather-server")
        self.weather_data = {
            "new_york": {"temp": 72, "humidity": 65, "condition": "partly_cloudy"},
            "london": {"temp": 59, "humidity": 78, "condition": "rainy"},
            "tokyo": {"temp": 68, "humidity": 82, "condition": "sunny"},
            "sydney": {"temp": 75, "humidity": 60, "condition": "clear"}
        }
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up the MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="get_weather",
                    description="Get current weather for a city",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "City name (e.g., 'new_york', 'london')"
                            }
                        },
                        "required": ["city"]
                    }
                ),
                Tool(
                    name="list_cities",
                    description="List all available cities for weather data",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="update_weather",
                    description="Update weather data for a city",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"},
                            "temp": {"type": "number"},
                            "humidity": {"type": "number"},
                            "condition": {"type": "string"}
                        },
                        "required": ["city", "temp", "humidity", "condition"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                if name == "get_weather":
                    city = arguments.get("city", "").lower()
                    if city in self.weather_data:
                        weather = self.weather_data[city]
                        result = f"Weather in {city.title()}:\n"
                        result += f"Temperature: {weather['temp']}°F\n"
                        result += f"Humidity: {weather['humidity']}%\n"
                        result += f"Condition: {weather['condition'].replace('_', ' ').title()}"
                        return [TextContent(type="text", text=result)]
                    else:
                        return [TextContent(type="text", text=f"Weather data not available for {city}")]
                
                elif name == "list_cities":
                    cities = list(self.weather_data.keys())
                    city_list = "\n".join([f"- {city.replace('_', ' ').title()}" for city in cities])
                    return [TextContent(type="text", text=f"Available cities:\n{city_list}")]
                
                elif name == "update_weather":
                    city = arguments.get("city", "").lower()
                    temp = arguments.get("temp")
                    humidity = arguments.get("humidity")
                    condition = arguments.get("condition")
                    
                    self.weather_data[city] = {
                        "temp": temp,
                        "humidity": humidity,
                        "condition": condition
                    }
                    return [TextContent(type="text", text=f"Weather updated for {city.title()}")]
                
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
                    
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        @self.server.list_prompts()
        async def handle_list_prompts() -> List[Prompt]:
            """List available prompts"""
            return [
                Prompt(
                    name="weather_report",
                    description="Generate a weather report for a city",
                    arguments=[
                        PromptArgument(
                            name="city",
                            description="City name",
                            required=True
                        )
                    ]
                ),
                Prompt(
                    name="weather_summary",
                    description="Generate a summary of all weather data",
                    arguments=[]
                )
            ]
        
        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: Dict[str, str]) -> GetPromptResult:
            """Handle prompt requests"""
            if name == "weather_report":
                city = arguments.get("city", "").lower()
                if city in self.weather_data:
                    weather = self.weather_data[city]
                    prompt_text = f"Create a detailed weather report for {city.title()} based on this data: "
                    prompt_text += f"Temperature: {weather['temp']}°F, "
                    prompt_text += f"Humidity: {weather['humidity']}%, "
                    prompt_text += f"Condition: {weather['condition']}"
                    
                    return GetPromptResult(
                        description=f"Weather report prompt for {city.title()}",
                        messages=[
                            PromptMessage(
                                role="user",
                                content=TextContent(type="text", text=prompt_text)
                            )
                        ]
                    )
                else:
                    return GetPromptResult(
                        description="Error: City not found",
                        messages=[
                            PromptMessage(
                                role="user",
                                content=TextContent(type="text", text=f"No weather data available for {city}")
                            )
                        ]
                    )
            
            elif name == "weather_summary":
                summary_text = "Generate a comprehensive weather summary based on this data:\n"
                for city, data in self.weather_data.items():
                    summary_text += f"- {city.title()}: {data['temp']}°F, {data['humidity']}% humidity, {data['condition']}\n"
                
                return GetPromptResult(
                    description="Weather summary prompt for all cities",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(type="text", text=summary_text)
                        )
                    ]
                )
            
            else:
                raise ValueError(f"Unknown prompt: {name}")

# Global server instance
weather_server = WeatherMCPServer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    logger.info("Starting MCP Weather Server...")
    yield
    logger.info("Shutting down MCP Weather Server...")

# Create FastAPI app
app = FastAPI(
    title="MCP Weather Server",
    description="Example MCP Server with SSE endpoint for weather data",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint with server info"""
    return {
        "name": "MCP Weather Server",
        "version": "1.0.0",
        "description": "Example MCP Server with SSE endpoint",
        "endpoints": {
            "sse": "/sse",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cities_available": len(weather_server.weather_data)
    }

@app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP communication"""
    logger.info("New SSE connection established")
    
    async def event_generator():
        """Generate SSE events"""
        try:
            # Create SSE transport
            transport = SseServerTransport()
            
            # Initialize the transport with the request
            await transport.connect(request)
            
            # Run the MCP server with SSE transport
            async with weather_server.server.run_server(
                transport,
                InitializationOptions(
                    server_name="weather-server",
                    server_version="1.0.0"
                )
            ) as server_session:
                # Keep the connection alive and handle messages
                async for message in transport:
                    if message:
                        yield f"data: {json.dumps(message)}\n\n"
                        
        except asyncio.CancelledError:
            logger.info("SSE connection cancelled")
        except Exception as e:
            logger.error(f"Error in SSE endpoint: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "mcp_weather_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )