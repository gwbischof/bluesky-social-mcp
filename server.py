"""Bluesky MCP Server.

A single-file implementation with all tool logic directly embedded.
"""

import base64
from contextlib import asynccontextmanager
from dataclasses import dataclass
import os
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from atproto import Client
from mcp.server.fastmcp import Context, FastMCP

from pathlib import Path

project_root = Path(__file__).parent.parent.absolute()

LOG_FILE = project_root / "custom-mcp.log"


def login() -> Optional[Client]:
    """Login to Bluesky API and return the client.

    Authenticates using environment variables:
    - BLUESKY_IDENTIFIER: The handle (username)
    - BLUESKY_APP_PASSWORD: The app password
    - BLUESKY_SERVICE_URL: The service URL (defaults to "https://bsky.social")

    Returns:
        Authenticated Client instance or None if credentials are not available
    """
    handle = os.environ.get("BLUESKY_IDENTIFIER")
    password = os.environ.get("BLUESKY_APP_PASSWORD")
    service_url = os.environ.get("BLUESKY_SERVICE_URL", "https://bsky.social")

    if not handle or not password:
        return None

    # This is helpful for debugging.
    # print(f"LOGIN {handle=} {service_url=}", file=sys.stderr)

    # Create and authenticate client
    client = Client(service_url)
    client.login(handle, password)
    return client


def get_authenticated_client(ctx: Context) -> Client:
    """Get an authenticated client, creating it lazily if needed.

    Args:
        ctx: MCP context

    Returns:
        Authenticated Client instance

    Raises:
        ValueError: If credentials are not available
    """
    app_context = ctx.request_context.lifespan_context

    # If we already have a client, return it
    if app_context.bluesky_client is not None:
        return app_context.bluesky_client

    # Try to create a new client by calling login again
    client = login()
    if client is None:
        raise ValueError(
            "Authentication required but credentials not available. "
            "Please set BLUESKY_IDENTIFIER and BLUESKY_APP_PASSWORD environment variables."
        )

    # Store it in the context for future use
    app_context.bluesky_client = client
    return client


