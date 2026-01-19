"""
Quick test to verify GitHub tools including create_issue
"""

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def check_tools():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["engine/mcp_servers/simple_github_mcp_server.py"],
        env={}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            print(f"\n✓ GitHub MCP Server has {len(tools.tools)} tools:\n")
            for tool in tools.tools:
                print(f"  📌 {tool.name} - {tool.description}")

asyncio.run(check_tools())
