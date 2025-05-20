"""Authentication module for Bluesky MCP server."""

import os
from typing import Optional, Tuple

from atproto import Client
from mcp.server.fastmcp import Context


class BlueskyAuthManager:
    """Manager for Bluesky authentication."""

    def __init__(self):
        """Initialize the auth manager."""
        self._clients = {}  # Map session IDs to authenticated clients
    
    def authenticate_from_env(self, ctx: Context) -> Tuple[bool, Optional[str]]:
        """Authenticate with Bluesky using environment variables.
        
        Looks for:
        - BLUESKY_IDENTIFIER: The handle (username)
        - BLUESKY_APP_PASSWORD: The app password
        - BLUESKY_SERVICE_URL: The service URL (defaults to "https://bsky.social")
        
        Args:
            ctx: MCP context
            
        Returns:
            Tuple of success boolean and error message if any
        """
        handle = os.environ.get("BLUESKY_IDENTIFIER")
        password = os.environ.get("BLUESKY_APP_PASSWORD")
        service_url = os.environ.get("BLUESKY_SERVICE_URL", "https://bsky.social")
        
        if not handle or not password:
            return False, "BLUESKY_IDENTIFIER and/or BLUESKY_APP_PASSWORD environment variables not set"
            
        return self.authenticate(handle, password, ctx, service_url)

    def authenticate(
        self, handle: str, password: str, ctx: Context, service_url: str = "https://bsky.social"
    ) -> Tuple[bool, Optional[str]]:
        """Authenticate with Bluesky.

        Args:
            handle: User handle (username)
            password: User password or app password
            ctx: MCP context
            service_url: The Bluesky service URL, defaults to "https://bsky.social"

        Returns:
            Tuple of success boolean and error message if any
        """
        try:
            # Create and authenticate client
            client = Client(service_url)
            profile = client.login(handle, password)

            # Store in session
            session_id = str(ctx.request_context.session.id)
            self._clients[session_id] = client

            ctx.info(f"Authenticated as {profile.display_name} (@{profile.handle})")
            return True, None
        except Exception as e:
            error_msg = f"Authentication failed: {str(e)}"
            ctx.error(error_msg)
            return False, error_msg

    def get_client(self, ctx: Context) -> Optional[Client]:
        """Get authenticated client for the current session.

        Args:
            ctx: MCP context

        Returns:
            Authenticated client if available, None otherwise
        """
        session_id = str(ctx.request_context.session.id)
        return self._clients.get(session_id)

    def is_authenticated(self, ctx: Context) -> bool:
        """Check if the current session is authenticated.

        Args:
            ctx: MCP context

        Returns:
            True if authenticated, False otherwise
        """
        return self.get_client(ctx) is not None

    def logout(self, ctx: Context) -> bool:
        """Log out the current session.

        Args:
            ctx: MCP context

        Returns:
            True if successful, False otherwise
        """
        session_id = str(ctx.request_context.session.id)
        if session_id in self._clients:
            del self._clients[session_id]
            return True
        return False
