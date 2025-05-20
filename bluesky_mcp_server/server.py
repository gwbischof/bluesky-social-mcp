"""Bluesky MCP Server."""

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Dict, List, Optional

from mcp.server.fastmcp import Context, FastMCP

from bluesky_mcp_server.authentication import BlueskyAuthManager
from bluesky_mcp_server.tools import (
    get_profile, 
    get_follows, 
    get_followers,
    get_timeline_posts,
    get_feed_posts,
    get_list_posts,
    get_user_posts,
    get_liked_posts,
    like_post,
    create_post,
    follow_user,
    search_posts,
    search_people,
    search_feeds,
    get_post_thread,
    convert_url_to_uri,
    get_trends,
    get_pinned_feeds
)


@dataclass
class ServerContext:
    """Server context holding shared resources."""

    auth_manager: BlueskyAuthManager


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[ServerContext]:
    """Manage application lifecycle with typed context.

    Args:
        server: The FastMCP server instance

    Yields:
        ServerContext with initialized resources
    """
    # Initialize resources
    auth_manager = BlueskyAuthManager()

    try:
        yield ServerContext(auth_manager=auth_manager)
    finally:
        # Cleanup resources when shutting down
        pass


# Create MCP server
mcp = FastMCP(
    name="BlueskyMCP",
    lifespan=app_lifespan,
    dependencies=["atproto", "mcp"],
)


@mcp.tool()
def login(handle: str, password: str, ctx: Context) -> dict:
    """Log in to Bluesky with your handle and app password.

    Args:
        handle: Your Bluesky handle (username)
        password: Your Bluesky password or app password
        ctx: MCP context

    Returns:
        Status of authentication
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    success, error = auth_manager.authenticate(handle, password, ctx)

    if success:
        return {"status": "success", "message": f"Logged in as {handle}"}
    else:
        return {"status": "error", "message": error}


@mcp.tool()
def logout(ctx: Context) -> dict:
    """Log out from Bluesky.

    Args:
        ctx: MCP context

    Returns:
        Status of logout operation
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    success = auth_manager.logout(ctx)

    if success:
        return {"status": "success", "message": "Logged out successfully"}
    else:
        return {"status": "error", "message": "Not logged in"}


