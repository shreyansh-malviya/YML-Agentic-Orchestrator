"""
Example MCP Filesystem Server using FastMCP
Provides file and directory operations for AI agents
"""

from fastmcp import FastMCP
from pathlib import Path
import os

# Create FastMCP server instance
server = FastMCP("Filesystem Tools")

# Define workspace directory
WORKSPACE_DIR = Path(__file__).parent / "workspace"
WORKSPACE_DIR.mkdir(exist_ok=True)


def _validate_path(filepath: str) -> Path:
    """Validate that path is within workspace directory"""
    abs_path = (WORKSPACE_DIR / filepath).resolve()
    
    if not str(abs_path).startswith(str(WORKSPACE_DIR.resolve())):
        raise ValueError(f"Access denied: path must be within workspace directory")
    
    return abs_path


@server.tool()
def create_file(filepath: str, content: str) -> str:
    """
    Create a new file with the given content
    
    Args:
        filepath: Path to the file relative to workspace
        content: Content to write to the file
    
    Returns:
        Success message with file path
    """
    try:
        abs_path = _validate_path(filepath)
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"✓ File created successfully: {filepath}"
    except Exception as e:
        return f"✗ Error creating file: {str(e)}"


@server.tool()
def read_file(filepath: str) -> str:
    """
    Read the contents of a file
    
    Args:
        filepath: Path to the file relative to workspace
    
    Returns:
        File contents or error message
    """
    try:
        abs_path = _validate_path(filepath)
        
        if not abs_path.exists():
            return f"✗ File not found: {filepath}"
        
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    except Exception as e:
        return f"✗ Error reading file: {str(e)}"


@server.tool()
def list_directory(dirpath: str = ".") -> str:
    """
    List contents of a directory
    
    Args:
        dirpath: Path to directory relative to workspace (default: workspace root)
    
    Returns:
        List of files and directories
    """
    try:
        abs_path = _validate_path(dirpath)
        
        if not abs_path.exists():
            return f"✗ Directory not found: {dirpath}"
        
        if not abs_path.is_dir():
            return f"✗ Not a directory: {dirpath}"
        
        items = []
        for item in abs_path.iterdir():
            item_type = "DIR " if item.is_dir() else "FILE"
            size = f"{item.stat().st_size:>10} bytes" if item.is_file() else ""
            items.append(f"  {item_type} {item.name:30} {size}")
        
        if not items:
            return f"Directory is empty: {dirpath}"
        
        return f"Contents of {dirpath}:\n" + "\n".join(items)
    except Exception as e:
        return f"✗ Error listing directory: {str(e)}"


@server.tool()
def create_directory(dirpath: str) -> str:
    """
    Create a new directory
    
    Args:
        dirpath: Path to directory relative to workspace
    
    Returns:
        Success message
    """
    try:
        abs_path = _validate_path(dirpath)
        abs_path.mkdir(parents=True, exist_ok=True)
        
        return f"✓ Directory created successfully: {dirpath}"
    except Exception as e:
        return f"✗ Error creating directory: {str(e)}"


@server.tool()
def delete_file(filepath: str) -> str:
    """
    Delete a file
    
    Args:
        filepath: Path to file relative to workspace
    
    Returns:
        Success message
    """
    try:
        abs_path = _validate_path(filepath)
        
        if not abs_path.exists():
            return f"✗ File not found: {filepath}"
        
        if abs_path.is_dir():
            return f"✗ Cannot delete directory with delete_file: {filepath}"
        
        abs_path.unlink()
        return f"✓ File deleted successfully: {filepath}"
    except Exception as e:
        return f"✗ Error deleting file: {str(e)}"


if __name__ == "__main__":
    # Run the MCP server
    server.run()
