"""
Test Calculator MCP Server
Demonstrates all calculator operations
"""

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_calculator():
    """Test calculator MCP tools"""
    
    print("=" * 60)
    print("Calculator MCP Server Test")
    print("=" * 60)
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["simple_calculator_mcp_server.py"],
        env={}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n✓ Calculator server initialized with 8 tools\n")
            
            # Test 1: Basic arithmetic
            print("Test 1: Addition")
            result = await session.call_tool("add", arguments={"a": 15, "b": 27})
            print(f"  {result.content[0].text}")
            
            print("\nTest 2: Subtraction")
            result = await session.call_tool("subtract", arguments={"a": 100, "b": 42})
            print(f"  {result.content[0].text}")
            
            print("\nTest 3: Multiplication")
            result = await session.call_tool("multiply", arguments={"a": 12, "b": 8})
            print(f"  {result.content[0].text}")
            
            print("\nTest 4: Division")
            result = await session.call_tool("divide", arguments={"a": 144, "b": 12})
            print(f"  {result.content[0].text}")
            
            # Test 5: Power
            print("\nTest 5: Power")
            result = await session.call_tool("power", arguments={"base": 2, "exponent": 10})
            print(f"  {result.content[0].text}")
            
            # Test 6: Square root
            print("\nTest 6: Square Root")
            result = await session.call_tool("sqrt", arguments={"n": 144})
            print(f"  {result.content[0].text}")
            
            # Test 7: Percentage
            print("\nTest 7: Percentage")
            result = await session.call_tool("percentage", arguments={"value": 200, "percent": 15})
            print(f"  {result.content[0].text}")
            
            # Test 8: Average
            print("\nTest 8: Average")
            result = await session.call_tool("average", arguments={"numbers": [10, 20, 30, 40, 50]})
            print(f"  {result.content[0].text}")
            
            # Test 9: Error handling - Division by zero
            print("\nTest 9: Error Handling (Division by zero)")
            result = await session.call_tool("divide", arguments={"a": 10, "b": 0})
            print(f"  {result.content[0].text}")
            
            print("\n" + "="*60)
            print("✓ All calculator tests completed!")
            print("="*60)


if __name__ == "__main__":
    asyncio.run(test_calculator())
