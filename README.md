# MCP Demo 2 - Model Context Protocol Integration

A complete demonstration of the Model Context Protocol (MCP) with LangChain integration, featuring:
- **MCP Weather Server**: FastMCP server exposing weather tools via SSE transport
- **MCP Weather Client**: Client for connecting to MCP servers and calling tools
- **LangChain Integration**: Tool wrapper for using MCP tools with LangChain agents
- **Ollama Integration**: Local LLM integration for natural language interactions
- **Automated Tests**: Comprehensive test suite for validation

## Setup

1. **Create and activate virtual environment:**
```bash
uv env
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac
```

2. **Install dependencies:**
```bash
uv pip install -r requirements.txt
```

## Running the MCP Weather Server

1. **Start the MCP server:**
```bash
python mcp_weather_server.py
```

The server will start on http://localhost:8000 with:
- **MCP SSE endpoint**: `/sse` - For MCP client connections
- **Available tools**: `get_weather_tool`, `set_weather_tool`, `list_cities_tool`

## Testing the System

### Automated Tests

1. **Start the MCP server** (in one terminal):
```bash
python mcp_weather_server.py
```

2. **Run the test suite** (in another terminal):
```bash
# Basic test suite (recommended)
python run_tests.py

# Full pytest suite
python run_tests.py --pytest

# Or run pytest directly
pytest tests/ -v --asyncio-mode=auto
```

**Test Coverage:**
- ✅ Server connectivity and health checks
- ✅ Tool discovery and listing
- ✅ Weather operations (get, set, list cities)
- ✅ Error handling for invalid inputs
- ✅ Multiple operation sequences
- ✅ Data persistence verification

## Running the Host

1. Start the ollama server and run a model:
```bash
ollama serve
ollama run llama3.2:3b
```

2. In another terminal (with the same virtual environment), run the host:
```bash
python mcp_host.py
```

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