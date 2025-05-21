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
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, TypeVar, Union

from atproto import Client
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
    name="bluesky-social",
    lifespan=app_lifespan,
    dependencies=["atproto", "mcp"],
)

def require_auth(func):
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
def unlike_post(
    ctx: Context,
    uri: str,
    cid: str,
) -> Dict:
    """Unlike a previously liked post.

    Args:
        ctx: MCP context
        uri: URI of the post to unlike
        cid: CID of the post to unlike

    Returns:
        Status of the unlike operation
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        client.unlike(uri, cid)
        return {
            "status": "success",
            "message": "Post unliked successfully",
        }
    except Exception as e:
        error_msg = f"Failed to unlike post: {str(e)}"
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
def repost_post(
    ctx: Context,
    uri: str,
    cid: str,
) -> Dict:
    """Repost another user's post.

    Args:
        ctx: MCP context
        uri: URI of the post to repost
        cid: CID of the post to repost

    Returns:
        Status of the repost operation
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        repost_response = client.repost(uri, cid)
        return {
            "status": "success",
            "message": "Post reposted successfully",
            "repost_uri": repost_response.uri,
            "repost_cid": repost_response.cid,
        }
    except Exception as e:
        error_msg = f"Failed to repost: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def unrepost_post(
    ctx: Context,
    uri: str,
    cid: str,
) -> Dict:
    """Remove a repost of another user's post.

    Args:
        ctx: MCP context
        uri: URI of the post to unrepost
        cid: CID of the post to unrepost

    Returns:
        Status of the unrepost operation
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        client.unrepost(uri, cid)
        return {
            "status": "success",
            "message": "Post unreposted successfully",
        }
    except Exception as e:
        error_msg = f"Failed to unrepost: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def get_likes(
    ctx: Context,
    uri: str,
    cid: Optional[str] = None,
    limit: Union[int, str] = 50,
    cursor: Optional[str] = None,
) -> Dict:
    """Get likes for a post.

    Args:
        ctx: MCP context
        uri: URI of the post to get likes for
        cid: Optional CID of the post (not strictly required)
        limit: Maximum number of results to return (1-100)
        cursor: Optional pagination cursor

    Returns:
        List of likes for the post
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        params = {"uri": uri, "limit": max(1, min(100, limit))}
        if cursor:
            params["cursor"] = cursor
            
        likes_response = client.get_likes(params)
        likes_data = likes_response.dict()
        
        return {"status": "success", "likes": likes_data}
    except Exception as e:
        error_msg = f"Failed to get likes: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def get_reposted_by(
    ctx: Context,
    uri: str,
    cid: Optional[str] = None,
    limit: Union[int, str] = 50,
    cursor: Optional[str] = None,
) -> Dict:
    """Get users who reposted a post.

    Args:
        ctx: MCP context
        uri: URI of the post to get reposts for
        cid: Optional CID of the post (not strictly required)
        limit: Maximum number of results to return (1-100)
        cursor: Optional pagination cursor

    Returns:
        List of users who reposted the post
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        params = {"uri": uri, "limit": max(1, min(100, limit))}
        if cursor:
            params["cursor"] = cursor
            
        reposts_response = client.get_reposted_by(params)
        reposts_data = reposts_response.dict()
        
        return {"status": "success", "reposts": reposts_data}
    except Exception as e:
        error_msg = f"Failed to get reposts: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def send_image(
    ctx: Context,
    text: str,
    image_data: str,
    alt_text: str = "",
    reply_to: Optional[Dict] = None,
) -> Dict:
    """Send a post with a single image.

    Args:
        ctx: MCP context
        text: Text content of the post
        image_data: Base64-encoded image data
        alt_text: Alternative text description for the image
        reply_to: Optional reply information dict with keys uri and cid

    Returns:
        Status of the post creation
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        # Decode base64 image
        try:
            img_bytes = BytesIO(base64.b64decode(image_data))
            image = img_bytes.read()
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to decode image data: {str(e)}",
            }
            
        # Prepare reply parameters if needed
        reply_params = {}
        if reply_to and "uri" in reply_to and "cid" in reply_to:
            reply_params = {
                "reply_to": {
                    "uri": reply_to["uri"],
                    "cid": reply_to["cid"]
                }
            }
            
            # Handle root if provided
            if "root_uri" in reply_to and "root_cid" in reply_to:
                reply_params["reply_to"]["root"] = {
                    "uri": reply_to["root_uri"],
                    "cid": reply_to["root_cid"]
                }
                
        # Send the post with image
        post_response = client.send_image(
            text=text,
            image=image,
            image_alt=alt_text,
            **reply_params
        )
        
        return {
            "status": "success",
            "message": "Post with image created successfully",
            "post_uri": post_response.uri,
            "post_cid": post_response.cid,
        }
    except Exception as e:
        error_msg = f"Failed to create post with image: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def send_images(
    ctx: Context,
    text: str,
    images: List[Dict[str, str]],
    reply_to: Optional[Dict] = None,
) -> Dict:
    """Send a post with multiple images (up to 4).

    Args:
        ctx: MCP context
        text: Text content of the post
        images: List of image dicts, each with "image_data" (base64) and "alt" keys
        reply_to: Optional reply information dict with keys uri and cid

    Returns:
        Status of the post creation
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        # Verify we have 1-4 images
        if not images:
            return {
                "status": "error",
                "message": "At least one image is required",
            }
        
        if len(images) > 4:
            return {
                "status": "error",
                "message": "Maximum of 4 images allowed",
            }
            
        # Process images
        image_bytes_list = []
        alt_texts = []
        
        for img in images:
            if "image_data" not in img:
                return {
                    "status": "error", 
                    "message": "Each image must contain 'image_data' with base64 encoded content"
                }
                
            # Decode base64 image
            try:
                img_bytes = BytesIO(base64.b64decode(img["image_data"]))
                image_bytes_list.append(img_bytes.read())
                
                # Add alt text
                alt_texts.append(img.get("alt", ""))
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to decode image data: {str(e)}",
                }
                
        # Prepare reply parameters if needed
        reply_params = {}
        if reply_to and "uri" in reply_to and "cid" in reply_to:
            reply_params = {
                "reply_to": {
                    "uri": reply_to["uri"],
                    "cid": reply_to["cid"]
                }
            }
            
            # Handle root if provided
            if "root_uri" in reply_to and "root_cid" in reply_to:
                reply_params["reply_to"]["root"] = {
                    "uri": reply_to["root_uri"],
                    "cid": reply_to["root_cid"]
                }
                
        # Send the post with images
        post_response = client.send_images(
            text=text,
            image=image_bytes_list,
            alt_text=alt_texts,
            **reply_params
        )
        
        return {
            "status": "success",
            "message": "Post with images created successfully",
            "post_uri": post_response.uri,
            "post_cid": post_response.cid,
        }
    except Exception as e:
        error_msg = f"Failed to create post with images: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def send_video(
    ctx: Context,
    text: str,
    video_data: str,
    alt_text: str = "",
    reply_to: Optional[Dict] = None,
) -> Dict:
    """Send a post with a video.

    Args:
        ctx: MCP context
        text: Text content of the post
        video_data: Base64-encoded video data
        alt_text: Alternative text description for the video
        reply_to: Optional reply information dict with keys uri and cid

    Returns:
        Status of the post creation
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        # Decode base64 video
        try:
            video_bytes = BytesIO(base64.b64decode(video_data))
            video = video_bytes.read()
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to decode video data: {str(e)}",
            }
            
        # Prepare reply parameters if needed
        reply_params = {}
        if reply_to and "uri" in reply_to and "cid" in reply_to:
            reply_params = {
                "reply_to": {
                    "uri": reply_to["uri"],
                    "cid": reply_to["cid"]
                }
            }
            
            # Handle root if provided
            if "root_uri" in reply_to and "root_cid" in reply_to:
                reply_params["reply_to"]["root"] = {
                    "uri": reply_to["root_uri"],
                    "cid": reply_to["root_cid"]
                }
                
        # Send the post with video
        post_response = client.send_video(
            text=text,
            video=video,
            video_alt=alt_text,
            **reply_params
        )
        
        return {
            "status": "success",
            "message": "Post with video created successfully",
            "post_uri": post_response.uri,
            "post_cid": post_response.cid,
        }
    except Exception as e:
        error_msg = f"Failed to create post with video: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def delete_post(
    ctx: Context,
    uri: str,
) -> Dict:
    """Delete a post created by the authenticated user.

    Args:
        ctx: MCP context
        uri: URI of the post to delete

    Returns:
        Status of the delete operation
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        # Extract the record key from the URI
        from atproto import AtUri
        post_uri = AtUri.from_str(uri)
        
        # Verify this is a post from the authenticated user
        if post_uri.did != client.me.did:
            return {
                "status": "error",
                "message": "You can only delete your own posts",
            }
            
        # Delete the post
        client.delete_post(uri)
        
        return {
            "status": "success",
            "message": "Post deleted successfully",
        }
    except Exception as e:
        error_msg = f"Failed to delete post: {str(e)}"
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
def block_user(
    ctx: Context,
    handle: str,
) -> Dict:
    """Block a user.

    Args:
        ctx: MCP context
        handle: Handle of the user to block

    Returns:
        Status of the block operation
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        # First resolve the handle to a DID
        resolved = client.resolve_handle(handle)
        did = resolved.did

        # Now block the user
        block_response = client.app.bsky.graph.block.create(
            client.me.did,
            {"subject": did, "createdAt": client.get_current_time_iso()},
        )
        
        return {
            "status": "success",
            "message": f"Blocked user @{handle}",
            "block_uri": block_response.uri,
        }
    except Exception as e:
        error_msg = f"Failed to block user: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def unblock_user(
    ctx: Context,
    handle: str,
) -> Dict:
    """Unblock a previously blocked user.

    Args:
        ctx: MCP context
        handle: Handle of the user to unblock

    Returns:
        Status of the unblock operation
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        # First resolve the handle to a DID
        resolved = client.resolve_handle(handle)
        did = resolved.did

        # Find the block record
        blocks = client.app.bsky.graph.block.list(client.me.did, limit=100)
        
        block_record = None
        for uri, block in blocks.records.items():
            if block.subject == did:
                block_record = uri
                break
        
        if not block_record:
            return {
                "status": "error",
                "message": f"No block record found for @{handle}",
            }
        
        # Extract the rkey from the AT URI
        from atproto import AtUri
        rkey = AtUri.from_str(block_record).rkey
        
        # Delete the block
        client.app.bsky.graph.block.delete(client.me.did, rkey)
        
        return {
            "status": "success",
            "message": f"Unblocked user @{handle}",
        }
    except Exception as e:
        error_msg = f"Failed to unblock user: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def get_blocks(
    ctx: Context,
    limit: Union[int, str] = 50,
    cursor: Optional[str] = None,
) -> Dict:
    """Get list of users blocked by the authenticated user.

    Args:
        ctx: MCP context
        limit: Maximum number of results to return (1-100)
        cursor: Optional pagination cursor

    Returns:
        List of blocked users
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        params = {"limit": max(1, min(100, limit))}
        if cursor:
            params["cursor"] = cursor
            
        blocks_response = client.app.bsky.graph.block.list(client.me.did, **params)
        
        # Extract and enhance the block records
        blocks_data = []
        for uri, block in blocks_response.records.items():
            try:
                # Try to get profile info for each blocked user
                profile = client.app.bsky.actor.get_profile({"actor": block.subject}).dict()
                blocks_data.append({
                    "uri": uri,
                    "did": block.subject,
                    "profile": profile,
                })
            except Exception:
                # If profile fetch fails, just include the basic info
                blocks_data.append({
                    "uri": uri,
                    "did": block.subject,
                })
        
        result = {
            "blocks": blocks_data,
            "cursor": blocks_response.cursor if hasattr(blocks_response, "cursor") else None,
        }
        
        return {"status": "success", "blocks_data": result}
    except Exception as e:
        error_msg = f"Failed to get blocks: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def mute_user(
    ctx: Context,
    handle: str,
) -> Dict:
    """Mute a user.

    Args:
        ctx: MCP context
        handle: Handle of the user to mute

    Returns:
        Status of the mute operation
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        # First resolve the handle to a DID
        resolved = client.resolve_handle(handle)
        did = resolved.did

        # Mute the user
        client.app.bsky.graph.mute_actor({"actor": did})
        
        return {
            "status": "success",
            "message": f"Muted user @{handle}",
        }
    except Exception as e:
        error_msg = f"Failed to mute user: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def unmute_user(
    ctx: Context,
    handle: str,
) -> Dict:
    """Unmute a previously muted user.

    Args:
        ctx: MCP context
        handle: Handle of the user to unmute

    Returns:
        Status of the unmute operation
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        # First resolve the handle to a DID
        resolved = client.resolve_handle(handle)
        did = resolved.did

        # Unmute the user
        client.app.bsky.graph.unmute_actor({"actor": did})
        
        return {
            "status": "success",
            "message": f"Unmuted user @{handle}",
        }
    except Exception as e:
        error_msg = f"Failed to unmute user: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def get_mutes(
    ctx: Context,
    limit: Union[int, str] = 50,
    cursor: Optional[str] = None,
) -> Dict:
    """Get list of users muted by the authenticated user.

    Args:
        ctx: MCP context
        limit: Maximum number of results to return (1-100)
        cursor: Optional pagination cursor

    Returns:
        List of muted users
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        params = {"limit": max(1, min(100, limit))}
        if cursor:
            params["cursor"] = cursor
            
        mutes_response = client.app.bsky.graph.get_mutes(params)
        mutes_data = mutes_response.dict()
        
        return {"status": "success", "mutes": mutes_data}
    except Exception as e:
        error_msg = f"Failed to get mutes: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def get_notifications(
    ctx: Context,
    limit: Union[int, str] = 50,
    cursor: Optional[str] = None,
    seen_at: Optional[str] = None,
    filter: Optional[str] = None,
) -> Dict:
    """Get notifications for the authenticated user.

    Args:
        ctx: MCP context
        limit: Maximum number of results to return (1-100)
        cursor: Optional pagination cursor
        seen_at: RFC3339 timestamp to mark notifications as seen up to
        filter: Optional filter for notification type ('mentions', 'replies', 'quotes', 'reposts', 'follows', 'likes')

    Returns:
        List of notifications
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        params = {"limit": max(1, min(100, limit))}
        if cursor:
            params["cursor"] = cursor
        if seen_at:
            params["seenAt"] = seen_at

        # Handle filter types
        valid_filters = {'mentions', 'replies', 'quotes', 'reposts', 'follows', 'likes'}
        if filter and filter in valid_filters:
            # Only include if it's a valid filter
            params["filter"] = filter
            
        notifications_response = client.app.bsky.notification.list_notifications(params)
        notifications_data = notifications_response.dict()
        
        return {"status": "success", "notifications": notifications_data}
    except Exception as e:
        error_msg = f"Failed to get notifications: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def count_unread_notifications(ctx: Context) -> Dict:
    """Count unread notifications for the authenticated user.

    Args:
        ctx: MCP context

    Returns:
        Count of unread notifications
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        count_response = client.app.bsky.notification.get_unread_count({})
        
        return {
            "status": "success",
            "count": count_response.count,
            "last_seen_at": getattr(count_response, "last_seen", None),
        }
    except Exception as e:
        error_msg = f"Failed to count unread notifications: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def mark_notifications_seen(ctx: Context) -> Dict:
    """Mark all notifications as seen.

    Args:
        ctx: MCP context

    Returns:
        Status of the operation
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        # Get current time as ISO string
        timestamp = client.get_current_time_iso()
        
        # Mark notifications as seen
        client.app.bsky.notification.update_seen({"seenAt": timestamp})
        
        return {
            "status": "success",
            "message": "Notifications marked as seen",
            "seen_at": timestamp,
        }
    except Exception as e:
        error_msg = f"Failed to mark notifications as seen: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
