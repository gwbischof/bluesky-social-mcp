"""Bluesky MCP Server.

A single-file implementation with all tool logic directly embedded.
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass
import base64
import functools
import re
from io import BytesIO
import os
import asyncio
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, TypeVar, Union

from atproto import Client
import mcp.server.stdio
from mcp.server.fastmcp import Context, FastMCP

from authentication import BlueskyAuthManager


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

# Type variable for function return types
F = TypeVar("F", bound=Callable[..., Any])


def require_auth(func: F) -> F:
    """Decorator to require authentication for a tool.

    If not authenticated, attempts to authenticate using environment variables.

    Args:
        func: The function to decorate

    Returns:
        Decorated function
    """

    @functools.wraps(func)
    def wrapper(ctx: Context, *args, **kwargs):
        auth_manager = ctx.request_context.lifespan_context.auth_manager

        # Check if already authenticated
        if not auth_manager.is_authenticated(ctx):
            # Try to authenticate using environment variables
            success, error = auth_manager.authenticate_from_env(ctx)

            # If environment authentication failed, return error
            if not success:
                return {
                    "status": "error",
                    "message": f"Authentication required. {error}",
                }

        # Now call the original function
        return func(ctx, *args, **kwargs)

    return wrapper


@mcp.tool()
def check_environment_variables(ctx: Context) -> dict:
    """Check if Bluesky environment variables are set.

    Args:
        ctx: MCP context

    Returns:
        Status of environment variables
    """
    handle = os.environ.get("BLUESKY_IDENTIFIER")
    password = os.environ.get("BLUESKY_APP_PASSWORD")
    service_url = os.environ.get("BLUESKY_SERVICE_URL")

    status = {
        "BLUESKY_IDENTIFIER": "✅ Set" if handle else "❌ Not set",
        "BLUESKY_APP_PASSWORD": "✅ Set" if password else "❌ Not set",
        "BLUESKY_SERVICE_URL": (
            f"✅ Set to {service_url}"
            if service_url
            else "⚠️ Not set (will default to https://bsky.social)"
        ),
    }

    if handle and password:
        return {
            "status": "success",
            "message": "Required environment variables are correctly set",
            "variables": status,
        }
    else:
        return {
            "status": "error",
            "message": "Missing required environment variables",
            "variables": status,
        }


@mcp.tool()
def check_auth_status(ctx: Context) -> dict:
    """Check if the current session is authenticated.

    Authentication happens automatically using environment variables:
    - BLUESKY_IDENTIFIER: Required - your Bluesky handle
    - BLUESKY_APP_PASSWORD: Required - your app password
    - BLUESKY_SERVICE_URL: Optional - defaults to https://bsky.social

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
        # Check if environment variables are set
        handle = os.environ.get("BLUESKY_IDENTIFIER")
        password = os.environ.get("BLUESKY_APP_PASSWORD")
        service_url = os.environ.get("BLUESKY_SERVICE_URL", "https://bsky.social")

        if handle and password:
            return {
                "status": "not_authenticated",
                "message": f"Environment variables are set but authentication hasn't happened yet. Will connect to {service_url} when you use any tool.",
            }
        else:
            return {
                "status": "not_authenticated",
                "message": "Required environment variables BLUESKY_IDENTIFIER and/or BLUESKY_APP_PASSWORD are not set.",
            }


