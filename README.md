# Bluesky Model Context Protocol Server

An MCP server for interacting with the Bluesky social network, providing tools for accessing Bluesky data and performing actions through Claude.

## Features

This MCP server provides tools for all major Bluesky API operations including:

### Authentication
- `login`: Log in with your Bluesky handle and app password
- `logout`: Log out of Bluesky
- `check_auth_status`: Check if you're authenticated

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
- `create_post`: Create a new post
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

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/bluesky-mcp-server.git
   cd bluesky-mcp-server
   ```

2. Install dependencies:
   ```
   uv add atproto mcp[cli]
   ```

3. Run the server:
   ```
   uv run python -m bluesky_mcp_server.server
   ```

   Note: The server requires Python 3.12 or higher as specified in pyproject.toml.

## Usage

To use with Claude:

1. Install the MCP server in Claude Desktop:
   ```
   mcp install path_to_your_server.py
   ```

2. In Claude, authenticate with your Bluesky account:
   ```
   /tool login --handle "yourusername.bsky.social" --password "your-app-password"
   ```

3. Use any of the available tools, for example:
   ```
   /tool get_timeline_posts
   ```
