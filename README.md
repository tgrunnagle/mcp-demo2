# mcp-demo2

## Setup

```
uv env
.venv\Scripts\activate
uv pip install -r requirements.txt
```

## Running the Server

1. Start the MCP server:
```bash
python mcp_sse_server.py
```

The server will start on http://localhost:8000 with the following endpoints:
- `/` - Server information
- `/health` - Health check
- `/sse` - SSE endpoint for MCP communication

## Running the Client

1. In another terminal (with the same virtual environment), run the demo client:
```bash
python mcp_weather_client.py
```

2. Or run the interactive client:
```bash
python mcp_weather_client.py interactive
```

## API Endpoints

### Server Endpoints
- `GET /` - Server information and available endpoints
- `GET /health` - Health check with server status
- `GET /sse` - Server-Sent Events endpoint for MCP communication

### MCP Tools
- `get_weather(city)` - Get current weather for a city
- `list_cities()` - List all available cities
- `update_weather(city, temp, humidity, condition)` - Update weather data

### MCP Prompts
- `weather_report(city)` - Generate weather report prompt for a city
- `weather_summary()` - Generate summary prompt for all weather data

## Example Usage

### Using the Client Library
```python
import asyncio
from mcp_sse_client import WeatherMCPClient

async def main():
    client = WeatherMCPClient()
    await client.connect()
    
    # Get weather
    weather = await client.call_tool("get_weather", {"city": "london"})
    print(weather)
    
    # List tools
    tools = await client.list_tools()
    for tool in tools:
        print(f"{tool['name']}: {tool['description']}")
    
    await client.disconnect()

asyncio.run(main())
```

### Direct HTTP Access
```bash
# Health check
curl http://localhost:8000/health

# Server info
curl http://localhost:8000/

# SSE endpoint (will stream MCP messages)
curl -N http://localhost:8000/sse
```

## Architecture

The example demonstrates:

1. **MCP Server**: Uses the `mcp` library to create a server that exposes weather-related tools and prompts
2. **SSE Transport**: FastAPI endpoint that provides Server-Sent Events for real-time MCP communication
3. **MCP Client**: Uses the `mcp` library to connect to the server via SSE and interact with tools/prompts
4. **Error Handling**: Proper error handling and logging throughout
5. **Type Safety**: Uses Pydantic models and proper typing for robust communication

## Features

- **Tools**: Callable functions that perform actions (get weather, update data, etc.)
- **Prompts**: Template generators for creating structured prompts
- **Real-time Communication**: SSE-based transport for efficient client-server communication
- **Health Monitoring**: Built-in health checks and logging
- **CORS Support**: Cross-origin resource sharing for web clients
- **Interactive Mode**: Command-line interface for testing