@mcp.tool()
@require_auth
def get_profile(ctx: Context, handle: Optional[str] = None) -> Dict:
    """Get a user profile.

    Args:
        ctx: MCP context
        handle: Optional handle to get profile for. If None, gets the authenticated user

    Returns:
        Profile data
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        # If no handle provided, get authenticated user's profile
        if not handle:
            handle = client.me.handle

        profile_response = client.app.bsky.actor.get_profile({"actor": handle})
        profile = profile_response.dict()
        return {"status": "success", "profile": profile}
    except Exception as e:
        error_msg = f"Failed to get profile: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def get_follows(
    ctx: Context,
    handle: Optional[str] = None,
    limit: Union[int, str] = 50,
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
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        # If no handle provided, get authenticated user's follows
        if not handle:
            handle = client.me.handle

        params = {"actor": handle, "limit": max(1, min(100, limit))}
        if cursor:
            params["cursor"] = cursor

        follows_response = client.app.bsky.graph.get_follows(params)
        follows = follows_response.dict()
        return {"status": "success", "follows": follows}
    except Exception as e:
        error_msg = f"Failed to get follows: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def get_followers(
    ctx: Context,
    handle: Optional[str] = None,
    limit: Union[int, str] = 50,
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
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        # If no handle provided, get authenticated user's followers
        if not handle:
            handle = client.me.handle

        params = {"actor": handle, "limit": max(1, min(100, limit))}
        if cursor:
            params["cursor"] = cursor

        followers_response = client.app.bsky.graph.get_followers(params)
        followers = followers_response.dict()
        return {"status": "success", "followers": followers}
    except Exception as e:
        error_msg = f"Failed to get followers: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def get_timeline_posts(
    ctx: Context,
    limit: Union[int, str] = 50,
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
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        params = {"limit": max(1, min(100, limit))}
        if cursor:
            params["cursor"] = cursor
        if algorithm:
            params["algorithm"] = algorithm

        timeline_response = client.app.bsky.feed.get_timeline(params)
        timeline = timeline_response.dict()
        return {"status": "success", "timeline": timeline}
    except Exception as e:
        error_msg = f"Failed to get timeline: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def get_feed_posts(
    ctx: Context,
    feed: str,
    limit: Union[int, str] = 50,
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
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        params = {"feed": feed, "limit": max(1, min(100, limit))}
        if cursor:
            params["cursor"] = cursor

        feed_response = client.app.bsky.feed.get_feed(params)
        feed_data = feed_response.dict()
        return {"status": "success", "feed": feed_data}
    except Exception as e:
        error_msg = f"Failed to get feed: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def get_list_posts(
    ctx: Context,
    list_uri: str,
    limit: Union[int, str] = 50,
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
    auth_manager = ctx.request_context.lifespan_context.auth_manager

    client = auth_manager.get_client(ctx)

    try:
        params = {"list": list_uri, "limit": max(1, min(100, limit))}
        if cursor:
            params["cursor"] = cursor

        list_response = client.app.bsky.feed.get_list_feed(params)
        list_data = list_response.dict()
        return {"status": "success", "list_feed": list_data}
    except Exception as e:
        error_msg = f"Failed to get list feed: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def get_user_posts(
    ctx: Context,
    handle: Optional[str] = None,
    limit: Union[int, str] = 50,
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
    auth_manager = ctx.request_context.lifespan_context.auth_manager

    client = auth_manager.get_client(ctx)

    try:
        # If no handle provided, get authenticated user's posts
        if not handle:
            handle = client.me.handle

        params = {"actor": handle, "limit": max(1, min(100, limit))}
        if cursor:
            params["cursor"] = cursor
        if filter:
            params["filter"] = filter

        author_feed_response = client.app.bsky.feed.get_author_feed(params)
        author_feed = author_feed_response.dict()
        return {"status": "success", "author_feed": author_feed}
    except Exception as e:
        error_msg = f"Failed to get user posts: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def get_liked_posts(
    ctx: Context,
    handle: Optional[str] = None,
    limit: Union[int, str] = 50,
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
    auth_manager = ctx.request_context.lifespan_context.auth_manager

    client = auth_manager.get_client(ctx)

    try:
        # If no handle provided, get authenticated user's likes
        if not handle:
            handle = client.me.handle

        params = {"actor": handle, "limit": max(1, min(100, limit))}
        if cursor:
            params["cursor"] = cursor

        likes_response = client.app.bsky.feed.get_actor_likes(params)
        likes = likes_response.dict()
        return {"status": "success", "likes": likes}
    except Exception as e:
        error_msg = f"Failed to get liked posts: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def like_post(
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
    auth_manager = ctx.request_context.lifespan_context.auth_manager

    client = auth_manager.get_client(ctx)

    try:
        like_response = client.like(uri, cid)
        return {
            "status": "success",
            "message": "Post liked successfully",
            "like_uri": like_response.uri,
            "like_cid": like_response.cid,
        }
    except Exception as e:
        error_msg = f"Failed to like post: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def create_post(
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
    auth_manager = ctx.request_context.lifespan_context.auth_manager

    client = auth_manager.get_client(ctx)

    try:
        # Basic text post
        post_params = {"text": text}

        # Handle reply
        if reply_to:
            reply_data: Dict[str, Dict[str, Any]] = {}

            if reply_to.get("root_uri") and reply_to.get("root_cid"):
                root_uri = str(reply_to.get("root_uri", ""))
                root_cid = str(reply_to.get("root_cid", ""))
                reply_data["root"] = {"uri": root_uri, "cid": root_cid}

            if reply_to.get("uri") and reply_to.get("cid"):
                uri = str(reply_to.get("uri", ""))
                cid = str(reply_to.get("cid", ""))
                reply_data["parent"] = {"uri": uri, "cid": cid}

            # Need to cast to Any to avoid type error
            post_params["reply"] = reply_data  # type: ignore

        # Handle images
        if images:
            image_uploads: List[Dict[str, Any]] = []
            for img_data in images:
                if "image_data" in img_data and "alt" in img_data:
                    # Assuming image_data is base64 encoded
                    img_bytes = BytesIO(base64.b64decode(img_data["image_data"]))
                    upload = client.upload_blob(img_bytes.read())

                    image_uploads.append({"image": upload.blob, "alt": img_data["alt"]})

            if image_uploads:
                post_params["images"] = image_uploads  # type: ignore

        # Handle quote post
        if quotes and "uri" in quotes and "cid" in quotes:
            quote_uri = str(quotes["uri"])
            quote_cid = str(quotes["cid"])
            post_params["quote"] = {"uri": quote_uri, "cid": quote_cid}  # type: ignore

        # Create the post
        post_response = client.send_post(**post_params)
        return {
            "status": "success",
            "message": "Post created successfully",
            "post_uri": post_response.uri,
            "post_cid": post_response.cid,
        }
    except Exception as e:
        error_msg = f"Failed to create post: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def follow_user(
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
    auth_manager = ctx.request_context.lifespan_context.auth_manager

    client = auth_manager.get_client(ctx)

    try:
        # First resolve the handle to a DID
        resolved = client.resolve_handle(handle)
        did = resolved.did

        # Now follow the user
        follow_response = client.follow(did)
        return {
            "status": "success",
            "message": f"Now following {handle}",
            "follow_uri": follow_response.uri,
        }
    except Exception as e:
        error_msg = f"Failed to follow user: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def search_posts(
    ctx: Context,
    query: str,
    limit: Union[int, str] = 25,
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
    auth_manager = ctx.request_context.lifespan_context.auth_manager

    client = auth_manager.get_client(ctx)

    try:
        params = {"q": query, "limit": max(1, min(100, limit))}
        if cursor:
            params["cursor"] = cursor

        # The bluesky API only supports "recent" or default (relevance)
        if sort.lower() == "latest":
            params["sort"] = "recent"

        search_response = client.app.bsky.feed.search_posts(params)
        search_results = search_response.dict()
        return {"status": "success", "search_results": search_results}
    except Exception as e:
        error_msg = f"Failed to search posts: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def search_people(
    ctx: Context,
    query: str,
    limit: Union[int, str] = 25,
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
    auth_manager = ctx.request_context.lifespan_context.auth_manager

    client = auth_manager.get_client(ctx)

    try:
        params = {"term": query, "limit": max(1, min(100, limit))}
        if cursor:
            params["cursor"] = cursor

        search_response = client.app.bsky.actor.search_actors(params)
        search_results = search_response.dict()
        return {"status": "success", "search_results": search_results}
    except Exception as e:
        error_msg = f"Failed to search people: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def search_feeds(
    ctx: Context,
    query: str,
    limit: Union[int, str] = 25,
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
    auth_manager = ctx.request_context.lifespan_context.auth_manager

    client = auth_manager.get_client(ctx)

    try:
        params = {"query": query, "limit": max(1, min(100, limit))}
        if cursor:
            params["cursor"] = cursor

        search_response = client.app.bsky.feed.search_feeds(params)
        search_results = search_response.dict()
        return {"status": "success", "search_results": search_results}
    except Exception as e:
        error_msg = f"Failed to search feeds: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def get_post_thread(
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
    auth_manager = ctx.request_context.lifespan_context.auth_manager

    client = auth_manager.get_client(ctx)

    try:
        params = {
            "uri": uri,
            "depth": max(0, min(1000, depth)),
            "parentHeight": max(0, min(1000, parent_height)),
        }

        thread_response = client.app.bsky.feed.get_post_thread(params)
        thread = thread_response.dict()
        return {"status": "success", "thread": thread}
    except Exception as e:
        error_msg = f"Failed to get post thread: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
def convert_url_to_uri(
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
    try:
        # Extract the key components from the URL
        # Handle post URLs
        post_pattern = r"https?://(?:www\.)?bsky\.app/profile/([^/]+)/post/([^/]+)"
        post_match = re.match(post_pattern, url)

        if post_match:
            handle = post_match.group(1)
            post_id = post_match.group(2)

            auth_manager = ctx.request_context.lifespan_context.auth_manager
            client = None

            # If authenticated, use the client
            if auth_manager.is_authenticated(ctx):
                client = auth_manager.get_client(ctx)
            else:
                # Create a temporary non-authenticated client
                client = Client()

            # Resolve handle to DID
            resolved = client.resolve_handle(handle)
            did = resolved.did

            # Construct the AT URI
            at_uri = f"at://{did}/app.bsky.feed.post/{post_id}"
            return {"status": "success", "uri": at_uri}

        # Handle profile URLs
        profile_pattern = r"https?://(?:www\.)?bsky\.app/profile/([^/]+)"
        profile_match = re.match(profile_pattern, url)

        if profile_match:
            handle = profile_match.group(1)

            auth_manager = ctx.request_context.lifespan_context.auth_manager
            client = None

            # If authenticated, use the client
            if auth_manager.is_authenticated(ctx):
                client = auth_manager.get_client(ctx)
            else:
                # Create a temporary non-authenticated client
                client = Client()

            # Resolve handle to DID
            resolved = client.resolve_handle(handle)
            did = resolved.did

            # Return the DID
            return {"status": "success", "uri": did}

        return {"status": "error", "message": "Unsupported URL format"}
    except Exception as e:
        error_msg = f"Failed to convert URL to URI: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def get_trends(
    ctx: Context,
) -> Dict:
    """Get current trending topics on Bluesky.

    Args:
        ctx: MCP context

    Returns:
        Trending topics with post counts
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager

    client = auth_manager.get_client(ctx)

    try:
        # Get popular posts
        popular_params = {"limit": 100}
        popular_response = client.app.bsky.unspecced.get_popular(popular_params)
        popular_posts = popular_response.dict()

        # Extract and count hashtags
        hashtags: Dict[str, int] = {}
        feed_items = popular_posts.get("feed", [])

        for post in feed_items:
            if "post" in post and "record" in post["post"]:
                record = post["post"]["record"]
                if "text" in record:
                    # Extract hashtags with regex
                    text = record["text"]
                    if isinstance(text, str):
                        tags = re.findall(r"#(\w+)", text)
                        for tag in tags:
                            tag_lower = tag.lower()
                            if tag_lower in hashtags:
                                hashtags[tag_lower] += 1
                            else:
                                hashtags[tag_lower] = 1

        # Sort by count
        sorted_tags = [
            {"tag": tag, "count": count}
            for tag, count in sorted(hashtags.items(), key=lambda x: x[1], reverse=True)
        ]

        return {
            "status": "success",
            "trends": sorted_tags[:20],  # Return top 20 trending tags
        }
    except Exception as e:
        error_msg = f"Failed to get trends: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def get_pinned_feeds(
    ctx: Context,
) -> Dict:
    """Get pinned feeds from user preferences.

    Args:
        ctx: MCP context

    Returns:
        Pinned feeds
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager

    client = auth_manager.get_client(ctx)

    try:
        # Get user preferences
        prefs_response = client.app.bsky.actor.get_preferences({})

        # Find pinned feeds in preferences
        pinned_feeds = []
        for pref in prefs_response.preferences:
            if pref.type == "app.bsky.actor.defs#savedFeedsPref":
                if hasattr(pref, "saved"):
                    pinned_feeds = pref.saved
                    break

        # If feeds are found, fetch details for each one
        feed_details = []
        if pinned_feeds:
            for feed_uri in pinned_feeds:
                try:
                    # Extract the feed generator DID and feed name
                    feed_match = re.match(
                        r"at://([^/]+)/app\.bsky\.feed\.generator/([^/]+)", feed_uri
                    )

                    if feed_match:
                        # Extract feed components (captured but not used directly)
                        feed_did: str = feed_match.group(1)
                        feed_id: str = feed_match.group(2)

                        # Variables are used indirectly through feed_uri in the API call below
                        _ = feed_did, feed_id  # Mark as used to satisfy linters

                        # Get feed info
                        feed_info = client.app.bsky.feed.get_feed_generator(
                            {"feed": feed_uri}
                        )

                        feed_details.append({"uri": feed_uri, "info": feed_info.dict()})
                except Exception as feed_err:
                    # Skip failed feeds
                    ctx.error(
                        f"Failed to get feed details for {feed_uri}: {str(feed_err)}"
                    )
                    continue

        return {"status": "success", "pinned_feeds": feed_details}
    except Exception as e:
        error_msg = f"Failed to get pinned feeds: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


# Support for running as a stdio server
async def run_stdio_server():
    """Run the server with stdio communication."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await mcp.serve_stdio(read_stream, write_stream)


# Main entry point
if __name__ == "__main__":
    # Support both HTTP and stdio
    # If run directly, we check if stdin is a TTY
    if os.isatty(0):
        # Run as HTTP server if stdin is a TTY
        mcp.run()
    else:
        # Run as stdio server if stdin is not a TTY (piped)
        asyncio.run(run_stdio_server())