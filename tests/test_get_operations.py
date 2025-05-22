"""Tests for get operations: get_post, get_posts, get_timeline."""

import json
import os
import pytest
import asyncio

from server import mcp
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)


@pytest.mark.asyncio
async def test_get_operations():
    """Test get_post, get_posts, and get_timeline operations.

    This test runs against the actual Bluesky server.
    Requires BLUESKY_IDENTIFIER and BLUESKY_APP_PASSWORD env vars.
    """
    identifier = os.getenv("BLUESKY_IDENTIFIER")
    app_password = os.getenv("BLUESKY_APP_PASSWORD")

    if not identifier or not app_password:
        pytest.skip(
            "BLUESKY_IDENTIFIER and BLUESKY_APP_PASSWORD required for live tests"
        )

    async with client_session(mcp._mcp_server) as client:
        # Test get_timeline first to get some posts
        print("\n1. Testing get_timeline...")
        timeline_params = {"limit": 5}
        result = await client.call_tool("get_timeline", timeline_params)
        timeline_result = json.loads(result.content[0].text)

        assert (
            timeline_result["status"] == "success"
        ), f"Failed to get timeline: {timeline_result.get('message')}"
        assert "timeline" in timeline_result

        # The timeline response should be a dict with 'feed' key
        timeline_data = timeline_result["timeline"]
        assert isinstance(
            timeline_data, dict
        ), f"Timeline data should be dict, got {type(timeline_data)}"
        assert "feed" in timeline_data, "Timeline should have a feed key"

        # Extract post URIs from timeline for further testing
        feed_items = timeline_data["feed"]

        if len(feed_items) == 0:
            print("No posts in timeline, creating a test post...")
            # Create a test post to ensure we have something to work with
            post_params = {"text": "Test post for get operations test"}
            result = await client.call_tool("send_post", post_params)
            test_post_result = json.loads(result.content[0].text)
            assert test_post_result["status"] == "success"

            # Wait a moment and get timeline again
            await asyncio.sleep(2)
            result = await client.call_tool("get_timeline", timeline_params)
            timeline_result = json.loads(result.content[0].text)
            timeline_data = timeline_result["timeline"]
            feed_items = timeline_data["feed"]

        assert len(feed_items) > 0, "No posts in timeline even after creating test post"

        # Get the first post URI and extract rkey
        first_post = feed_items[0]["post"]
        post_uri = first_post["uri"]  # Format: at://did:plc:xxx/app.bsky.feed.post/rkey

        # Parse the URI to get author DID and rkey
        uri_parts = post_uri.split("/")
        author_did = uri_parts[2]  # did:plc:xxx
        post_rkey = uri_parts[-1]  # the rkey

        print(
            f"\n2. Testing get_post with rkey={post_rkey[:8]}... and author={author_did[:20]}..."
        )

        # Test get_post with the extracted post
        post_params = {"post_rkey": post_rkey, "profile_identify": author_did}
        result = await client.call_tool("get_post", post_params)
        post_result = json.loads(result.content[0].text)

        assert (
            post_result["status"] == "success"
        ), f"Failed to get post: {post_result.get('message')}"
        assert "post" in post_result

        # Test get_posts with multiple URIs
        print("\n3. Testing get_posts with multiple URIs...")

        # Get up to 3 post URIs from timeline
        post_uris = [item["post"]["uri"] for item in feed_items[:3]]

        posts_params = {"uris": post_uris}
        result = await client.call_tool("get_posts", posts_params)
        posts_result = json.loads(result.content[0].text)

        assert (
            posts_result["status"] == "success"
        ), f"Failed to get posts: {posts_result.get('message')}"
        assert "posts" in posts_result

        # The posts response should have a posts key
        posts_data = posts_result["posts"]
        assert isinstance(posts_data, dict), "Posts data should be a dict"
        assert "posts" in posts_data, "Posts data should have a 'posts' key"

        returned_posts = posts_data["posts"]
        assert len(returned_posts) > 0, "No posts returned"

        print("\n✅ All get operations tests passed!")
        print(f"   - get_timeline returned {len(feed_items)} posts")
        print("   - get_post successfully retrieved post")
        print(f"   - get_posts retrieved {len(returned_posts)} posts")


if __name__ == "__main__":
    asyncio.run(test_get_operations())