@require_auth
def get_notification_preferences(ctx: Context) -> Dict:
    """Get notification preferences for the authenticated user.

    Args:
        ctx: MCP context

    Returns:
        Notification preferences
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    client = auth_manager.get_client(ctx)

    try:
        # Get user preferences
        prefs_response = client.app.bsky.actor.get_preferences({})

        # Extract notification preferences
        notification_prefs = {}
        for pref in prefs_response.preferences:
            # Look for notification-specific preferences
            if pref.type == "app.bsky.actor.defs#notificationPref":
                notification_prefs = pref.dict()
                break
        
        # If no notification preferences found, return empty default
        if not notification_prefs:
            notification_prefs = {"enabled": True}
        
        return {
            "status": "success",
            "preferences": notification_prefs,
        }
    except Exception as e:
        error_msg = f"Failed to get notification preferences: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@mcp.tool()
def resolve_handle(
    ctx: Context,
    handle: str,
) -> Dict:
    """Resolve a handle to a DID.

    This tool does not require authentication and can be used to convert
    a Bluesky handle (like username.bsky.social) to a DID.

    Args:
        ctx: MCP context
        handle: User handle to resolve

    Returns:
        Resolved DID information
    """
    auth_manager = ctx.request_context.lifespan_context.auth_manager
    
    # Try to use existing client if authenticated
    client = None
    if auth_manager.is_authenticated(ctx):
        client = auth_manager.get_client(ctx)
    else:
        # Create a temporary client instance for unauthenticated use
        from atproto import Client
        client = Client()
    
    try:
        resolved = client.resolve_handle(handle)
        
        return {
            "status": "success",
            "handle": handle,
            "did": resolved.did,
        }
    except Exception as e:
        error_msg = f"Failed to resolve handle: {str(e)}"
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


# Add resource to provide information about available tools
@mcp.resource("info://bluesky-tools")
def get_bluesky_tools_info() -> Dict:
    """Get information about the available Bluesky tools."""
    tools_info = {
        "description": "Bluesky API Tools",
        "version": "0.1.0",
        "auth_requirements": "Most tools require authentication using BLUESKY_IDENTIFIER and BLUESKY_APP_PASSWORD environment variables",
        "categories": {
            "authentication": ["check_environment_variables", "check_auth_status"],
            "profiles": ["get_profile", "get_follows", "get_followers", "follow_user"],
            "posts": ["get_timeline_posts", "get_feed_posts", "get_list_posts", "get_user_posts", "get_liked_posts", "create_post", "like_post", "get_post_thread"],
            "search": ["search_posts", "search_people", "search_feeds"],
            "utilities": ["convert_url_to_uri", "get_trends", "get_pinned_feeds"],
        }
    }
    return tools_info


# Main entry point
if __name__ == "__main__":
    # Auto-detect based on TTY
    transport = "sse" if os.isatty(0) else "stdio"
    mcp.run(transport=transport)
