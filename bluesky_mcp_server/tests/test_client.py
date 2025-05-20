#!/usr/bin/env python
"""Test client for the Bluesky MCP server."""

import requests
import json
import sys

print("Attempting to connect to MCP server...")

url = "http://localhost:8000/api/v1/tools"

try:
    # Try to get a list of available tools
    response = requests.get(url)
    
    if response.status_code == 200:
        print("Server is responding!")
        data = response.json()
        print(f"Available tools: {json.dumps(data, indent=2)}")
        sys.exit(0)
    else:
        print(f"Server returned non-200 status code: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)
except Exception as e:
    print(f"Error connecting to server: {e}")
    sys.exit(1)