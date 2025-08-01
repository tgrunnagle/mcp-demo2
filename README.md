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
python run_tests.py
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

## API Endpoints

### Server Endpoints
- `GET /sse` - Server-Sent Events endpoint for MCP communication

### MCP Tools
- `get_weather(city)` - Get current weather for a city
- `list_cities()` - List all available cities
- `update_weather(city, temp, humidity, condition)` - Update weather data
