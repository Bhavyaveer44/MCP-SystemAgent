from mcp.server.fastmcp import FastMCP

from tools import file_ops, shell_ops

mcp = FastMCP("system-automation-agent")


@mcp.tool()
def read_file(relative_path: str) -> str:
    """Read the contents of a file inside the workspace."""
    try:
        return file_ops.read_file(relative_path)
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


@mcp.tool()
def write_file(relative_path: str, content: str) -> str:
    """Write (or overwrite) a file inside the workspace with the given content."""
    try:
        return file_ops.write_file(relative_path, content)
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


@mcp.tool()
def list_dir(relative_path: str = ".") -> str:
    """List files and folders inside a directory in the workspace."""
    try:
        return str(file_ops.list_dir(relative_path))
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


@mcp.tool()
def delete_file(relative_path: str) -> str:
    """Delete a file inside the workspace. Irreversible — use carefully."""
    try:
        return file_ops.delete_file(relative_path)
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


@mcp.tool()
def run_command(raw_command: str) -> str:
    """
    Run a shell command inside the workspace. Only commands on the
    allowlist are permitted; some require local user confirmation.
    Example: 'git status', 'ls -la', 'pytest'.
    """
    try:
        return shell_ops.run_command(raw_command)
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


if __name__ == "__main__":
    mcp.run()