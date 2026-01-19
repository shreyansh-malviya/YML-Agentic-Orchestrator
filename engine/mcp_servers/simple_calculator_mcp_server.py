"""
Simple Calculator MCP Server
Provides mathematical calculation tools via MCP protocol
"""

import sys
import os

# Fix Windows asyncio issues FIRST
if sys.platform == 'win32':
    for mod in list(sys.modules.keys()):
        if 'asyncio' in mod or 'selectors' in mod or '_overlapped' in mod:
            del sys.modules[mod]
    os.environ['PYTHONASYNCIODEBUG'] = '0'

import asyncio

if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except:
        pass

import math
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# Create MCP server
app = Server("calculator-tools")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available calculator tools"""
    return [
        types.Tool(
            name="add",
            description="Add two numbers",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    }
                },
                "required": ["a", "b"]
            }
        ),
        types.Tool(
            name="subtract",
            description="Subtract second number from first number",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    }
                },
                "required": ["a", "b"]
            }
        ),
        types.Tool(
            name="multiply",
            description="Multiply two numbers",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    }
                },
                "required": ["a", "b"]
            }
        ),
        types.Tool(
            name="divide",
            description="Divide first number by second number",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "Dividend (number to be divided)"
                    },
                    "b": {
                        "type": "number",
                        "description": "Divisor (number to divide by)"
                    }
                },
                "required": ["a", "b"]
            }
        ),
        types.Tool(
            name="power",
            description="Raise first number to the power of second number",
            inputSchema={
                "type": "object",
                "properties": {
                    "base": {
                        "type": "number",
                        "description": "Base number"
                    },
                    "exponent": {
                        "type": "number",
                        "description": "Exponent"
                    }
                },
                "required": ["base", "exponent"]
            }
        ),
        types.Tool(
            name="sqrt",
            description="Calculate square root of a number",
            inputSchema={
                "type": "object",
                "properties": {
                    "n": {
                        "type": "number",
                        "description": "Number to find square root of (must be non-negative)"
                    }
                },
                "required": ["n"]
            }
        ),
        types.Tool(
            name="percentage",
            description="Calculate percentage of a number",
            inputSchema={
                "type": "object",
                "properties": {
                    "value": {
                        "type": "number",
                        "description": "The value to calculate percentage of"
                    },
                    "percent": {
                        "type": "number",
                        "description": "Percentage (e.g., 25 for 25%)"
                    }
                },
                "required": ["value", "percent"]
            }
        ),
        types.Tool(
            name="average",
            description="Calculate average of multiple numbers",
            inputSchema={
                "type": "object",
                "properties": {
                    "numbers": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "List of numbers to average"
                    }
                },
                "required": ["numbers"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Execute calculator tool calls"""
    try:
        if name == "add":
            result = arguments["a"] + arguments["b"]
            return [types.TextContent(
                type="text",
                text=f"{arguments['a']} + {arguments['b']} = {result}"
            )]
        
        elif name == "subtract":
            result = arguments["a"] - arguments["b"]
            return [types.TextContent(
                type="text",
                text=f"{arguments['a']} - {arguments['b']} = {result}"
            )]
        
        elif name == "multiply":
            result = arguments["a"] * arguments["b"]
            return [types.TextContent(
                type="text",
                text=f"{arguments['a']} × {arguments['b']} = {result}"
            )]
        
        elif name == "divide":
            if arguments["b"] == 0:
                return [types.TextContent(
                    type="text",
                    text="✗ Error: Division by zero"
                )]
            result = arguments["a"] / arguments["b"]
            return [types.TextContent(
                type="text",
                text=f"{arguments['a']} ÷ {arguments['b']} = {result}"
            )]
        
        elif name == "power":
            result = arguments["base"] ** arguments["exponent"]
            return [types.TextContent(
                type="text",
                text=f"{arguments['base']}^{arguments['exponent']} = {result}"
            )]
        
        elif name == "sqrt":
            if arguments["n"] < 0:
                return [types.TextContent(
                    type="text",
                    text="✗ Error: Cannot calculate square root of negative number"
                )]
            result = math.sqrt(arguments["n"])
            return [types.TextContent(
                type="text",
                text=f"√{arguments['n']} = {result}"
            )]
        
        elif name == "percentage":
            result = (arguments["value"] * arguments["percent"]) / 100
            return [types.TextContent(
                type="text",
                text=f"{arguments['percent']}% of {arguments['value']} = {result}"
            )]
        
        elif name == "average":
            numbers = arguments["numbers"]
            if not numbers:
                return [types.TextContent(
                    type="text",
                    text="✗ Error: Cannot calculate average of empty list"
                )]
            result = sum(numbers) / len(numbers)
            return [types.TextContent(
                type="text",
                text=f"Average of {numbers} = {result}"
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
