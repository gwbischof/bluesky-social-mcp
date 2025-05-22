"""Tests for feed operations: get_author_feed, get_post_thread."""
import json
import os
import pytest
import asyncio

from server import mcp
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)


@pytest.mark.asyncio
async def test_feed_operations():
    """Test get_author_feed and get_post_thread operations.
    
    This test runs against the actual Bluesky server.
    Requires BLUESKY_IDENTIFIER and BLUESKY_APP_PASSWORD env vars.
    """
    identifier = os.getenv("BLUESKY_IDENTIFIER")
    app_password = os.getenv("BLUESKY_APP_PASSWORD")
    
    if not identifier or not app_password:
        pytest.skip("BLUESKY_IDENTIFIER and BLUESKY_APP_PASSWORD required for live tests")
    
    async with client_session(mcp._mcp_server) as client:
        # First get the user's own handle to test get_author_feed
        print(f"\n1. Testing get_author_feed with handle={identifier}...")
        
        # Test get_author_feed with the user's own handle
        author_feed_params = {
            "actor": identifier,
            "limit": 5
        }
        result = await client.call_tool("get_author_feed", author_feed_params)
        author_feed_result = json.loads(result.content[0].text)
        
        assert author_feed_result["status"] == "success", f"Failed to get author feed: {author_feed_result.get('message')}"
        assert "feed" in author_feed_result
        
        # The feed response should be a dict with 'feed' key
        feed_data = author_feed_result["feed"]
        assert isinstance(feed_data, dict), f"Feed data should be dict, got {type(feed_data)}"
        assert "feed" in feed_data, "Feed data should have a 'feed' key"
        
        # Extract posts from feed
        feed_items = feed_data["feed"]
        if len(feed_items) == 0:
            print("No posts found in author's feed, skipping thread test")
            return
            
        print(f"Found {len(feed_items)} posts in author's feed")
        
        # Get the first post URI for thread testing
        first_post = feed_items[0]["post"]
        post_uri = first_post["uri"]
        
        print(f"\n2. Testing get_post_thread with post URI...")
        
        # Test get_post_thread
        thread_params = {
            "uri": post_uri,
            "depth": 3,  # Get up to 3 levels of replies
            "parent_height": 2  # Get up to 2 parent posts
        }
        result = await client.call_tool("get_post_thread", thread_params)
        thread_result = json.loads(result.content[0].text)
        
        assert thread_result["status"] == "success", f"Failed to get post thread: {thread_result.get('message')}"
        assert "thread" in thread_result
        
        # The thread response should be a dict with 'thread' key
        thread_data = thread_result["thread"]
        assert isinstance(thread_data, dict), f"Thread data should be dict, got {type(thread_data)}"
        assert "thread" in thread_data, "Thread data should have a 'thread' key"
        
        # Verify we got the thread structure
        thread = thread_data["thread"]
        assert "post" in thread, "Thread should have a post"
        
        print(f"\n✅ All feed operations tests passed!")
        print(f"   - get_author_feed returned {len(feed_items)} posts for {identifier}")
        print(f"   - get_post_thread successfully retrieved thread structure")


if __name__ == "__main__":
    asyncio.run(test_feed_operations())