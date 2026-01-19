# MCP Servers

This directory contains all Model Context Protocol (MCP) server implementations for the YML-Agentic-Orchestrator.

## Available Servers

### 1. **simple_mcp_server.py**
Provides filesystem and Python execution tools:
- `create_file` - Create files in workspace
- `read_file` - Read file contents
- `list_directory` - List directory contents
- `create_directory` - Create directories
- `delete_file` - Delete files
- `execute_python` - Execute Python code safely

### 2. **mcp_filesystem_server.py**
FastMCP-based filesystem server with similar functionality to simple_mcp_server.py

### 3. **simple_calculator_mcp_server.py**
Mathematical calculation tools:
- `add`, `subtract`, `multiply`, `divide` - Basic arithmetic
- `power`, `sqrt`, `factorial` - Advanced operations
- `sin`, `cos`, `tan` - Trigonometric functions
- `evaluate` - Evaluate mathematical expressions

### 4. **simple_github_mcp_server.py**
GitHub repository management tools:
- `get_repository` - Get repository information
- `list_issues` - List repository issues
- `create_issue` - Create new issues
- `search_repositories` - Search GitHub repositories
- And more...

### 5. **mcp_server_launcher.py**
Launcher wrapper to spawn MCP servers in fresh processes (Windows compatibility helper)

## Usage in YAML Configs

Reference these servers in your workflow YAML files:

```yaml
tools:
  filesystem:
    server: "python"
    args: ["engine/mcp_servers/simple_mcp_server.py"]
  
  calculator:
    server: "python"
    args: ["engine/mcp_servers/simple_calculator_mcp_server.py"]
  
  github:
    server: "python"
    args: ["engine/mcp_servers/simple_github_mcp_server.py"]
    env:
      GITHUB_TOKEN: "your-token-here"
```

## Creating Custom Servers

To create a new MCP server:

1. Create a new Python file in this directory
2. Implement using either:
   - `mcp.server.Server` (direct implementation)
   - `FastMCP` (simplified API)
3. Define tools using decorators
4. Add to YAML config

See existing servers for examples.
