"""
Simple MCP Server - Direct Implementation (No FastMCP)
Provides filesystem and Python execution tools
"""

import sys

# Fix Windows asyncio issues FIRST before any other imports
if sys.platform == 'win32':
    # Force clean import of asyncio by removing any cached modules
    for mod in list(sys.modules.keys()):
        if 'asyncio' in mod or 'selectors' in mod or '_overlapped' in mod:
            del sys.modules[mod]
    
    # Set environment to use selector event loop
    import os
    os.environ['PYTHONASYNCIODEBUG'] = '0'

# Now safe to import asyncio
import asyncio

# Set Windows event loop policy after import
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except:
        pass  # If selector policy doesn't exist, use default

import io
import traceback
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# Workspace directory - use root workspace to avoid disturbing mcp_servers folder
WORKSPACE_DIR = Path(__file__).parent.parent.parent / "workspace"
WORKSPACE_DIR.mkdir(exist_ok=True)


def _validate_path(filepath: str) -> Path:
    """Validate that path is within workspace directory"""
    abs_path = (WORKSPACE_DIR / filepath).resolve()
    if not str(abs_path).startswith(str(WORKSPACE_DIR.resolve())):
        raise ValueError(f"Access denied: path must be within workspace directory")
    return abs_path


# Create MCP server
app = Server("simple-filesystem")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="create_file",
            description="Create a new file with the given content",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file relative to workspace"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["filepath", "content"]
            }
        ),
        types.Tool(
            name="read_file",
            description="Read the contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file relative to workspace"
                    }
                },
                "required": ["filepath"]
            }
        ),
        types.Tool(
            name="list_directory",
            description="List contents of a directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "dirpath": {
                        "type": "string",
                        "description": "Path to directory relative to workspace (default: workspace root)",
                        "default": "."
                    }
                }
            }
        ),
        types.Tool(
            name="execute_python",
            description="Execute Python code and return the output",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute"
                    }
                },
                "required": ["code"]
            }
        ),
        types.Tool(
            name="create_directory",
            description="Create a new directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "dirpath": {
                        "type": "string",
                        "description": "Path to directory relative to workspace"
                    }
                },
                "required": ["dirpath"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""
    
    try:
        if name == "create_file":
            filepath = arguments["filepath"]
            content = arguments["content"]
            abs_path = _validate_path(filepath)
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return [types.TextContent(
                type="text",
                text=f"✓ File created successfully: {filepath}"
            )]
        
        elif name == "read_file":
            filepath = arguments["filepath"]
            abs_path = _validate_path(filepath)
            if not abs_path.exists():
                return [types.TextContent(
                    type="text",
                    text=f"✗ File not found: {filepath}"
                )]
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return [types.TextContent(type="text", text=content)]
        
        elif name == "list_directory":
            dirpath = arguments.get("dirpath", ".")
            abs_path = _validate_path(dirpath)
            if not abs_path.exists():
                return [types.TextContent(
                    type="text",
                    text=f"✗ Directory not found: {dirpath}"
                )]
            if not abs_path.is_dir():
                return [types.TextContent(
                    type="text",
                    text=f"✗ Not a directory: {dirpath}"
                )]
            
            items = []
            for item in abs_path.iterdir():
                item_type = "DIR " if item.is_dir() else "FILE"
                size = f"{item.stat().st_size:>10} bytes" if item.is_file() else ""
                items.append(f"  {item_type} {item.name:30} {size}")
            
            if not items:
                result = f"Directory is empty: {dirpath}"
            else:
                result = f"Contents of {dirpath}:\n" + "\n".join(items)
            
            return [types.TextContent(type="text", text=result)]
        
        elif name == "execute_python":
            code = arguments["code"]
            
            # Capture stdout and stderr
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                try:
                    compiled_code = compile(code, '<string>', 'exec')
                    exec(compiled_code, {})
                except Exception as e:
                    traceback.print_exc()
            
            stdout_value = stdout_capture.getvalue()
            stderr_value = stderr_capture.getvalue()
            
            result = ""
            if stdout_value:
                result += f"[STDOUT]\n{stdout_value}\n"
            if stderr_value:
                result += f"[STDERR]\n{stderr_value}\n"
            if not stdout_value and not stderr_value:
                result = "✓ Code executed successfully (no output)"
            
            return [types.TextContent(type="text", text=result.strip())]
        
        elif name == "create_directory":
            dirpath = arguments["dirpath"]
            abs_path = _validate_path(dirpath)
            abs_path.mkdir(parents=True, exist_ok=True)
            return [types.TextContent(
                type="text",
                text=f"✓ Directory created successfully: {dirpath}"
            )]
        
        else:
            return [types.TextContent(
                type="text",
                text=f"✗ Unknown tool: {name}"
            )]
    
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"✗ Error: {str(e)}"
        )]


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
