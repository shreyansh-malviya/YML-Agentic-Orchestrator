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
import logging
import traceback

logger = logging.getLogger(__name__)


@asynccontextmanager
async def custom_stdio_client(params: StdioServerParameters):
    """
    Custom stdio client context manager for MCP server communication.
    Uses asyncio directly to avoid anyio/Windows compatibility issues.
    
    Args:
        params: Server parameters including command, args, and environment
        
    Yields:
        Tuple of (read_stream, write_stream, process) for session communication and cleanup
    """
    command = params.command
    args = params.args
    env = params.env
    
    # Create memory streams for the session to use
    read_stream_writer, read_stream = anyio.create_memory_object_stream(100)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(100)
    
    # Prepare environment - merge with system env to avoid issues
    import os
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    
    # Add flags to reset asyncio state
    full_env['PYTHONUNBUFFERED'] = '1'
    full_env['PYTHONASYNCIODEBUG'] = '0'
    
    # Use asyncio directly to avoid anyio/Windows issues
    # On Windows, use CREATE_NO_WINDOW to create process with fresh state
    create_kwargs = {
        'stdin': asyncio.subprocess.PIPE,
        'stdout': asyncio.subprocess.PIPE,
        'stderr': asyncio.subprocess.PIPE,
        'env': full_env
    }
    
    # Windows-specific: use creation flags to isolate process
    if sys.platform == 'win32':
        import subprocess
        create_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
    
    process = await asyncio.create_subprocess_exec(
        command, *args,
        **create_kwargs
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
        yield read_stream, write_stream, process  # Return process for tracking
    finally:
        # Cleanup sequence for proper resource management
        
        # Step 1: Cancel background tasks
        for task in tasks:
            if not task.done():
                task.cancel()
        
        # Step 2: Wait for tasks to finish cancelling
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Step 3: Close stdin first to signal process to exit
        try:
            if process.stdin and not process.stdin.is_closing():
                process.stdin.close()
                await asyncio.sleep(0.05)  # Give process time to see stdin close
        except:
            pass
        
        # Step 4: Terminate process gently
        try:
            if process.returncode is None:
                process.terminate()
                # Wait up to 2 seconds for graceful termination
                try:
                    await asyncio.wait_for(process.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    # Force kill if it doesn't terminate gracefully
                    try:
                        process.kill()
                        await process.wait()
                    except:
                        pass
        except:
            pass
        
        # Step 5: Close streams properly
        try:
            await read_stream.aclose()
        except:
            pass
        try:
            await write_stream.aclose()
        except:
            pass
        try:
            await read_stream_writer.aclose()
        except:
            pass
        try:
            await write_stream_reader.aclose()
        except:
            pass


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
        self.processes = {}  # Track subprocess instances for proper cleanup
    
    async def initialize(self):
        """Start all MCP servers and extract tool schemas"""
        if not self.mcp_tools_config:
            return
        
        logger.info("Initializing MCP Tools...")
        for tool_name, config in self.mcp_tools_config.items():
            try:
                await self._start_server(tool_name, config)
            except Exception as e:
                logger.error(f"Failed to initialize {tool_name}: {e}")
                logger.error(traceback.format_exc())
                logger.warning(f"Continuing without this tool...")
    
    async def _start_server(self, tool_name: str, config: Dict[str, Any]):
        """
        Start a single MCP server with proper context management.
        
        Args:
            tool_name: Name identifier for the tool
            config: Server configuration including command, args, and env
        """
        logger.info(f"Starting {tool_name}...")
        
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
        read, write, process = await stdio_context.__aenter__()
        self.transports[tool_name] = stdio_context
        self.processes[tool_name] = process  # Store process for proper cleanup
        
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
        
        logger.info(f"{tool_name}: {len(tools_response.tools)} tools ready")
        for tool in tools_response.tools:
            logger.info(f"  • {tool.name}")

    
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
            logger.error(f"Tool '{function_name}' not found. Available tools: {list(self.tool_schemas.keys())}")
            raise ValueError(f"Tool '{function_name}' not found")
        
        logger.info(f"Executing: {function_name}")
        
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
            
            logger.info(f"Success")
            return result_text
            
        except Exception as e:
            logger.error(f"MCP execution failed: {e}")
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
        """Cleanup all MCP servers with proper resource management"""
        logger.info("Shutting down MCP servers...")
        
        try:
            # Step 1: Close sessions gracefully
            for tool_name, info in list(self.sessions.items()):
                try:
                    session = info.get('session')
                    if session:
                        try:
                            await session.__aexit__(None, None, None)
                        except Exception:
                            pass  # Ignore session cleanup errors
                except Exception as e:
                    if "cancel scope" not in str(e).lower():
                        logger.debug(f"Error closing session {tool_name}: {e}")
            
            # Step 2: Terminate processes before closing transports
            for tool_name, process in list(self.processes.items()):
                try:
                    if process and process.returncode is None:
                        # Close stdin to signal graceful shutdown
                        try:
                            if process.stdin and not process.stdin.is_closing():
                                process.stdin.close()
                        except Exception:
                            pass
                        
                        # Terminate the process
                        try:
                            process.terminate()
                            # Wait briefly for graceful termination
                            await asyncio.wait_for(process.wait(), timeout=1.0)
                        except asyncio.TimeoutError:
                            # Force kill if needed
                            try:
                                process.kill()
                                await asyncio.wait_for(process.wait(), timeout=1.0)
                            except Exception:
                                pass
                        except Exception:
                            pass
                        
                        logger.debug(f"Process {tool_name} terminated")
                except Exception as e:
                    logger.debug(f"Error terminating process {tool_name}: {e}")
            
            # Step 3: Give processes time to fully exit
            try:
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                pass
            
            # Step 4: Close transports (this will cleanup streams)
            for tool_name, stdio_context in list(self.transports.items()):
                try:
                    await stdio_context.__aexit__(None, None, None)
                    print(f"  ✓ {tool_name} closed")
                except Exception as e:
                    if "cancel scope" not in str(e).lower() and "closed pipe" not in str(e).lower():
                        logger.debug(f"Error closing transport {tool_name}: {e}")
            
            # Step 5: Clear all references
            self.sessions.clear()
            self.transports.clear()
            self.tool_schemas.clear()
            self.processes.clear()
            
            # Step 6: Final cleanup delay
            try:
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                pass
                
        except asyncio.CancelledError:
            # If shutdown itself is cancelled, ensure cleanup still happens
            logger.warning("Shutdown cancelled, forcing cleanup...")
            self.sessions.clear()
            self.transports.clear()
            self.tool_schemas.clear()
            self.processes.clear()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            # Ensure cleanup happens even on error
            self.sessions.clear()
            self.transports.clear()
            self.tool_schemas.clear()
            self.processes.clear()
