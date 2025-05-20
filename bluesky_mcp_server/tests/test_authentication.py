"""Test authentication functionality."""

import unittest
from unittest.mock import MagicMock, patch

from bluesky_mcp_server.authentication import BlueskyAuthManager


class TestBlueskyAuthManager(unittest.TestCase):
    """Test the BlueskyAuthManager class."""

    def test_is_authenticated(self):
        """Test is_authenticated method."""
        auth_manager = BlueskyAuthManager()
        context = MagicMock()
        context.request_context.session_id = "test_session"

        # Should be False when no client exists
        self.assertFalse(auth_manager.is_authenticated(context))

        # Should be True when client exists
        auth_manager._clients["test_session"] = MagicMock()
        self.assertTrue(auth_manager.is_authenticated(context))

    def test_logout(self):
        """Test logout method."""
        auth_manager = BlueskyAuthManager()
        context = MagicMock()
        context.request_context.session_id = "test_session"

        # Should return False when no client exists
        self.assertFalse(auth_manager.logout(context))

        # Should return True and remove client when exists
        auth_manager._clients["test_session"] = MagicMock()
        self.assertTrue(auth_manager.logout(context))
        self.assertFalse("test_session" in auth_manager._clients)

    @patch("bluesky_mcp_server.authentication.Client")
    def test_authenticate(self, mock_client_class):
        """Test authenticate method."""
        mock_client = MagicMock()
        mock_profile = MagicMock()
        mock_profile.display_name = "Test User"
        mock_profile.handle = "test.user"
        mock_client.login.return_value = mock_profile
        mock_client_class.return_value = mock_client

        auth_manager = BlueskyAuthManager()
        context = MagicMock()
        context.request_context.session_id = "test_session"

        success, error = auth_manager.authenticate("test.user", "password", context)

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertEqual(auth_manager._clients["test_session"], mock_client)

        # Test failure case
        mock_client.login.side_effect = Exception("Login failed")
        success, error = auth_manager.authenticate("test.user", "password", context)

        self.assertFalse(success)
        self.assertEqual(error, "Authentication failed: Login failed")


if __name__ == "__main__":
    unittest.main()
