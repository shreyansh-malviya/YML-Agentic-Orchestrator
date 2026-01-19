"""
Simple GitHub MCP Server
Provides GitHub repository tools via MCP protocol
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

import requests
from typing import Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

if not GITHUB_TOKEN:
    print("Warning: GITHUB_TOKEN not found in environment. Some operations may be limited.", file=sys.stderr)


def _get_headers() -> dict:
    """Get headers for GitHub API requests"""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "YML-Agentic-Orchestrator-MCP"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


# Create MCP server
app = Server("github-tools")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available GitHub tools"""
    return [
        types.Tool(
            name="search_repositories",
            description="Search for GitHub repositories by query string",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'machine learning', 'user:username', 'org:organization')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="list_repository_files",
            description="List all files in a GitHub repository at a specific path",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner (username or organization)"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "path": {
                        "type": "string",
                        "description": "Path in repository (default: root '/')",
                        "default": ""
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch name (default: repository's default branch)",
                        "default": ""
                    }
                },
                "required": ["owner", "repo"]
            }
        ),
        types.Tool(
            name="read_file_content",
            description="Read the contents of a file from a GitHub repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner (username or organization)"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file in the repository"
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch name (default: repository's default branch)",
                        "default": ""
                    }
                },
                "required": ["owner", "repo", "filepath"]
            }
        ),
        types.Tool(
            name="create_issue",
            description="Create a new issue in a GitHub repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner (username or organization)"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "title": {
                        "type": "string",
                        "description": "Issue title"
                    },
                    "body": {
                        "type": "string",
                        "description": "Issue description/body",
                        "default": ""
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels to apply to the issue",
                        "default": []
                    }
                },
                "required": ["owner", "repo", "title"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Execute GitHub tool calls"""
    try:
        if name == "search_repositories":
            return await search_repositories(
                query=arguments["query"],
                max_results=arguments.get("max_results", 10)
            )
        
        elif name == "list_repository_files":
            return await list_repository_files(
                owner=arguments["owner"],
                repo=arguments["repo"],
                path=arguments.get("path", ""),
                branch=arguments.get("branch", "")
            )
        
        elif name == "read_file_content":
            return await read_file_content(
                owner=arguments["owner"],
                repo=arguments["repo"],
                filepath=arguments["filepath"],
                branch=arguments.get("branch", "")
            )
        
        elif name == "create_issue":
            return await create_issue(
                owner=arguments["owner"],
                repo=arguments["repo"],
                title=arguments["title"],
                body=arguments.get("body", ""),
                labels=arguments.get("labels", [])
            )
        
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


async def search_repositories(query: str, max_results: int = 10) -> list[types.TextContent]:
    """Search for GitHub repositories"""
    try:
        url = f"{GITHUB_API_BASE}/search/repositories"
        params = {
            "q": query,
            "per_page": min(max_results, 100),
            "sort": "stars",
            "order": "desc"
        }
        
        response = requests.get(url, headers=_get_headers(), params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        repos = data.get("items", [])
        
        if not repos:
            return [types.TextContent(
                type="text",
                text=f"No repositories found for query: {query}"
            )]
        
        result_lines = [f"Found {data.get('total_count', 0)} repositories (showing top {len(repos)}):\n"]
        
        for repo in repos[:max_results]:
            result_lines.append(
                f"📦 {repo['full_name']}\n"
                f"   ⭐ {repo['stargazers_count']} stars | "
                f"🍴 {repo['forks_count']} forks\n"
                f"   📝 {repo.get('description', 'No description')}\n"
                f"   🔗 {repo['html_url']}\n"
            )
        
        return [types.TextContent(
            type="text",
            text="\n".join(result_lines)
        )]
    
    except requests.exceptions.RequestException as e:
        return [types.TextContent(
            type="text",
            text=f"✗ GitHub API error: {str(e)}"
        )]


async def list_repository_files(owner: str, repo: str, path: str = "", branch: str = "") -> list[types.TextContent]:
    """List files in a GitHub repository"""
    try:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
        params = {}
        if branch:
            params["ref"] = branch
        
        response = requests.get(url, headers=_get_headers(), params=params, timeout=10)
        response.raise_for_status()
        
        contents = response.json()
        
        # Handle single file response
        if isinstance(contents, dict):
            return [types.TextContent(
                type="text",
                text=f"'{path}' is a file, not a directory"
            )]
        
        if not contents:
            return [types.TextContent(
                type="text",
                text=f"No files found in {owner}/{repo}/{path}"
            )]
        
        result_lines = [f"📁 {owner}/{repo}/{path or '(root)'}\n"]
        
        # Separate directories and files
        dirs = [item for item in contents if item['type'] == 'dir']
        files = [item for item in contents if item['type'] == 'file']
        
        # List directories first
        for item in sorted(dirs, key=lambda x: x['name']):
            result_lines.append(f"📂 {item['name']}/")
        
        # Then list files
        for item in sorted(files, key=lambda x: x['name']):
            size_kb = item.get('size', 0) / 1024
            result_lines.append(f"📄 {item['name']} ({size_kb:.1f} KB)")
        
        result_lines.append(f"\nTotal: {len(dirs)} directories, {len(files)} files")
        
        return [types.TextContent(
            type="text",
            text="\n".join(result_lines)
        )]
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return [types.TextContent(
                type="text",
                text=f"✗ Repository or path not found: {owner}/{repo}/{path}"
            )]
        raise
    except requests.exceptions.RequestException as e:
        return [types.TextContent(
            type="text",
            text=f"✗ GitHub API error: {str(e)}"
        )]


async def read_file_content(owner: str, repo: str, filepath: str, branch: str = "") -> list[types.TextContent]:
    """Read file content from a GitHub repository"""
    try:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{filepath}"
        params = {}
        if branch:
            params["ref"] = branch
        
        response = requests.get(url, headers=_get_headers(), params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Check if it's a file
        if data.get('type') != 'file':
            return [types.TextContent(
                type="text",
                text=f"✗ '{filepath}' is not a file"
            )]
        
        # Decode content (GitHub returns base64 encoded content)
        import base64
        content = base64.b64decode(data['content']).decode('utf-8')
        
        result = (
            f"📄 {owner}/{repo}/{filepath}\n"
            f"Size: {data.get('size', 0)} bytes\n"
            f"{'='*60}\n"
            f"{content}\n"
            f"{'='*60}"
        )
        
        return [types.TextContent(
            type="text",
            text=result
        )]
    
    except UnicodeDecodeError:
        return [types.TextContent(
            type="text",
            text=f"✗ File is binary or cannot be decoded as UTF-8"
        )]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return [types.TextContent(
                type="text",
                text=f"✗ File not found: {owner}/{repo}/{filepath}"
            )]
        raise
    except requests.exceptions.RequestException as e:
        return [types.TextContent(
            type="text",
            text=f"✗ GitHub API error: {str(e)}"
        )]


async def create_issue(owner: str, repo: str, title: str, body: str = "", labels: list = None) -> list[types.TextContent]:
    """Create a new issue in a GitHub repository"""
    try:
        if not GITHUB_TOKEN:
            return [types.TextContent(
                type="text",
                text="✗ Authentication required: GITHUB_TOKEN environment variable not set. Cannot create issues without authentication."
            )]
        
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues"
        
        payload = {
            "title": title,
            "body": body
        }
        
        if labels:
            payload["labels"] = labels
        
        response = requests.post(url, headers=_get_headers(), json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        result = (
            f"✓ Issue created successfully!\n"
            f"📋 #{data['number']}: {data['title']}\n"
            f"👤 Created by: {data['user']['login']}\n"
            f"🔗 URL: {data['html_url']}\n"
        )
        
        if labels:
            result += f"🏷️  Labels: {', '.join(labels)}\n"
        
        return [types.TextContent(
            type="text",
            text=result
        )]
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return [types.TextContent(
                type="text",
                text=f"✗ Repository not found: {owner}/{repo}"
            )]
        elif e.response.status_code == 401:
            return [types.TextContent(
                type="text",
                text="✗ Authentication failed. Check your GITHUB_TOKEN."
            )]
        elif e.response.status_code == 403:
            return [types.TextContent(
                type="text",
                text="✗ Forbidden. You may not have permission to create issues in this repository."
            )]
        raise
    except requests.exceptions.RequestException as e:
        return [types.TextContent(
            type="text",
            text=f"✗ GitHub API error: {str(e)}"
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
