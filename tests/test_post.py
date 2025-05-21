#!/usr/bin/env python
"""Integration tests for Bluesky MCP server post operations."""
import json
import os
import sys
import pytest
import uuid

from server import mcp
from mcp.shared.memory import create_connected_server_and_client_session as client_session

@pytest.mark.anyio
async def test_create_and_delete_post():
    """Test creating a post and then deleting it."""
    # Create client session
    async with client_session(mcp._mcp_server) as client:
        # 1. Create a post with a unique identifier to avoid duplicate posts
        unique_id = str(uuid.uuid4())[:8]
        test_text = f"Test post from Bluesky MCP test suite - {unique_id}"
        create_params = {"text": test_text}

        # Call the create_post tool
        result = await client.call_tool("create_post", create_params)
        post_result = json.loads(result.content[0].text)

        # # Verify create result
        assert post_result.get("status") == "success"

        post_uri = post_result["post_uri"]

        # 2. Delete the post we just created
        delete_params = {"uri": post_uri}
        result = await client.call_tool("delete_post", delete_params)
        delete_result = json.loads(result.content[0].text)
        assert delete_result.get("status") == "success"
