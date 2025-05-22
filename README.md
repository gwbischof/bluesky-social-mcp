# Bluesky Social MCP

An MCP server for interacting with the Bluesky social network via the [atproto](https://github.com/MarshalX/atproto) client.

## Quick Start

Get your Bluesky app password at: https://bsky.app/settings/app-passwords

Add to your Claude Desktop config:
```json
{
  "mcpServers": {
    "bluesky-social": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/gwbischof/bluesky-social-mcp", "bluesky-social-mcp"],
      "env": {
        "BLUESKY_IDENTIFIER": "your-handle.bsky.social",
        "BLUESKY_APP_PASSWORD": "your-app-password"
      }
    }
  }
}
```

## Tool Status
- ✅ = Tested and working
- ❓ = Not yet tested

### Authentication & Setup
- ✅ `check_auth_status` - Check if the current session is authenticated

### Profile Operations
- ✅ `get_profile` - Get a user profile
- ✅ `get_follows` - Get users followed by an account
- ✅ `get_followers` - Get users who follow an account
- ✅ `follow_user` - Follow a user
- ❓ `block_user` - Block a user
- ❓ `unblock_user` - Unblock a previously blocked user
- ❓ `get_blocks` - Get list of blocked users
- ❓ `mute_user` - Mute a user
- ❓ `unmute_user` - Unmute a previously muted user
- ❓ `get_mutes` - Get list of muted users

### Feed Operations
- ❓ `get_timeline_posts` - Get posts from your home timeline
- ❓ `get_feed_posts` - Get posts from a specific feed
- ❓ `get_list_posts` - Get posts from a specific list
- ❓ `get_user_posts` - Get posts from a specific user
- ❓ `get_liked_posts` - Get posts liked by a user
- ❓ `get_post_thread` - Get a full conversation thread for a post

### Post Interactions
- ✅ `like_post` - Like a post
- ✅ `unlike_post` - Unlike a post
- ✅ `get_likes` - Get likes for a post
- ❓ `repost_post` - Repost another user's post
- ❓ `unrepost_post` - Remove a repost
- ❓ `get_reposted_by` - Get users who reposted a post

### Post Creation
- ✅ `send_post` - Create a new text post with optional replies/quotes/embeds
- ❓ `send_image` - Send a post with a single image
- ❓ `send_images` - Send a post with multiple images (up to 4)
- ❓ `send_video` - Send a post with a video
- ✅ `delete_post` - Delete a post

### Notification Management
- ❓ `get_notifications` - Get notifications for your account
- ❓ `count_unread_notifications` - Count unread notifications
- ❓ `mark_notifications_seen` - Mark all notifications as seen
- ❓ `get_notification_preferences` - Get notification preferences

### Search
- ❓ `search_posts` - Search for posts with keywords
- ❓ `search_people` - Search for users/profiles
- ❓ `search_feeds` - Search for feeds

### Utilities
- ❓ `convert_url_to_uri` - Convert a Bluesky web URL to AT URI format
- ❓ `get_trends` - Get current trending topics on Bluesky
- ❓ `get_pinned_feeds` - Get pinned feeds from user preferences

### Run from local clone of repo.
```bash
{
    "mcpServers": {
        "bluesky-social": {
            "command": "uv",
            "args": [
                "--directory",
                "/ABSOLUTE/PATH/TO/PARENT/FOLDER/bluesky-social-mcp",
                "run",
                "server.py"
            ]
            "env": {
                "BLUESKY_IDENTIFIER": "user-name.bsky.social‬",
                "BLUESKY_APP_PASSWORD": "app-password-here"
            }
        }
    }
}
```

# Dev Setup
1. Install dependencies:
   ```bash
   uv sync
   ```

2. Run the server:
   ```bash
   uv run bluesky-social-mcp
   ```

### Debug with MCP Inspector
```bash
mcp dev server.py
mcp dev server.py --with-editable .
```

### Run the tests
- I run the tests against the actual Bluesky server.
- The tests will use BLUESKY_IDENTIFIER, and BLUESKY_APP_PASSWORD env vars.
```bash
uv run pytest
```
