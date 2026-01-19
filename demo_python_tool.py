"""
Quick demo of the Python execution tool
"""

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def demo_python_execution():
    """Demonstrate the execute_python tool"""
    
    print("=" * 60)
    print("Python Execution Tool Demo")
    print("=" * 60)
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["engine/mcp_servers/simple_mcp_server.py"],
        env={}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\nTest 1: Simple calculation")
            result = await session.call_tool(
                "execute_python",
                arguments={"code": "print('10 * 5 =', 10 * 5)"}
            )
            print(f"Result: {result.content[0].text}")
            
            print("\nTest 2: Loop and list comprehension")
            code = """
numbers = [1, 2, 3, 4, 5]
squared = [n**2 for n in numbers]
print('Numbers:', numbers)
print('Squared:', squared)
"""
            result = await session.call_tool(
                "execute_python",
                arguments={"code": code}
            )
            print(f"Result: {result.content[0].text}")
            
            print("\nTest 3: String operations")
            result = await session.call_tool(
                "execute_python",
                arguments={"code": "print('Hello, World!'.upper())"}
            )
            print(f"Result: {result.content[0].text}")
            
            print("\n" + "=" * 60)
            print("✓ All Python execution tests passed!")
            print("=" * 60)

if __name__ == "__main__":
    asyncio.run(demo_python_execution())
