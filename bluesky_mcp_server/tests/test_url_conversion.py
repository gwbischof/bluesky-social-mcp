"""Test the URL conversion utility."""

import unittest
from unittest.mock import MagicMock, patch

from atproto import Client
from bluesky_mcp_server.server import convert_url_to_uri


class TestUrlConversion(unittest.TestCase):
    """Test URL to URI conversion functionality."""
    
    @patch("atproto.Client")
    def test_convert_post_url(self, mock_client_class):
        """Test conversion of a post URL to AT URI."""
        # Setup mock
        mock_client = MagicMock()
        mock_resolved = MagicMock()
        mock_resolved.did = "did:plc:abcdefg"
        mock_client.resolve_handle.return_value = mock_resolved
        mock_client_class.return_value = mock_client
        
        # Setup context
        mock_ctx = MagicMock()
        mock_auth_manager = MagicMock()
        mock_auth_manager.is_authenticated.return_value = False
        mock_ctx.request_context.lifespan_context.auth_manager = mock_auth_manager
        
        # Test URL
        url = "https://bsky.app/profile/test.bsky.social/post/abcdef123"
        
        # Call function
        result = convert_url_to_uri(mock_ctx, url)
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["uri"], "at://did:plc:abcdefg/app.bsky.feed.post/abcdef123")
        
        # Verify mock calls
        mock_client.resolve_handle.assert_called_once_with("test.bsky.social")
    
    @patch("atproto.Client")
    def test_convert_profile_url(self, mock_client_class):
        """Test conversion of a profile URL to DID."""
        # Setup mock
        mock_client = MagicMock()
        mock_resolved = MagicMock()
        mock_resolved.did = "did:plc:abcdefg"
        mock_client.resolve_handle.return_value = mock_resolved
        mock_client_class.return_value = mock_client
        
        # Setup context
        mock_ctx = MagicMock()
        mock_auth_manager = MagicMock()
        mock_auth_manager.is_authenticated.return_value = False
        mock_ctx.request_context.lifespan_context.auth_manager = mock_auth_manager
        
        # Test URL
        url = "https://bsky.app/profile/test.bsky.social"
        
        # Call function
        result = convert_url_to_uri(mock_ctx, url)
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["uri"], "did:plc:abcdefg")
        
        # Verify mock calls
        mock_client.resolve_handle.assert_called_once_with("test.bsky.social")
    
    def test_invalid_url(self):
        """Test handling of invalid URLs."""
        # Setup context
        mock_ctx = MagicMock()
        
        # Test invalid URL
        url = "https://example.com/invalid"
        
        # Call function
        result = convert_url_to_uri(mock_ctx, url)
        
        # Check result
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "Unsupported URL format")


if __name__ == "__main__":
    unittest.main()