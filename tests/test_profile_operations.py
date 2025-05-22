#!/usr/bin/env python
"""Integration tests for Bluesky MCP server profile operations."""
import json
import pytest
import asyncio

from server import mcp
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)


@pytest.mark.asyncio
async def test_profile_follow_operations():
    """Test profile operations including get_follows, get_followers, and follow_user."""
    # Create client session
    async with client_session(mcp._mcp_server) as client:
        # First, get the authenticated user's profile to have our handle
        profile_result = await client.call_tool("get_profile", {})
        profile_data = json.loads(profile_result.content[0].text)
        assert profile_data.get("status") == "success"
        my_handle = profile_data["profile"]["handle"]
        
        # Get current follows (before following anyone new)
        follows_params = {"limit": 10}
        result = await client.call_tool("get_follows", follows_params)
        follows_result = json.loads(result.content[0].text)
        assert follows_result.get("status") == "success"
        
        initial_follows = follows_result["follows"]
        initial_follow_count = len(initial_follows.get("follows", []))
        print(f"Initial follow count: {initial_follow_count}")
        
        # Get current followers
        followers_params = {"limit": 10}
        result = await client.call_tool("get_followers", followers_params)
        followers_result = json.loads(result.content[0].text)
        assert followers_result.get("status") == "success"
        
        initial_followers = followers_result["followers"]
        initial_follower_count = len(initial_followers.get("followers", []))
        print(f"Initial follower count: {initial_follower_count}")
        
        # Follow a well-known test account (Bluesky team account)
        test_handle = "bsky.app"
        follow_params = {"handle": test_handle}
        
        # Check if we're already following this account
        already_following = False
        for follow in initial_follows.get("follows", []):
            if follow.get("handle") == test_handle:
                already_following = True
                print(f"Already following {test_handle}")
                break
        
        if not already_following:
            # Follow the account
            result = await client.call_tool("follow_user", follow_params)
            follow_result = json.loads(result.content[0].text)
            assert follow_result.get("status") == "success"
            assert follow_result.get("follow_uri") is not None
            print(f"Successfully followed {test_handle}")
            
            # Wait a moment for the follow to propagate
            await asyncio.sleep(2)
            
            # Verify the follow by checking our follows list again
            result = await client.call_tool("get_follows", follows_params)
            new_follows_result = json.loads(result.content[0].text)
            assert new_follows_result.get("status") == "success"
            
            new_follows = new_follows_result["follows"]
            new_follow_count = len(new_follows.get("follows", []))
            
            # We should have one more follow
            assert new_follow_count >= initial_follow_count
            
            # Verify the followed account is in the list
            found_in_follows = False
            for follow in new_follows.get("follows", []):
                if follow.get("handle") == test_handle:
                    found_in_follows = True
                    break
            assert found_in_follows, f"{test_handle} not found in follows list"
        
        # Test getting follows for a specific user (not ourselves)
        specific_follows_params = {"handle": test_handle, "limit": 5}
        result = await client.call_tool("get_follows", specific_follows_params)
        specific_follows_result = json.loads(result.content[0].text)
        assert specific_follows_result.get("status") == "success"
        
        # Test getting followers for a specific user
        specific_followers_params = {"handle": test_handle, "limit": 5}
        result = await client.call_tool("get_followers", specific_followers_params)
        specific_followers_result = json.loads(result.content[0].text)
        assert specific_followers_result.get("status") == "success"
        
        print("All profile operations tests passed!")