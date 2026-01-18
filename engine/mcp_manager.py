"""
MCP Server Manager
Manages Model Context Protocol (MCP) servers for tool execution
"""

import asyncio
import json
import os
import sys
import anyio
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
import mcp.types as types
from mcp.shared.message import SessionMessage
import traceback


@asynccontextmanager
async def custom_stdio_client(params: StdioServerParameters):
    """
    Custom stdio client context manager for MCP server communication.
    Uses asyncio directly to avoid anyio/Windows compatibility issues.
    
    Args:
        params: Server parameters including command, args, and environment
        
    Yields:
        Tuple of (read_stream, write_stream) for session communication
    """
    command = params.command
    args = params.args
    env = params.env
    
    # Create memory streams for the session to use
    read_stream_writer, read_stream = anyio.create_memory_object_stream(100)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(100)
    
    # Use asyncio directly to avoid anyio/Windows issues
    process = await asyncio.create_subprocess_exec(
        command, *args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )
    
    async def stdout_reader():
        """Read and parse JSON-RPC messages from server stdout"""
        try:
            async with read_stream_writer:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    
                    try:
                        line_str = line.decode('utf-8').strip()
                        if not line_str:
                            continue
                            
                        # Parse JSON-RPC message
                        message = types.JSONRPCMessage.model_validate_json(line_str)
                        session_message = SessionMessage(message)
                        await read_stream_writer.send(session_message)
                    except Exception as exc:
                        print(f"Failed to parse JSONRPC message: {exc}")
                        continue
        except Exception as e:
            print(f"stdout_reader error: {e}")

    async def stdin_writer():
        """Write session messages to server stdin"""
        try:
            async with write_stream_reader:
                async for session_message in write_stream_reader:
                    # Serialize message
                    json_str = session_message.message.model_dump_json(by_alias=True, exclude_none=True)
                    data = (json_str + "\n").encode('utf-8')
                    process.stdin.write(data)
                    await process.stdin.drain()
        except Exception as e:
            print(f"stdin_writer error: {e}")

    async def stderr_reader():
        """Monitor server stderr for debugging"""
        while True:
            line = await process.stderr.readline()
            if not line: 
                break
            print(f"  [MCP STDERR] {line.decode().strip()}")

    # Start background tasks
    tasks = [
        asyncio.create_task(stdout_reader()),
        asyncio.create_task(stdin_writer()),
        asyncio.create_task(stderr_reader())
    ]
    
    try:
        yield read_stream, write_stream
    finally:
        # Cleanup
        for task in tasks:
            task.cancel()
            
        try:
            process.terminate()
            await process.wait()
        except:
            pass
        
        # Close streams
        await read_stream.aclose()
        await write_stream.aclose()
        await read_stream_writer.aclose()
        await write_stream_reader.aclose()


