"""
Test GitHub MCP Server
Demonstrates search, list files, and read file operations
"""

import asyncio
import sys
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_github_tools():
    """Test GitHub MCP tools"""
    
    print("=" * 60)
    print("GitHub MCP Server Test")
    print("=" * 60)
    
    # Check for GitHub token
    if not os.environ.get("GITHUB_TOKEN"):
        print("\n⚠️  Warning: GITHUB_TOKEN not set in environment")
        print("Some features may be rate-limited without authentication\n")
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["simple_github_mcp_server.py"],
        env=os.environ.copy()
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Test 1: Search for repositories
            print("\n" + "="*60)
            print("Test 1: Search for repositories")
            print("="*60)
            result = await session.call_tool(
                "search_repositories",
                arguments={
                    "query": "fastapi python",
                    "max_results": 3
                }
            )
            print(result.content[0].text)
            
            # Test 2: List files in a repository
            print("\n" + "="*60)
            print("Test 2: List repository files")
            print("="*60)
            result = await session.call_tool(
                "list_repository_files",
                arguments={
                    "owner": "microsoft",
                    "repo": "vscode",
                    "path": "src"
                }
            )
            print(result.content[0].text)
            
            # Test 3: Read a file
            print("\n" + "="*60)
            print("Test 3: Read file content")
            print("="*60)
            result = await session.call_tool(
                "read_file_content",
                arguments={
                    "owner": "microsoft",
                    "repo": "vscode",
                    "filepath": "README.md"
                }
            )
            # Show first 500 chars of README
            content = result.content[0].text
            if len(content) > 500:
                print(content[:500] + "\n... (truncated)")
            else:
                print(content)
            
            print("\n" + "="*60)
            print("✓ All tests completed!")
            print("="*60)


if __name__ == "__main__":
    asyncio.run(test_github_tools())
