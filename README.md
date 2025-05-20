# Bluesky Model Context Protocol Server

An MCP server for interacting with the Bluesky social network, providing tools for accessing Bluesky data and performing actions through Claude.

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

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bluesky-social-mcp.git
   cd bluesky-social-mcp
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

   Or if starting fresh:
   ```bash
   uv add atproto mcp[cli] requests
   uv add --dev black mypy pytest ruff
   ```

3. Run the server:
   ```bash
   uv run python bluesky_mcp_server/server.py
   ```

   Or as a module:
   ```bash
   uv run python -m bluesky_mcp_server.server
   ```

## Authentication

This MCP server uses environment variables for authentication. Before using any tool that requires authentication, set the following environment variables:

Required:
```bash
export BLUESKY_IDENTIFIER=yourusername.bsky.social
export BLUESKY_APP_PASSWORD=your-app-password
```

Optional:
```bash
export BLUESKY_SERVICE_URL=https://bsky.social  # Default value, change if using a different instance
```

Authentication happens automatically when you use any tool that requires it. No explicit login command is needed.

## Using with Claude

### Communication Modes

The server supports two communication modes:

1. **HTTP Server** (default for interactive use)
   - Used when running the server directly in a terminal
   - Accessible via HTTP requests to localhost

2. **StdIO Server** (automatic for Claude integration)
   - Used when the server is run with piped input/output
   - Automatically activated when used with Claude
   - Allows direct communication between Claude and the server

### Installation in Claude

1. Install the MCP server in Claude:
   ```bash
   mcp install /path/to/bluesky_mcp_server/server.py
   ```

2. Set environment variables in your Claude environment:
   ```bash
   export BLUESKY_IDENTIFIER=yourusername.bsky.social
   export BLUESKY_APP_PASSWORD=your-app-password
   ```

3. Access tools in Claude using the `/tool` command with the appropriate tool name.

## Development

### Running Tests
```bash
uv run pytest
```

### Code Formatting
```bash
uv run black .
```

### Linting
```bash
uv run ruff check .
```

### Type Checking
```bash
uv run mypy .
```