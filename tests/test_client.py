#!/usr/bin/env python
"""Test client for the Bluesky MCP server."""

import os
import sys
import asyncio
import importlib.util

# Add parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Check if the MCP client library is installed
if importlib.util.find_spec("mcp") is None:
    print("Error: MCP client library not installed")
    print("Run 'uv add mcp[cli]' to install it")
    sys.exit(1)

try:
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from mcp.client.session import ClientSession
except ImportError as e:
    print(f"Error importing MCP client: {e}")
    sys.exit(1)

print("Setting up test client for Bluesky MCP server...")

async def test_mcp_client():
    """Test the MCP client connection to the server."""
    # Make sure we use the right path for the server script
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    server_path = os.path.join(script_dir, "server.py")
    
    print(f"Server script path: {server_path}")
    
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", server_path],
        env={"PYTHONUNBUFFERED": "1"},  # Ensure unbuffered output
    )
    
    try:
        print("Connecting to MCP server via stdio...")
        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            try:
                async with ClientSession(read, write) as session:
                    print("Session created, initializing...")
                    # Initialize the session
                    await session.initialize()
                    print("Session initialized successfully")
                    
                    # Just return success without trying to list tools for now
                    print("Test completed successfully!")
                    return True
            except Exception as session_error:
                print(f"Session error: {session_error}")
                import traceback
                traceback.print_exc()
                return False
    except Exception as e:
        print(f"Error testing MCP client: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_client())
    sys.exit(0 if success else 1)
