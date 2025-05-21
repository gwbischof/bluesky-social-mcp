# Bluesky Model Context Protocol Server

An MCP server for interacting with the Bluesky social network.
Provides support for all of the methods of the python Bluesky client: [atproto](https://github.com/MarshalX/atproto)

## Note
- Create and Delete post are working.
- I have to test the rest of the tools.
- I will also add uvx support.

## Tools

### Authentication & Setup
- `check_environment_variables` - Check if Bluesky environment variables are set correctly
- `check_auth_status` - Check if the current session is authenticated
- `resolve_handle` - Convert a Bluesky handle to a DID

### Profile Operations
- `get_profile` - Get a user profile
- `get_follows` - Get users followed by an account
- `get_followers` - Get users who follow an account
- `follow_user` - Follow a user
- `block_user` - Block a user
- `unblock_user` - Unblock a previously blocked user
- `get_blocks` - Get list of blocked users
- `mute_user` - Mute a user
- `unmute_user` - Unmute a previously muted user
- `get_mutes` - Get list of muted users

### Feed Operations
- `get_timeline_posts` - Get posts from your home timeline
- `get_feed_posts` - Get posts from a specific feed
- `get_list_posts` - Get posts from a specific list
- `get_user_posts` - Get posts from a specific user
- `get_liked_posts` - Get posts liked by a user
- `get_post_thread` - Get a full conversation thread for a post

### Post Interactions
- `like_post` - Like a post
- `unlike_post` - Unlike a post
- `get_likes` - Get likes for a post
- `repost_post` - Repost another user's post
- `unrepost_post` - Remove a repost
- `get_reposted_by` - Get users who reposted a post

### Post Creation
- `create_post` - Create a new text post with optional replies/quotes
- `send_image` - Send a post with a single image
- `send_images` - Send a post with multiple images (up to 4)
- `send_video` - Send a post with a video
- `delete_post` - Delete a post

### Notification Management
- `get_notifications` - Get notifications for your account
- `count_unread_notifications` - Count unread notifications
- `mark_notifications_seen` - Mark all notifications as seen
- `get_notification_preferences` - Get notification preferences

### Search
- `search_posts` - Search for posts with keywords
- `search_people` - Search for users/profiles
- `search_feeds` - Search for feeds

### Utilities
- `convert_url_to_uri` - Convert a Bluesky web URL to AT URI format
- `get_trends` - Get current trending topics on Bluesky
- `get_pinned_feeds` - Get pinned feeds from user preferences

## Installation

### Prerequisites
- Python 3.12 or higher
- uv package manager

### Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Run the server:
   ```bash
   uv run python server.py
   ```

### Debug with MCP Inspector
```bash
mcp dev server.py
mcp dev server.py --with pandas --with numpy
mcp dev server.py --with-editable .
```

## Using with Claude

### Installation in Claude

1. Install the MCP server in Claude through CLI:
   ```bash
   uv run mcp install server.py -v BLUESKY_IDENTIFIER=yourusername.bsky.social -v BLUESKY_APP_PASSWORD=your-app-password
   ```

2. Or update your mcp server config file like this:
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
        }
    }
}
```
