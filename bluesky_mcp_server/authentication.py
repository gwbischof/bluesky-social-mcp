"""Authentication module for Bluesky MCP server."""

from typing import Optional, Tuple

from atproto import Client
from mcp.server.fastmcp import Context


class BlueskyAuthManager:
    """Manager for Bluesky authentication."""

    def __init__(self):
        """Initialize the auth manager."""
        self._clients = {}  # Map session IDs to authenticated clients

    def authenticate(
        self, handle: str, password: str, ctx: Context
    ) -> Tuple[bool, Optional[str]]:
        """Authenticate with Bluesky.

        Args:
            handle: User handle (username)
            password: User password or app password
            ctx: MCP context

        Returns:
            Tuple of success boolean and error message if any
        """
        try:
            # Create and authenticate client
            client = Client()
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
