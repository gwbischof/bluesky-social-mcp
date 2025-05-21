# Bluesky Model Context Protocol Server

An MCP server for interacting with the Bluesky social network, providing tools for accessing Bluesky data and performing actions through Claude.

Built with FastMCP, this server offers seamless integration with Claude and provides a comprehensive set of tools for Bluesky API operations.

## Features

This MCP server provides tools for all major Bluesky API operations including:

### Authentication
- `check_auth_status`: Check if you're authenticated
- `check_environment_variables`: Verify your environment variables are set correctly

### Profile
- `get_profile`: Get a user profile
- `get_follows`: Get users followed by an account
- `get_followers`: Get users who follow an account

### Timeline
- `get_timeline_posts`: Get posts from your home timeline
- `get_feed_posts`: Get posts from a specific feed
- `get_list_posts`: Get posts from a specific list
- `get_user_posts`: Get posts from a specific user

### Interaction
- `get_liked_posts`: Get posts liked by a user
- `like_post`: Like a post
- `create_post`: Create a new post with optional images, reply and quote support
- `follow_user`: Follow a specific user

### Search
- `search_posts`: Search for posts
- `search_people`: Search for people
- `search_feeds`: Search for feeds

### Utilities
- `get_post_thread`: Get a full conversation thread
- `convert_url_to_uri`: Convert a Bluesky web URL to AT URI format
- `get_trends`: Get current trending topics on Bluesky
- `get_pinned_feeds`: Get pinned feeds from user preferences

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
