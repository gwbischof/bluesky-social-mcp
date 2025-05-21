#!/usr/bin/env python
"""Integration tests for Bluesky MCP server post operations."""
import os
import sys
import pytest
import uuid

from server import mcp
from mcp.shared.memory import create_connected_server_and_client_session as client_session

@pytest.mark.anyio
async def test_create_and_delete_post():
    """Test creating a post and then deleting it.

    This test doesn't work.
    There isn't any good documentation about making pytest for FastMCP servers.
    The modelcontextprotocol/python-sdk docs say that the fastest way to test is
    with MCP Inspector.

    So I will leave this as a place holder.
    """
    # Create client session
    async with client_session(mcp._mcp_server) as client:
        # 1. Create a post with a unique identifier to avoid duplicate posts
        print("HELLO")
        unique_id = str(uuid.uuid4())[:8]
        test_text = f"Test post from Bluesky MCP test suite - {unique_id}"
        create_params = {"text": test_text}

        # Call the create_post tool
        create_result = await client.call_tool("create_post", create_params)

        # # The result is a CallToolResult object - convert to dict to check properties
        # create_result_dict = create_result.model_dump()

        # # Verify create result
        # assert create_result_dict.get("status") == "success"
        # assert "post_uri" in create_result_dict
        # assert "post_cid" in create_result_dict

        # post_uri = create_result_dict["post_uri"]

        # # 2. Delete the post we just created
        # delete_params = {"uri": post_uri}
        # delete_result = await client.call_tool("delete_post", delete_params)

        # # Convert result to dict and verify
        # delete_result_dict = delete_result.model_dump()
        # assert delete_result_dict.get("status") == "success"
        # assert "Post deleted successfully" in delete_result_dict.get("message", "")


