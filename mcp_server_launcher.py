"""
MCP Server Launcher Wrapper
Spawns a fresh Python process to avoid Windows asyncio inheritance issues
"""

import sys
import subprocess

if __name__ == "__main__":
    # Launch server in a completely fresh Python process
    # This avoids inheriting the parent's asyncio state
    result = subprocess.run(
        [sys.executable, "-u", "simple_mcp_server.py"],
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )
    sys.exit(result.returncode)
