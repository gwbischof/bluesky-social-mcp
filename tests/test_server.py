#!/usr/bin/env python
"""Test if the Bluesky MCP server can be imported and run."""

import os
import sys
import inspect
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import MCP components
try:
    from server import mcp
    from mcp.server.fastmcp import FastMCP, Context
except Exception as e:
    print(f"Error importing components: {e}")
    sys.exit(1)


class TestBlueskyServer(unittest.TestCase):
    """Test cases for Bluesky MCP server."""
    
    def test_server_initialization(self):
        """Test that the server has been properly initialized."""
        self.assertIsInstance(mcp, FastMCP)
        self.assertEqual(mcp.name, "bluesky-social")
        
        # Verify lifespan exists
        has_lifespan = hasattr(mcp, "lifespan") or any(attr.endswith("lifespan") for attr in dir(mcp))
        self.assertTrue(has_lifespan)
        
        # Verify run method exists
        self.assertTrue(hasattr(mcp, "run"))
        self.assertTrue(callable(mcp.run))
    
    def test_tools_exist(self):
        """Test that key tools exist."""
        # Get all tool names
        all_tools = [name[len("_tool_"):] for name in dir(mcp) 
                    if name.startswith('_tool_') and callable(getattr(mcp, name))]
        
        # Check for newly added tools
        self.assertIn("resolve_handle", all_tools)
        self.assertIn("block_user", all_tools)
        self.assertIn("unblock_user", all_tools)
        self.assertIn("mute_user", all_tools)
        self.assertIn("unmute_user", all_tools)
        self.assertIn("repost_post", all_tools)
        self.assertIn("unrepost_post", all_tools)
        self.assertIn("unlike_post", all_tools)
        self.assertIn("send_image", all_tools)
        self.assertIn("send_images", all_tools)
        self.assertIn("send_video", all_tools)
        self.assertIn("delete_post", all_tools)


class TestResolveHandle(unittest.TestCase):
    """Tests specifically for the resolve_handle functionality."""
    
    @patch('server.BlueskyAuthManager')
    def test_resolve_handle_functionality(self, mock_auth_manager):
        """Test the resolve_handle tool functionality."""
        # Import the function to test
        from server import resolve_handle
        
        # Create a mock context
        mock_context = MagicMock()
        mock_client = MagicMock()
        
        # Setup mock return value for resolve_handle
        mock_resolved = MagicMock()
        mock_resolved.did = "did:plc:abcdefg123456"
        mock_client.resolve_handle.return_value = mock_resolved
        
        # Setup mock auth manager to return the mock client
        mock_auth_manager_instance = MagicMock()
        mock_auth_manager_instance.is_authenticated.return_value = False
        mock_auth_manager_instance.get_client.return_value = mock_client
        mock_context.request_context.lifespan_context.auth_manager = mock_auth_manager_instance
        
        # Test with unauthenticated client creation path
        with patch('server.Client') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Call the function
            result = resolve_handle(mock_context, "test.bsky.social")
            
            # Check results
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["handle"], "test.bsky.social")
            self.assertEqual(result["did"], "did:plc:abcdefg123456")
            
            # Verify client was created and used correctly
            mock_client_class.assert_called_once()
            mock_client.resolve_handle.assert_called_with("test.bsky.social")


if __name__ == "__main__":
    print("Running Bluesky MCP server tests...")
    unittest.main()