@dataclass
class AppContext:
    bluesky_client: Optional[Client]


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with typed context.

    Args:
        server: The FastMCP server instance

    Yields:
        ServerContext with initialized resources
    """
    # Initialize resources - login may return None if credentials not available
    bluesky_client = login()
    try:
        yield AppContext(bluesky_client=bluesky_client)
    finally:
        # TODO: Add a logout here.
        pass


# Create MCP server
mcp = FastMCP(
    "bluesky-social",
    lifespan=app_lifespan,
    dependencies=["atproto", "mcp"],
)


@mcp.tool()
def check_auth_status(ctx: Context) -> str:
    """Check if the current session is authenticated.

    Authentication happens automatically using environment variables:
    - BLUESKY_IDENTIFIER: Required - your Bluesky handle
    - BLUESKY_APP_PASSWORD: Required - your app password
    - BLUESKY_SERVICE_URL: Optional - defaults to https://bsky.social

    Returns:
        Authentication status
    """
    try:
        bluesky_client = get_authenticated_client(ctx)
        return f"Authenticated to {bluesky_client._base_url}"
    except ValueError as e:
        return f"Not authenticated: {str(e)}"


@mcp.tool()
def get_profile(ctx: Context, handle: Optional[str] = None) -> Dict:
    """Get a user profile.

    Args:
        ctx: MCP context
        handle: Optional handle to get profile for. If None, gets the authenticated user

    Returns:
        Profile data
    """
    try:
        bluesky_client = get_authenticated_client(ctx)

        # If no handle provided, get authenticated user's profile
        if not handle:
            handle = bluesky_client.me.handle

        profile_response = bluesky_client.get_profile(handle)
        profile = profile_response.dict()
        return {"status": "success", "profile": profile}
    except Exception as e:
        error_msg = f"Failed to get profile: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
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
    try:
        bluesky_client = get_authenticated_client(ctx)

        # If no handle provided, get authenticated user's follows
        if not handle:
            handle = bluesky_client.me.handle

        # Convert limit to int if it's a string
        if isinstance(limit, str):
            limit = int(limit)
        limit = max(1, min(100, limit))

        # Call get_follows directly with positional arguments as per the client signature
        follows_response = bluesky_client.get_follows(handle, cursor, limit)
        follows_data = follows_response.dict()

        return {"status": "success", "follows": follows_data}
    except Exception as e:
        error_msg = f"Failed to get follows: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
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
    try:
        bluesky_client = get_authenticated_client(ctx)

        # If no handle provided, get authenticated user's followers
        if not handle:
            handle = bluesky_client.me.handle

        # Convert limit to int if it's a string
        if isinstance(limit, str):
            limit = int(limit)
        limit = max(1, min(100, limit))

        # Call get_followers directly with positional arguments as per the client signature
        followers_response = bluesky_client.get_followers(handle, cursor, limit)
        followers_data = followers_response.dict()

        return {"status": "success", "followers": followers_data}
    except Exception as e:
        error_msg = f"Failed to get followers: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
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
    try:
        bluesky_client = get_authenticated_client(ctx)
        like_response = bluesky_client.like(uri, cid)
        return {
            "status": "success",
            "message": "Post liked successfully",
            "like_uri": like_response.uri,
            "like_cid": like_response.cid,
        }
    except Exception as e:
        error_msg = f"Failed to like post: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
def unlike_post(
    ctx: Context,
    like_uri: str,
) -> Dict:
    """Unlike a previously liked post.

    Args:
        ctx: MCP context
        like_uri: URI of the like.

    Returns:
        Status of the unlike operation
    """
    try:
        bluesky_client = get_authenticated_client(ctx)
        bluesky_client.unlike(like_uri)
        return {
            "status": "success",
            "message": "Post unliked successfully",
        }
    except Exception as e:
        error_msg = f"Failed to unlike post: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
def send_post(
    ctx: Context,
    text: str,
    profile_identify: Optional[str] = None,
    reply_to: Optional[Dict[str, Any]] = None,
    embed: Optional[Dict[str, Any]] = None,
    langs: Optional[List[str]] = None,
    facets: Optional[List[Dict[str, Any]]] = None,
) -> Dict:
    """Send a post to Bluesky.

    Args:
        ctx: MCP context
        text: Text content of the post
        profile_identify: Optional handle or DID. Where to send post. If not provided, sends to current profile
        reply_to: Optional reply reference with 'root' and 'parent' containing 'uri' and 'cid'
        embed: Optional embed object (images, external links, records, or video)
        langs: Optional list of language codes used in the post (defaults to ['en'])
        facets: Optional list of rich text facets (mentions, links, etc.)

    Returns:
        Status of the post creation with uri and cid of the created post
    """
    try:
        bluesky_client = get_authenticated_client(ctx)

        # Prepare parameters for send_post
        kwargs: Dict[str, Any] = {"text": text}

        # Add optional parameters if provided
        if profile_identify:
            kwargs["profile_identify"] = profile_identify

        if reply_to:
            kwargs["reply_to"] = reply_to

        if embed:
            kwargs["embed"] = embed

        if langs:
            kwargs["langs"] = langs

        if facets:
            kwargs["facets"] = facets

        # Create the post using the native send_post method
        post_response = bluesky_client.send_post(**kwargs)

        return {
            "status": "success",
            "message": "Post sent successfully",
            "post_uri": post_response.uri,
            "post_cid": post_response.cid,
        }
    except Exception as e:
        error_msg = f"Failed to send post: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
def repost(
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
    try:
        bluesky_client = get_authenticated_client(ctx)
        repost_response = bluesky_client.repost(uri, cid)
        return {
            "status": "success",
            "message": "Post reposted successfully",
            "repost_uri": repost_response.uri,
            "repost_cid": repost_response.cid,
        }
    except Exception as e:
        error_msg = f"Failed to repost: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
def unrepost(
    ctx: Context,
    repost_uri: str,
) -> Dict:
    """Remove a repost of another user's post.

    Args:
        ctx: MCP context
        repost_uri: URI of the repost to remove

    Returns:
        Status of the unrepost operation
    """
    try:
        bluesky_client = get_authenticated_client(ctx)
        success = bluesky_client.unrepost(repost_uri)

        if success:
            return {
                "status": "success",
                "message": "Repost removed successfully",
            }
        else:
            return {
                "status": "error",
                "message": "Failed to remove repost",
            }
    except Exception as e:
        error_msg = f"Failed to unrepost: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
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
    try:
        bluesky_client = get_authenticated_client(ctx)
        params = {"uri": uri, "limit": max(1, min(100, limit))}
        if cursor:
            params["cursor"] = cursor

        likes_response = bluesky_client.get_likes(**params)
        likes_data = likes_response.dict()

        return {"status": "success", "likes": likes_data}
    except Exception as e:
        error_msg = f"Failed to get likes: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
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
    try:
        bluesky_client = get_authenticated_client(ctx)

        # Convert limit to int if it's a string
        if isinstance(limit, str):
            limit = int(limit)
        limit = max(1, min(100, limit))

        # Call get_reposted_by with positional arguments as per the client signature
        reposts_response = bluesky_client.get_reposted_by(uri, cid, cursor, limit)
        reposts_data = reposts_response.dict()

        return {"status": "success", "reposts": reposts_data}
    except Exception as e:
        error_msg = f"Failed to get reposts: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
def get_post(
    ctx: Context,
    post_rkey: str,
    profile_identify: Optional[str] = None,
    cid: Optional[str] = None,
) -> Dict:
    """Get a specific post.

    Args:
        ctx: MCP context
        post_rkey: The record key of the post
        profile_identify: Handle or DID of the post author
        cid: Optional CID of the post

    Returns:
        The requested post
    """
    try:
        bluesky_client = get_authenticated_client(ctx)

        post_response = bluesky_client.get_post(post_rkey, profile_identify, cid)

        # Convert the response to a dictionary
        if hasattr(post_response, "model_dump"):
            post_data = post_response.model_dump()
        else:
            post_data = post_response

        return {"status": "success", "post": post_data}
    except Exception as e:
        error_msg = f"Failed to get post: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
def get_posts(
    ctx: Context,
    uris: List[str],
) -> Dict:
    """Get multiple posts by their URIs.

    Args:
        ctx: MCP context
        uris: List of post URIs to retrieve

    Returns:
        List of requested posts
    """
    try:
        bluesky_client = get_authenticated_client(ctx)

        posts_response = bluesky_client.get_posts(uris)

        # Convert the response to a dictionary
        if hasattr(posts_response, "model_dump"):
            posts_data = posts_response.model_dump()
        else:
            posts_data = posts_response

        return {"status": "success", "posts": posts_data}
    except Exception as e:
        error_msg = f"Failed to get posts: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
def get_timeline(
    ctx: Context,
    algorithm: Optional[str] = None,
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
) -> Dict:
    """Get posts from your home timeline.

    Args:
        ctx: MCP context
        algorithm: Optional algorithm to use for timeline
        cursor: Optional pagination cursor
        limit: Maximum number of results to return

    Returns:
        Timeline feed with posts
    """
    try:
        bluesky_client = get_authenticated_client(ctx)

        timeline_response = bluesky_client.get_timeline(algorithm, cursor, limit)

        # Convert the response to a dictionary
        if hasattr(timeline_response, "model_dump"):
            timeline_data = timeline_response.model_dump()
        else:
            timeline_data = timeline_response

        return {"status": "success", "timeline": timeline_data}
    except Exception as e:
        error_msg = f"Failed to get timeline: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
def get_author_feed(
    ctx: Context,
    actor: str,
    cursor: Optional[str] = None,
    filter: Optional[str] = None,
    limit: Optional[int] = None,
    include_pins: bool = False,
) -> Dict:
    """Get posts from a specific user.

    Args:
        ctx: MCP context
        actor: Handle or DID of the user
        cursor: Optional pagination cursor
        filter: Optional filter for post types
        limit: Maximum number of results to return
        include_pins: Whether to include pinned posts

    Returns:
        Feed with posts from the specified user
    """
    try:
        bluesky_client = get_authenticated_client(ctx)

        feed_response = bluesky_client.get_author_feed(
            actor, cursor, filter, limit, include_pins
        )

        # Convert the response to a dictionary
        if hasattr(feed_response, "model_dump"):
            feed_data = feed_response.model_dump()
        else:
            feed_data = feed_response

        return {"status": "success", "feed": feed_data}
    except Exception as e:
        error_msg = f"Failed to get author feed: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
def get_post_thread(
    ctx: Context,
    uri: str,
    depth: Optional[int] = None,
    parent_height: Optional[int] = None,
) -> Dict:
    """Get a full conversation thread.

    Args:
        ctx: MCP context
        uri: URI of the post to get thread for
        depth: How many levels of replies to include
        parent_height: How many parent posts to include

    Returns:
        Thread with the post and its replies/parents
    """
    try:
        bluesky_client = get_authenticated_client(ctx)

        thread_response = bluesky_client.get_post_thread(uri, depth, parent_height)

        # Convert the response to a dictionary
        if hasattr(thread_response, "model_dump"):
            thread_data = thread_response.model_dump()
        else:
            thread_data = thread_response

        return {"status": "success", "thread": thread_data}
    except Exception as e:
        error_msg = f"Failed to get post thread: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
def resolve_handle(
    ctx: Context,
    handle: str,
) -> Dict:
    """Resolve a handle to a DID.

    Args:
        ctx: MCP context
        handle: User handle to resolve (e.g. "user.bsky.social")

    Returns:
        Resolved DID information
    """
    try:
        bluesky_client = get_authenticated_client(ctx)

        resolved = bluesky_client.resolve_handle(handle)

        # Convert the response to a dictionary
        if hasattr(resolved, "model_dump"):
            resolved_data = resolved.model_dump()
        else:
            resolved_data = resolved

        return {
            "status": "success",
            "handle": handle,
            "did": resolved_data.get("did"),
        }
    except Exception as e:
        error_msg = f"Failed to resolve handle: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
def mute_user(
    ctx: Context,
    actor: str,
) -> Dict:
    """Mute a user.

    Args:
        ctx: MCP context
        actor: Handle or DID of the user to mute

    Returns:
        Status of the mute operation
    """
    try:
        bluesky_client = get_authenticated_client(ctx)

        # The mute method returns a boolean
        success = bluesky_client.mute(actor)

        if success:
            return {
                "status": "success",
                "message": f"Muted user {actor}",
            }
        else:
            return {
                "status": "error",
                "message": "Failed to mute user",
            }
    except Exception as e:
        error_msg = f"Failed to mute user: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
def unmute_user(
    ctx: Context,
    actor: str,
) -> Dict:
    """Unmute a previously muted user.

    Args:
        ctx: MCP context
        actor: Handle or DID of the user to unmute

    Returns:
        Status of the unmute operation
    """
    try:
        bluesky_client = get_authenticated_client(ctx)

        # The unmute method returns a boolean
        success = bluesky_client.unmute(actor)

        if success:
            return {
                "status": "success",
                "message": f"Unmuted user {actor}",
            }
        else:
            return {
                "status": "error",
                "message": "Failed to unmute user",
            }
    except Exception as e:
        error_msg = f"Failed to unmute user: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
def unfollow_user(
    ctx: Context,
    follow_uri: str,
) -> Dict:
    """Unfollow a user.

    Args:
        ctx: MCP context
        follow_uri: URI of the follow record to delete

    Returns:
        Status of the unfollow operation
    """
    try:
        bluesky_client = get_authenticated_client(ctx)

        # The unfollow method returns a boolean
        success = bluesky_client.unfollow(follow_uri)

        if success:
            return {
                "status": "success",
                "message": "Successfully unfollowed user",
            }
        else:
            return {
                "status": "error",
                "message": "Failed to unfollow user",
            }
    except Exception as e:
        error_msg = f"Failed to unfollow user: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
def send_image(
    ctx: Context,
    text: str,
    image_data: str,
    image_alt: str,
    profile_identify: Optional[str] = None,
    reply_to: Optional[Dict[str, Any]] = None,
    langs: Optional[List[str]] = None,
    facets: Optional[List[Dict[str, Any]]] = None,
) -> Dict:
    """Send a post with a single image.

    Args:
        ctx: MCP context
        text: Text content of the post
        image_data: Base64-encoded image data
        image_alt: Alternative text description for the image
        profile_identify: Optional handle or DID for the post author
        reply_to: Optional reply information dict with keys uri and cid
        langs: Optional list of language codes
        facets: Optional list of facets (mentions, links, etc.)

    Returns:
        Status of the post creation
    """
    try:
        bluesky_client = get_authenticated_client(ctx)

        # Decode base64 image
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to decode image data: {str(e)}",
            }

        # Send the post with image
        post_response = bluesky_client.send_image(
            text=text,
            image=image_bytes,
            image_alt=image_alt,
            profile_identify=profile_identify,
            reply_to=reply_to,
            langs=langs,
            facets=facets,
        )

        return {
            "status": "success",
            "message": "Post with image created successfully",
            "post_uri": post_response.uri,
            "post_cid": post_response.cid,
        }
    except Exception as e:
        error_msg = f"Failed to create post with image: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
def send_images(
    ctx: Context,
    text: str,
    images_data: List[str],
    image_alts: Optional[List[str]] = None,
    profile_identify: Optional[str] = None,
    reply_to: Optional[Dict[str, Any]] = None,
    langs: Optional[List[str]] = None,
    facets: Optional[List[Dict[str, Any]]] = None,
) -> Dict:
    """Send a post with multiple images (up to 4).

    Args:
        ctx: MCP context
        text: Text content of the post
        images_data: List of base64-encoded image data (max 4)
        image_alts: Optional list of alt text for each image
        profile_identify: Optional handle or DID for the post author
        reply_to: Optional reply information dict with keys uri and cid
        langs: Optional list of language codes
        facets: Optional list of facets (mentions, links, etc.)

    Returns:
        Status of the post creation
    """
    try:
        bluesky_client = get_authenticated_client(ctx)

        # Verify we have 1-4 images
        if not images_data:
            return {
                "status": "error",
                "message": "At least one image is required",
            }

        if len(images_data) > 4:
            return {
                "status": "error",
                "message": "Maximum of 4 images allowed",
            }

        # Decode all images
        images_bytes = []
        for img_data in images_data:
            try:
                image_bytes = base64.b64decode(img_data)
                images_bytes.append(image_bytes)
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to decode image data: {str(e)}",
                }

        # Send the post with images
        post_response = bluesky_client.send_images(
            text=text,
            images=images_bytes,
            image_alts=image_alts,
            profile_identify=profile_identify,
            reply_to=reply_to,
            langs=langs,
            facets=facets,
        )

        return {
            "status": "success",
            "message": "Post with images created successfully",
            "post_uri": post_response.uri,
            "post_cid": post_response.cid,
        }
    except Exception as e:
        error_msg = f"Failed to create post with images: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
def send_video(
    ctx: Context,
    text: str,
    video_data: str,
    video_alt: Optional[str] = None,
    profile_identify: Optional[str] = None,
    reply_to: Optional[Dict[str, Any]] = None,
    langs: Optional[List[str]] = None,
    facets: Optional[List[Dict[str, Any]]] = None,
) -> Dict:
    """Send a post with a video.

    Args:
        ctx: MCP context
        text: Text content of the post
        video_data: Base64-encoded video data
        video_alt: Optional alternative text description for the video
        profile_identify: Optional handle or DID for the post author
        reply_to: Optional reply information dict with keys uri and cid
        langs: Optional list of language codes
        facets: Optional list of facets (mentions, links, etc.)

    Returns:
        Status of the post creation
    """
    try:
        bluesky_client = get_authenticated_client(ctx)

        # Decode base64 video
        try:
            video_bytes = base64.b64decode(video_data)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to decode video data: {str(e)}",
            }

        # Send the post with video
        post_response = bluesky_client.send_video(
            text=text,
            video=video_bytes,
            video_alt=video_alt,
            profile_identify=profile_identify,
            reply_to=reply_to,
            langs=langs,
            facets=facets,
        )

        return {
            "status": "success",
            "message": "Post with video created successfully",
            "post_uri": post_response.uri,
            "post_cid": post_response.cid,
        }
    except Exception as e:
        error_msg = f"Failed to create post with video: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
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
    try:
        bluesky_client = get_authenticated_client(ctx)
        # Delete the post
        bluesky_client.delete_post(uri)

        return {
            "status": "success",
            "message": "Post deleted successfully",
        }
    except Exception as e:
        error_msg = f"Failed to delete post: {str(e)}"
        return {"status": "error", "message": error_msg}


@mcp.tool()
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
    try:
        bluesky_client = get_authenticated_client(ctx)

        # First resolve the handle to a DID
        resolved = bluesky_client.resolve_handle(handle)
        did = resolved.did

        # Now follow the user - follow method expects the DID as subject parameter
        follow_response = bluesky_client.follow(did)

        return {
            "status": "success",
            "message": f"Now following {handle}",
            "follow_uri": follow_response.uri,
            "follow_cid": follow_response.cid,
        }
    except Exception as e:
        error_msg = f"Failed to follow user: {str(e)}"
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
            "posts": [
                "get_timeline_posts",
                "get_feed_posts",
                "get_list_posts",
                "get_user_posts",
                "get_liked_posts",
                "create_post",
                "like_post",
                "get_post_thread",
            ],
            "search": ["search_posts", "search_people", "search_feeds"],
            "utilities": ["convert_url_to_uri", "get_trends", "get_pinned_feeds"],
        },
    }
    return tools_info


def main():
    """Main entry point for the script."""
    # Stdio is prefered for local execution.
    mcp.run(transport="stdio")


# Main entry point
if __name__ == "__main__":
    main()
