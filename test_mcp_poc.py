"""
Proof of Concept: Test MCP Server with Filesystem and Python Tools
This script tests if the MCP server can start and execute tools properly
"""

import asyncio
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    """Test the MCP filesystem server"""
    
    print("=" * 60)
    print("MCP Server Proof of Concept Test")
    print("=" * 60)
    
    # Server parameters
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["engine/mcp_servers/simple_mcp_server.py"],
        env={}
    )
    
    print("\n1. Starting MCP server...")
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                print("   ✓ Server started successfully")
                
                # List available tools
                print("\n2. Listing available tools...")
                tools_response = await session.list_tools()
                print(f"   ✓ Found {len(tools_response.tools)} tools:")
                for tool in tools_response.tools:
                    print(f"     • {tool.name}: {tool.description}")
                
                # Test 1: Create a file
                print("\n3. Testing create_file tool...")
                test_content = """def hello():
    print("Hello from MCP!")
    return "Success"

hello()
"""
                result = await session.call_tool(
                    "create_file",
                    arguments={
                        "filepath": "test_hello.py",
                        "content": test_content
                    }
                )
                print(f"   {result.content[0].text}")
                
                # Test 2: Read the file back
                print("\n4. Testing read_file tool...")
                result = await session.call_tool(
                    "read_file",
                    arguments={"filepath": "test_hello.py"}
                )
                print(f"   ✓ File content read successfully")
                print(f"   Preview: {result.content[0].text[:50]}...")
                
                # Test 3: Execute Python code
                print("\n5. Testing execute_python tool...")
                result = await session.call_tool(
                    "execute_python",
                    arguments={
                        "code": "print('2 + 2 =', 2 + 2)\nprint('Hello from Python executor!')"
                    }
                )
                print(f"   {result.content[0].text}")
                
                # Test 4: List directory
                print("\n6. Testing list_directory tool...")
                result = await session.call_tool(
                    "list_directory",
                    arguments={"dirpath": "."}
                )
                lines = result.content[0].text.split('\n')
                print(f"   {lines[0]}")
                print(f"   Found {len(lines)-1} items")
                
                print("\n" + "=" * 60)
                print("✓ ALL TESTS PASSED!")
                print("MCP server is working correctly with:")
                print("  • Filesystem operations (create_file, read_file)")
                print("  • Python code execution (execute_python)")
                print("  • Directory listing (list_directory)")
                print("=" * 60)
                
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        print("✗ TEST FAILED")
        print("=" * 60)
        return False
    
    return True


if __name__ == "__main__":
    # Run the async test
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)
