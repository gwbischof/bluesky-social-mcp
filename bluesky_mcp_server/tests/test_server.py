#!/usr/bin/env python
"""Test if the Bluesky MCP server can be imported and run."""

print("Script started...")

try:
    print("Importing mcp from server...")
    from bluesky_mcp_server.server import mcp

    print("Import successful!")

    print("Type of mcp:", type(mcp))
    print("mcp attributes:", dir(mcp))

    # Check if run method exists
    if hasattr(mcp, "run"):
        print("mcp has run method")
        print("Starting server (this might not output anything if it's running)...")
        mcp.run()
        print(
            "Server completed (this might not be printed if server runs in background)"
        )
    else:
        print("Error: mcp doesn't have a run method")

except Exception as e:
    print(f"Error: {e}")

print("Script completed (if this is reached, the server likely ran and exited)")
