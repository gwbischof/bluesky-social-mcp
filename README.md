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
- ✅ `get_profile` - Get a user profile (Client method: `get_profile`)
- ✅ `get_follows` - Get users followed by an account (Client method: `get_follows`)
- ✅ `get_followers` - Get users who follow an account (Client method: `get_followers`) 
- ✅ `follow_user` - Follow a user (Client method: `follow`)
- ❓ `unfollow_user` - Unfollow a user (Client method: `unfollow`)
- ❓ `mute_user` - Mute a user (Client method: `mute`)
- ❓ `unmute_user` - Unmute a user (Client method: `unmute`)
- ❓ `resolve_handle` - Resolve a handle to DID (Client method: `resolve_handle`)

### Feed Operations
- ❓ `get_timeline` - Get posts from your home timeline (Client method: `get_timeline`)
- ❓ `get_author_feed` - Get posts from a specific user (Client method: `get_author_feed`)
- ❓ `get_post_thread` - Get a full conversation thread (Client method: `get_post_thread`)

### Post Interactions
- ✅ `like_post` - Like a post (Client method: `like`)
- ✅ `unlike_post` - Unlike a post (Client method: `unlike`)
- ✅ `get_likes` - Get likes for a post (Client method: `get_likes`)
- ✅ `repost` - Repost a post (Client method: `repost`)
- ✅ `unrepost` - Remove a repost (Client method: `unrepost`)
- ✅ `get_reposted_by` - Get users who reposted (Client method: `get_reposted_by`)

### Post Creation & Management
- ✅ `send_post` - Create a new text post (Client method: `send_post`)
- ❓ `send_image` - Send a post with a single image (Client method: `send_image`)
- ❓ `send_images` - Send a post with multiple images (Client method: `send_images`)
- ❓ `send_video` - Send a post with a video (Client method: `send_video`)
- ✅ `delete_post` - Delete a post (Client method: `delete_post`)
- ❓ `get_post` - Get a specific post (Client method: `get_post`)
- ❓ `get_posts` - Get multiple posts (Client method: `get_posts`)

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
