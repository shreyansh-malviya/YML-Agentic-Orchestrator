from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("filesystem")

# Root directory sandbox
PROJECT_ROOT = Path.cwd() / "workspace"
PROJECT_ROOT.mkdir(exist_ok=True)


def resolve_path(path: str) -> Path:
    full = (PROJECT_ROOT / path).resolve()
    if not str(full).startswith(str(PROJECT_ROOT.resolve())):
        raise ValueError("Access outside project directory is not allowed")
    return full


@mcp.tool()
def read_file(path: str) -> str:
    """Read a file from the project workspace."""
    file_path = resolve_path(path)
    return file_path.read_text()


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write content to a file in the project workspace."""
    file_path = resolve_path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    return "File written successfully"


@mcp.tool()
def move_file(src: str, dest: str) -> str:
    """Move or rename a file within the workspace."""
    src_path = resolve_path(src)
    dest_path = resolve_path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    src_path.rename(dest_path)
    return "File moved successfully"


@mcp.tool()
def list_directory(path: str = ".") -> list[str]:
    """List files in a directory."""
    dir_path = resolve_path(path)
    return [p.name for p in dir_path.iterdir()]


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()