#!/usr/bin/env python
"""Integration tests for Bluesky MCP server post operations."""
import json
import pytest
import uuid
import asyncio

from server import mcp
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)


@pytest.mark.asyncio
async def test_create_and_delete_post():
    """Test creating a post and then deleting it."""
    # Create client session
    async with client_session(mcp._mcp_server) as client:
        # Create a post with a unique identifier to avoid duplicate posts
        unique_id = str(uuid.uuid4())[:8]
        test_text = f"Test post from Bluesky MCP test suite - {unique_id}"
        create_params = {"text": test_text}

        # Call the send_post tool
        result = await client.call_tool("send_post", create_params)
        post_result = json.loads(result.content[0].text)
        assert post_result.get("status") == "success", f"Failed with: {post_result.get('message')}"

        post_uri = post_result["post_uri"]
        post_cid = post_result["post_cid"]

        # Get likes for the post (should be empty)
        get_likes_params = {"uri": post_uri}
        result = await client.call_tool("get_likes", get_likes_params)
        likes_result = json.loads(result.content[0].text)
        assert likes_result.get("status") == "success"

        # Verify initial like count is 0 or likes array is empty
        likes_data = likes_result.get("likes", {})
        initial_likes = len(likes_data.get("likes", []))
        assert initial_likes == 0

        # Like the post
        like_params = {"uri": post_uri, "cid": post_cid}
        result = await client.call_tool("like_post", like_params)
        like_result = json.loads(result.content[0].text)
        assert like_result.get("status") == "success"

        await asyncio.sleep(1)
        # Get likes for the post (should be empty)
        get_likes_params = {"uri": post_uri}
        result = await client.call_tool("get_likes", get_likes_params)
        likes_result = json.loads(result.content[0].text)
        assert likes_result.get("status") == "success"

        # Like count should be 1
        likes_data = likes_result.get("likes", {})
        like_count = len(likes_data.get("likes", []))
        assert like_count == 1

        # TODO: this part doesn't work yet, I'm not sure how to get the like_uri.
        # Unlike the post
        # like_uri = likes_data['likes'][0]
        # unlike_params = {"like_uri": like_uri}
        # result = await client.call_tool("unlike_post", unlike_params)
        # unlike_result = json.loads(result.content[0].text)
        # assert unlike_result.get("status") == "success"

        # Delete the post we just created
        delete_params = {"uri": post_uri}
        result = await client.call_tool("delete_post", delete_params)
        delete_result = json.loads(result.content[0].text)
        assert delete_result.get("status") == "success"
