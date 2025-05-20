#!/usr/bin/env python
"""Run the Bluesky MCP server with debugging."""

import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Import server with relative imports
from bluesky_mcp_server.server import mcp

if __name__ == "__main__":
    print("Starting Bluesky MCP server...")
    try:
        print("Running MCP server with default parameters...")
        mcp.run()
    except Exception as e:
        print(f"Error starting server: {e}")