class MCPManager:
    """
    Manager for multiple MCP servers and their tools.
    Handles server initialization, tool schema extraction, and tool execution.
    """
    
    def __init__(self, mcp_tools_config: Dict[str, Any]):
        """
        Initialize MCP Manager with configuration.
        
        Args:
            mcp_tools_config: Dictionary mapping tool names to their server configurations
        """
        self.mcp_tools_config = mcp_tools_config
        self.sessions = {}
        self.tool_schemas = {}
        self.transports = {}
    
    async def initialize(self):
        """Start all MCP servers and extract tool schemas"""
        if not self.mcp_tools_config:
            return
        
        print("\n🔧 Initializing MCP Tools...")
        for tool_name, config in self.mcp_tools_config.items():
            try:
                await self._start_server(tool_name, config)
            except Exception as e:
                print(f"  ⚠️  Failed to initialize {tool_name}: {e}")
                traceback.print_exc()
                print(f"     Continuing without this tool...")
    
    async def _start_server(self, tool_name: str, config: Dict[str, Any]):
        """
        Start a single MCP server with proper context management.
        
        Args:
            tool_name: Name identifier for the tool
            config: Server configuration including command, args, and env
        """
        print(f"  Starting {tool_name}...")
        
        cmd = config['server']
        if cmd == "python":
            cmd = sys.executable

        # Build server parameters
        server_params = StdioServerParameters(
            command=cmd,
            args=config.get('args', []),
            env=config.get('env', {})
        )
        
        # Create and enter the context manager manually
        # Use our custom client instead of library one
        stdio_context = custom_stdio_client(server_params)
        read, write = await stdio_context.__aenter__()
        self.transports[tool_name] = stdio_context
        
        # Create session using the transport
        session = ClientSession(read, write)
        await session.__aenter__()
        await session.initialize()
        
        # List available tools
        tools_response = await session.list_tools()
        
        self.sessions[tool_name] = {'session': session}
        
        # Convert MCP tools to schemas
        for tool in tools_response.tools:
            schema = self._mcp_tool_to_schema(tool)
            self.tool_schemas[tool.name] = {
                'schema': schema,
                'category': tool_name
            }
        
        print(f"  ✓ {tool_name}: {len(tools_response.tools)} tools ready")
        for tool in tools_response.tools:
            print(f"    • {tool.name}")
    
    def get_tool_schemas_for_agent(self, tool_categories: List[str]) -> List[Dict[str, Any]]:
        """
        Get tool schemas for specific categories.
        
        Args:
            tool_categories: List of tool category names
            
        Returns:
            List of tool schemas for the requested categories
        """
        schemas = []
        for category in tool_categories:
            if category in self.sessions:
                # Find all tools belonging to this category
                for tool_name, info in self.tool_schemas.items():
                    if info['category'] == category:
                        schemas.append(info['schema'])
        return schemas
    
    async def execute_tool(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool call via MCP.
        
        Args:
            function_name: Name of the tool to execute
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool execution result as string
            
        Raises:
            ValueError: If tool is not found
        """
        # Find which server has this tool
        tool_info = self.tool_schemas.get(function_name)
        if not tool_info:
            tool_info = self._fuzzy_find_tool(function_name)
            
        if not tool_info:
            raise ValueError(f"Tool '{function_name}' not found")
        
        print(f"  🔨 Executing: {function_name}")
        
        try:
            category = tool_info['category']
            session = self.sessions[category]['session']
            
            # Execute the tool
            result = await session.call_tool(function_name, arguments)
            
            # Extract text from result
            result_text = ""
            if result.content:
                for content_item in result.content:
                    if hasattr(content_item, 'text'):
                        result_text += content_item.text
            
            print(f"  ✓ Success")
            return result_text
            
        except Exception as e:
            print(f"  ✗ MCP execution failed: {e}")
            raise

    def _mcp_tool_to_schema(self, mcp_tool) -> Dict[str, Any]:
        """
        Convert MCP tool definition to AI model tool schema.
        
        Args:
            mcp_tool: MCP tool object
            
        Returns:
            Tool schema dictionary compatible with AI models
        """
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        if hasattr(mcp_tool, 'inputSchema') and mcp_tool.inputSchema:
            schema = mcp_tool.inputSchema
            if isinstance(schema, dict):
                parameters = schema
        
        return {
            "name": mcp_tool.name,
            "description": mcp_tool.description or f"Execute {mcp_tool.name}",
            "parameters": parameters
        }

    def _fuzzy_find_tool(self, function_name: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to find a tool using fuzzy matching.
        
        Args:
            function_name: Name to search for
            
        Returns:
            Tool info if found, None otherwise
        """
        # Check all registered tools
        for name, info in self.tool_schemas.items():
            if function_name.lower() in name.lower():
                return info
        return None

    async def shutdown(self):
        """Cleanup all MCP servers"""
        print("\n🔧 Shutting down MCP servers...")
        
        # Close sessions first
        for tool_name, info in self.sessions.items():
            try:
                await info['session'].__aexit__(None, None, None)
            except Exception as e:
                print(f"  ⚠️  Error closing session {tool_name}: {e}")

        # Then close transports
        for tool_name, stdio_context in self.transports.items():
            try:
                await stdio_context.__aexit__(None, None, None)
                print(f"  ✓ {tool_name} closed")
            except Exception as e:
                print(f"  ⚠️  Error closing {tool_name}: {e}")
