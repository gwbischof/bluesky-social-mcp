"""Authentication module for Bluesky MCP server."""

import os
from typing import Optional

from atproto import Client


def login() -> Client:
    """Login to Bluesky API and return the client.
    
    Authenticates using environment variables:
    - BLUESKY_IDENTIFIER: The handle (username)
    - BLUESKY_APP_PASSWORD: The app password
    - BLUESKY_SERVICE_URL: The service URL (defaults to "https://bsky.social")
    
    Returns:
        Authenticated Client instance or None if authentication fails
    """
    handle = os.environ.get("BLUESKY_IDENTIFIER")
    password = os.environ.get("BLUESKY_APP_PASSWORD")
    service_url = os.environ.get("BLUESKY_SERVICE_URL", "https://bsky.social")
    
    if not handle or not password:
        raise ValueError("BLUESKY_IDENTIFIER and/or BLUESKY_APP_PASSWORD environment variables not set")
    
        # Create and authenticate client
    client = Client(service_url)
    client.login(handle, password)
    return client

if __name__ == "__main__":
    login()
