# MCP (Model Context Protocol) Integration

This project now supports MCP servers for extending agent capabilities with custom tools!

## What is MCP?

MCP (Model Context Protocol) is a protocol that allows AI agents to interact with external tools and services. This integration enables your agents to:

- Access filesystem operations
- Query databases
- Make API calls
- And any custom functionality you want to add!

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:

- `mcp` - Core MCP protocol library
- `anyio` - Async I/O support
- `fastmcp` - Optional FastMCP for easier server creation

### 2. Configure MCP Tools in Your Workflow

Add an `mcp_tools` section to your YAML configuration:

```yaml
# Define MCP servers
mcp_tools:
  filesystem:
    server: "python"
    args:
      - "mcp_filesystem_server.py"
    env: {}

  # Add more servers as needed
  custom_tool:
    server: "node"
    args:
      - "path/to/server.js"
    env:
      API_KEY: "your-key"
```

### 3. Assign Tools to Agents

Add `mcp_tools` to your agent configuration:

```yaml
agents:
  - id: "file_agent"
    role: "File Manager"
    goal: "Manage files"
    model: gemini-2.5-flash
    mcp_tools:
      - filesystem # References the MCP server defined above
    instruction: |
      Use the filesystem tools to manage files and directories.
```

## Architecture

### Components

1. **mcp_manager.py** - Core MCP management
   - Starts and manages MCP server processes
   - Extracts tool schemas
   - Routes tool execution to appropriate servers
2. **custom_stdio_client** - Windows-compatible MCP client
   - Uses asyncio for process management
   - Handles JSON-RPC communication
   - Manages server lifecycle

3. **Agent.py Integration**
   - Automatically initializes MCP manager when configured
   - Injects MCP tool schemas into agent prompts
   - Provides tools to LLM model configuration

### Workflow

1. **Initialization**: When `run_agent()` is called with a YAML containing `mcp_tools`
   - MCPManager is created with the configuration
   - Each MCP server is started as a subprocess
   - Tool schemas are extracted and cached

2. **Execution**: When an agent with `mcp_tools` executes
   - Tool schemas are added to the agent's prompt
   - Tools are made available to the LLM
   - LLM can call tools, which are routed through MCP servers

3. **Cleanup**: After workflow completes
   - All MCP server sessions are closed
   - Server processes are terminated
   - Resources are cleaned up

## Example MCP Server

See `engine/examples/config_mcp_example.yml` for a complete example.

## Creating Custom MCP Servers

### Option 1: Using FastMCP (Recommended)

```python
from fastmcp import FastMCP

server = FastMCP("My Custom Tools")

@server.tool()
def my_custom_function(param: str) -> str:
    """Description of what this tool does"""
    return f"Result: {param}"

if __name__ == "__main__":
    server.run()
```

### Option 2: Using the MCP SDK

See the [MCP documentation](https://github.com/modelcontextprotocol/python-sdk) for details.

## Troubleshooting

### Windows Issues

The custom stdio client uses asyncio instead of anyio to avoid Windows compatibility issues. If you encounter subprocess issues:

1. Ensure Python server paths are correct
2. Check server stderr output in logs
3. Verify environment variables are set correctly

### Tool Not Found

If you get "Tool not found" errors:

1. Check that the MCP server started successfully (look for "✓ server_name: X tools ready")
2. Verify the tool name matches what the server exposes
3. Ensure the agent has the correct MCP tool category in its config

## Advanced Configuration

### Environment Variables

Pass environment variables to MCP servers:

```yaml
mcp_tools:
  api_service:
    server: "python"
    args: ["api_server.py"]
    env:
      API_KEY: "sk-..."
      API_URL: "https://api.example.com"
```

### Multiple Tool Categories

Agents can use multiple MCP tool categories:

```yaml
agents:
  - id: "power_agent"
    role: "Multi-tool Agent"
    mcp_tools:
      - filesystem
      - api_service
      - database
```

## Logging

MCP operations are logged with:

- 🔧 Server initialization messages
- 🔨 Tool execution tracking
- ✓/✗ Success/failure indicators
- Full stderr from MCP servers

Check the workflow logs in `engine/logs/` for detailed information.