@mcp.tool()
def check_auth_status(ctx: Context) -> dict:
    """Check if the current session is authenticated.

    Args:
        ctx: MCP context

    Returns:
        Authentication status
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    is_authenticated = auth_manager.is_authenticated(ctx)

    if is_authenticated:
        client = auth_manager.get_client(ctx)
        return {
            "status": "authenticated",
            "handle": client.me.handle,
            "did": client.me.did,
        }
    else:
        return {"status": "not_authenticated"}


@mcp.tool()
def get_profile_tool(ctx: Context, handle: Optional[str] = None) -> Dict:
    """Get a user profile.

    Args:
        ctx: MCP context
        handle: Optional handle to get profile for. If None, gets the authenticated user

    Returns:
        Profile data
    """
    return get_profile(ctx, handle)


@mcp.tool()
def get_follows_tool(
    ctx: Context,
    handle: Optional[str] = None,
    limit: int = 50,
    cursor: Optional[str] = None,
) -> Dict:
    """Get users followed by an account.

    Args:
        ctx: MCP context
        handle: Optional handle to get follows for. If None, gets the authenticated user
        limit: Maximum number of results to return (1-100)
        cursor: Optional pagination cursor

    Returns:
        List of followed accounts
    """
    return get_follows(ctx, handle, limit, cursor)


@mcp.tool()
def get_followers_tool(
    ctx: Context,
    handle: Optional[str] = None,
    limit: int = 50,
    cursor: Optional[str] = None,
) -> Dict:
    """Get users who follow an account.

    Args:
        ctx: MCP context
        handle: Optional handle to get followers for. If None, gets the authenticated user
        limit: Maximum number of results to return (1-100)
        cursor: Optional pagination cursor

    Returns:
        List of follower accounts
    """
    return get_followers(ctx, handle, limit, cursor)


@mcp.tool()
def get_timeline_posts_tool(
    ctx: Context,
    limit: int = 50,
    cursor: Optional[str] = None,
    algorithm: Optional[str] = None,
) -> Dict:
    """Get posts from the authenticated user's home timeline.
    
    Args:
        ctx: MCP context
        limit: Maximum number of results to return (1-100)
        cursor: Optional pagination cursor
        algorithm: Optional algorithm to use, e.g. "reverse-chronological"
        
    Returns:
        Timeline posts
    """
    return get_timeline_posts(ctx, limit, cursor, algorithm)


@mcp.tool()
def get_feed_posts_tool(
    ctx: Context,
    feed: str,
    limit: int = 50,
    cursor: Optional[str] = None,
) -> Dict:
    """Get posts from a specified feed.
    
    Args:
        ctx: MCP context
        feed: URI of the feed to get posts from
        limit: Maximum number of results to return (1-100)
        cursor: Optional pagination cursor
        
    Returns:
        Feed posts
    """
    return get_feed_posts(ctx, feed, limit, cursor)


@mcp.tool()
def get_list_posts_tool(
    ctx: Context,
    list_uri: str,
    limit: int = 50,
    cursor: Optional[str] = None,
) -> Dict:
    """Get posts from the specified list.
    
    Args:
        ctx: MCP context
        list_uri: URI of the list to get posts from
        limit: Maximum number of results to return (1-100)
        cursor: Optional pagination cursor
        
    Returns:
        List posts
    """
    return get_list_posts(ctx, list_uri, limit, cursor)


@mcp.tool()
def get_user_posts_tool(
    ctx: Context,
    handle: Optional[str] = None,
    limit: int = 50,
    cursor: Optional[str] = None,
    filter: Optional[str] = None,
) -> Dict:
    """Get posts from a specified user.
    
    Args:
        ctx: MCP context
        handle: Optional handle to get posts for. If None, gets the authenticated user
        limit: Maximum number of results to return (1-100)
        cursor: Optional pagination cursor
        filter: Optional filter, e.g. "posts_with_media", "posts_no_replies"
        
    Returns:
        User posts
    """
    return get_user_posts(ctx, handle, limit, cursor, filter)


@mcp.tool()
def get_liked_posts_tool(
    ctx: Context,
    handle: Optional[str] = None,
    limit: int = 50,
    cursor: Optional[str] = None,
) -> Dict:
    """Get posts liked by a user.
    
    Args:
        ctx: MCP context
        handle: Optional handle to get likes for. If None, gets the authenticated user
        limit: Maximum number of results to return (1-100)
        cursor: Optional pagination cursor
        
    Returns:
        Liked posts
    """
    return get_liked_posts(ctx, handle, limit, cursor)


@mcp.tool()
def like_post_tool(
    ctx: Context,
    uri: str,
    cid: str,
) -> Dict:
    """Like a post.
    
    Args:
        ctx: MCP context
        uri: URI of the post to like
        cid: CID of the post to like
        
    Returns:
        Status of the like operation
    """
    return like_post(ctx, uri, cid)


@mcp.tool()
def create_post_tool(
    ctx: Context,
    text: str,
    reply_to: Optional[Dict] = None,
    images: Optional[List[Dict]] = None,
    quotes: Optional[Dict] = None,
    links: Optional[List[Dict]] = None,
) -> Dict:
    """Create a new post.
    
    Args:
        ctx: MCP context
        text: Text content of the post
        reply_to: Optional reply information dict with keys uri and cid
        images: Optional list of image dicts with keys image_data (base64) and alt
        quotes: Optional quote information dict with keys uri and cid
        links: Optional list of link information dicts
        
    Returns:
        Status of the post creation
    """
    return create_post(ctx, text, reply_to, images, quotes, links)


@mcp.tool()
def follow_user_tool(
    ctx: Context,
    handle: str,
) -> Dict:
    """Follow a user.
    
    Args:
        ctx: MCP context
        handle: Handle of the user to follow
        
    Returns:
        Status of the follow operation
    """
    return follow_user(ctx, handle)


@mcp.tool()
def search_posts_tool(
    ctx: Context,
    query: str,
    limit: int = 25,
    cursor: Optional[str] = None,
    sort: str = "top",
) -> Dict:
    """Search for posts with a given query.
    
    Args:
        ctx: MCP context
        query: Search query
        limit: Maximum number of results to return (1-100)
        cursor: Optional pagination cursor
        sort: Sort order, either "top" or "latest"
        
    Returns:
        Search results
    """
    return search_posts(ctx, query, limit, cursor, sort)


@mcp.tool()
def search_people_tool(
    ctx: Context,
    query: str,
    limit: int = 25,
    cursor: Optional[str] = None,
) -> Dict:
    """Search for people with a given query.
    
    Args:
        ctx: MCP context
        query: Search query
        limit: Maximum number of results to return (1-100)
        cursor: Optional pagination cursor
        
    Returns:
        Search results
    """
    return search_people(ctx, query, limit, cursor)


@mcp.tool()
def search_feeds_tool(
    ctx: Context,
    query: str,
    limit: int = 25,
    cursor: Optional[str] = None,
) -> Dict:
    """Search for feeds with a given query.
    
    Args:
        ctx: MCP context
        query: Search query
        limit: Maximum number of results to return (1-100)
        cursor: Optional pagination cursor
        
    Returns:
        Search results
    """
    return search_feeds(ctx, query, limit, cursor)


@mcp.tool()
def get_post_thread_tool(
    ctx: Context,
    uri: str,
    depth: int = 6,
    parent_height: int = 80,
) -> Dict:
    """Get a thread from a post URI.
    
    Args:
        ctx: MCP context
        uri: URI of the post to get the thread for
        depth: Maximum depth to retrieve (for replies)
        parent_height: Maximum height to retrieve (for parents)
        
    Returns:
        Thread data
    """
    return get_post_thread(ctx, uri, depth, parent_height)


@mcp.tool()
def convert_url_to_uri_tool(
    ctx: Context,
    url: str,
) -> Dict:
    """Convert a Bluesky web URL to an AT URI.
    
    Args:
        ctx: MCP context
        url: URL to convert (e.g., https://bsky.app/profile/username.bsky.social/post/abcdef)
        
    Returns:
        AT URI
    """
    return convert_url_to_uri(ctx, url)


@mcp.tool()
def get_trends_tool(
    ctx: Context,
) -> Dict:
    """Get current trending topics on Bluesky.
    
    Args:
        ctx: MCP context
        
    Returns:
        Trending topics with post counts
    """
    return get_trends(ctx)


@mcp.tool()
def get_pinned_feeds_tool(
    ctx: Context,
) -> Dict:
    """Get pinned feeds from user preferences.
    
    Args:
        ctx: MCP context
        
    Returns:
        Pinned feeds
    """
    return get_pinned_feeds(ctx)


if __name__ == "__main__":
    mcp.run()
