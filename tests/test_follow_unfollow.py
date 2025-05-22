"""Tests for follow and unfollow operations."""

import json
import os
import pytest
import asyncio

from server import mcp
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)


@pytest.mark.asyncio
async def test_follow_unfollow_operations():
    """Test follow_user and unfollow_user operations.

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
        # Use a test account that we can safely follow/unfollow
        test_handle = "bsky.app"

        print(f"\n1. Testing follow_user with handle={test_handle}...")

        # Follow the user
        follow_params = {"handle": test_handle}
        result = await client.call_tool("follow_user", follow_params)
        follow_result = json.loads(result.content[0].text)

        if (
            follow_result["status"] == "error"
            and "already following" in follow_result.get("message", "").lower()
        ):
            print(f"Already following {test_handle}, will unfollow first")

            # Get the follow URI by checking our follows
            follows_params = {"limit": 100}
            result = await client.call_tool("get_follows", follows_params)
            follows_result = json.loads(result.content[0].text)

            follow_uri = None
            for follow in follows_result["follows"]["follows"]:
                if follow["handle"] == test_handle:
                    follow_uri = follow["viewer"]["following"]
                    break

            if follow_uri:
                # Unfollow first
                unfollow_params = {"follow_uri": follow_uri}
                result = await client.call_tool("unfollow_user", unfollow_params)
                unfollow_result = json.loads(result.content[0].text)
                assert unfollow_result["status"] == "success"

                await asyncio.sleep(1)

                # Now follow again
                result = await client.call_tool("follow_user", follow_params)
                follow_result = json.loads(result.content[0].text)

        assert (
            follow_result["status"] == "success"
        ), f"Failed to follow user: {follow_result.get('message')}"
        assert "follow_uri" in follow_result

        follow_uri = follow_result["follow_uri"]
        print(f"Successfully followed {test_handle}, follow_uri: {follow_uri[:50]}...")

        # Give the API a moment to process
        await asyncio.sleep(1)

        print("\n2. Testing unfollow_user with follow_uri...")

        # Now unfollow the user
        unfollow_params = {"follow_uri": follow_uri}
        result = await client.call_tool("unfollow_user", unfollow_params)
        unfollow_result = json.loads(result.content[0].text)

        assert (
            unfollow_result["status"] == "success"
        ), f"Failed to unfollow user: {unfollow_result.get('message')}"
        print(f"Successfully unfollowed {test_handle}")

        # Give the API a moment to process
        await asyncio.sleep(1)

        # Verify the unfollow by checking our follows list
        print("\n3. Verifying unfollow by checking follows list...")

        follows_params = {"limit": 100}
        result = await client.call_tool("get_follows", follows_params)
        follows_result = json.loads(result.content[0].text)

        # Check that the test account is not in our follows
        still_following = False
        for follow in follows_result["follows"]["follows"]:
            if follow["handle"] == test_handle:
                still_following = True
                break

        assert not still_following, f"Still following {test_handle} after unfollow"

        print("\n✅ All follow/unfollow operations tests passed!")
        print(f"   - follow_user successfully followed {test_handle}")
        print(f"   - unfollow_user successfully unfollowed {test_handle}")
        print("   - Verified user is no longer in follows list")


if __name__ == "__main__":
    asyncio.run(test_follow_unfollow_operations())
