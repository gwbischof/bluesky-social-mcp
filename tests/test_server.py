#!/usr/bin/env python
"""Test if the Bluesky MCP server can be imported and run."""

import os
import sys
import inspect

# Add parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print("Script started...")

try:
    print("Importing mcp from server...")
    from server import mcp

    print("Import successful!")

    print("Type of mcp:", type(mcp))
    
    # Check if it's a FastMCP instance
    from mcp.server.fastmcp import FastMCP
    if isinstance(mcp, FastMCP):
        print("✅ mcp is a FastMCP instance")
    else:
        print("❌ mcp is not a FastMCP instance")
    
    # Check some key attributes
    print("\nChecking key properties:")
    print(f"- Server name: {mcp.name}")
    
    # Check if lifespan attribute exists (might be private or differently named)
    has_lifespan = hasattr(mcp, "lifespan") or any(attr.endswith("lifespan") for attr in dir(mcp))
    print(f"- Has lifespan handler: {'✅ Yes' if has_lifespan else '❌ No'}")
    
    # Check available tools
    tool_count = len([name for name in dir(mcp) if name.startswith('_handle_call_tool') or name.startswith('_tool_')])
    resource_count = len([name for name in dir(mcp) if name.startswith('_handle_read_resource') or name.startswith('_resource_')])
    print(f"\nFound approximately {tool_count} tools and {resource_count} resources")
    
    # Check if run method exists
    if hasattr(mcp, "run") and callable(mcp.run):
        print("\n✅ mcp has run method")
        print("The server can be run, but we won't actually start it in this test.")
        print("To run the server, use: uv run python server.py")
    else:
        print("\n❌ Error: mcp doesn't have a run method")
    
    print("\nServer import test completed successfully!")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

print("Script completed successfully")
