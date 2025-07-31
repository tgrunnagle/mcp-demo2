# MCP Server with SSE Endpoint Example
# File: mcp_sse_server.py

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Weather data storage
weather_data = {
    "new_york": {"temp": 72, "humidity": 65, "condition": "partly_cloudy"},
    "london": {"temp": 59, "humidity": 78, "condition": "rainy"},
    "tokyo": {"temp": 68, "humidity": 82, "condition": "sunny"},
    "sydney": {"temp": 75, "humidity": 60, "condition": "clear"}
}

def get_weather(city: str) -> str:
    """Get weather for a city"""
    city = city.lower().replace(" ", "_")
    if city in weather_data:
        data = weather_data[city]
        return f"Weather in {city.replace('_', ' ').title()}: {data['temp']}°F, {data['humidity']}% humidity, {data['condition'].replace('_', ' ')}"
    else:
        available_cities = ", ".join([c.replace("_", " ").title() for c in weather_data.keys()])
        return f"Weather data not available for {city.replace('_', ' ').title()}. Available cities: {available_cities}"

def set_weather(city: str, temperature: float, condition: str) -> str:
    """Set weather for a city"""
    city = city.lower().replace(" ", "_")
    condition = condition.lower().replace(" ", "_")
    
    # Calculate a reasonable humidity based on condition
    humidity_map = {
        "sunny": 45, "clear": 40, "partly_cloudy": 60,
        "cloudy": 70, "rainy": 85, "stormy": 90
    }
    humidity = humidity_map.get(condition, 60)
    
    weather_data[city] = {
        "temp": temperature,
        "humidity": humidity,
        "condition": condition
    }
    
    return f"Weather updated for {city.replace('_', ' ').title()}: {temperature}°F, {humidity}% humidity, {condition.replace('_', ' ')}"

def list_cities() -> str:
    """List all available cities"""
    cities = [city.replace("_", " ").title() for city in weather_data.keys()]
    return f"Available cities: {', '.join(cities)}"

# Create FastMCP server instance
mcp_server = FastMCP("weather-server")

# Register tools with FastMCP server
@mcp_server.tool()
def get_weather_tool(city: str) -> str:
    """Get current weather for a city"""
    return get_weather(city)

@mcp_server.tool()
def set_weather_tool(city: str, temperature: float, condition: str) -> str:
    """Set weather for a city"""
    return set_weather(city, temperature, condition)

@mcp_server.tool()
def list_cities_tool() -> str:
    """List all available cities"""
    return list_cities()

if __name__ == "__main__":
    # Run FastMCP server directly with SSE transport
    print("Starting FastMCP Weather Server with SSE transport...")
    print("MCP Tools available:")
    print("  - get_weather_tool(city)")
    print("  - set_weather_tool(city, temperature, condition)")
    print("  - list_cities_tool()")
    print("")
    print("Server endpoints:")
    print("  - MCP SSE: http://localhost:8000/sse")
    print("  - Health: Use MCP client to check server status")
    print("")
    print("Connect MCP client to: http://localhost:8000/sse")
    
    # Run FastMCP server with SSE transport (defaults to localhost:8000)
    mcp_server.run(transport="sse")