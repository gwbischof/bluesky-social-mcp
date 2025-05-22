"""Bluesky MCP Server.

A single-file implementation with all tool logic directly embedded.
"""

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


# @mcp.tool()
# def get_timeline_posts(
#     ctx: Context,
#     limit: Union[int, str] = 50,
#     cursor: Optional[str] = None,
#     algorithm: Optional[str] = None,
# ) -> Dict:
#     """Get posts from the authenticated user's home timeline.

#     Args:
#         ctx: MCP context
#         limit: Maximum number of results to return (1-100)
#         cursor: Optional pagination cursor
#         algorithm: Optional algorithm to use, e.g. "reverse-chronological"

#     Returns:
#         Timeline posts
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         params = {"limit": max(1, min(100, limit))}
#         if cursor:
#             params["cursor"] = cursor
#         if algorithm:
#             params["algorithm"] = algorithm

#         timeline_response = client.app.bsky.feed.get_timeline(params)
#         timeline = timeline_response.dict()
#         return {"status": "success", "timeline": timeline}
#     except Exception as e:
#         error_msg = f"Failed to get timeline: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def get_feed_posts(
#     ctx: Context,
#     feed: str,
#     limit: Union[int, str] = 50,
#     cursor: Optional[str] = None,
# ) -> Dict:
#     """Get posts from a specified feed.

#     Args:
#         ctx: MCP context
#         feed: URI of the feed to get posts from
#         limit: Maximum number of results to return (1-100)
#         cursor: Optional pagination cursor

#     Returns:
#         Feed posts
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         params = {"feed": feed, "limit": max(1, min(100, limit))}
#         if cursor:
#             params["cursor"] = cursor

#         feed_response = client.app.bsky.feed.get_feed(params)
#         feed_data = feed_response.dict()
#         return {"status": "success", "feed": feed_data}
#     except Exception as e:
#         error_msg = f"Failed to get feed: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def get_list_posts(
#     ctx: Context,
#     list_uri: str,
#     limit: Union[int, str] = 50,
#     cursor: Optional[str] = None,
# ) -> Dict:
#     """Get posts from the specified list.

#     Args:
#         ctx: MCP context
#         list_uri: URI of the list to get posts from
#         limit: Maximum number of results to return (1-100)
#         cursor: Optional pagination cursor

#     Returns:
#         List posts
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager

#     client = auth_manager.get_client(ctx)

#     try:
#         params = {"list": list_uri, "limit": max(1, min(100, limit))}
#         if cursor:
#             params["cursor"] = cursor

#         list_response = client.app.bsky.feed.get_list_feed(params)
#         list_data = list_response.dict()
#         return {"status": "success", "list_feed": list_data}
#     except Exception as e:
#         error_msg = f"Failed to get list feed: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def get_user_posts(
#     ctx: Context,
#     handle: Optional[str] = None,
#     limit: Union[int, str] = 50,
#     cursor: Optional[str] = None,
#     filter: Optional[str] = None,
# ) -> Dict:
#     """Get posts from a specified user.

#     Args:
#         ctx: MCP context
#         handle: Optional handle to get posts for. If None, gets the authenticated user
#         limit: Maximum number of results to return (1-100)
#         cursor: Optional pagination cursor
#         filter: Optional filter, e.g. "posts_with_media", "posts_no_replies"

#     Returns:
#         User posts
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager

#     client = auth_manager.get_client(ctx)

#     try:
#         # If no handle provided, get authenticated user's posts
#         if not handle:
#             handle = client.me.handle

#         params = {"actor": handle, "limit": max(1, min(100, limit))}
#         if cursor:
#             params["cursor"] = cursor
#         if filter:
#             params["filter"] = filter

#         author_feed_response = client.app.bsky.feed.get_author_feed(params)
#         author_feed = author_feed_response.dict()
#         return {"status": "success", "author_feed": author_feed}
#     except Exception as e:
#         error_msg = f"Failed to get user posts: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def get_liked_posts(
#     ctx: Context,
#     handle: Optional[str] = None,
#     limit: Union[int, str] = 50,
#     cursor: Optional[str] = None,
# ) -> Dict:
#     """Get posts liked by a user.

#     Args:
#         ctx: MCP context
#         handle: Optional handle to get likes for. If None, gets the authenticated user
#         limit: Maximum number of results to return (1-100)
#         cursor: Optional pagination cursor

#     Returns:
#         Liked posts
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager

#     client = auth_manager.get_client(ctx)

#     try:
#         # If no handle provided, get authenticated user's likes
#         if not handle:
#             handle = client.me.handle

#         params = {"actor": handle, "limit": max(1, min(100, limit))}
#         if cursor:
#             params["cursor"] = cursor

#         likes_response = client.app.bsky.feed.get_actor_likes(params)
#         likes = likes_response.dict()
#         return {"status": "success", "likes": likes}
#     except Exception as e:
#         error_msg = f"Failed to get liked posts: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


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


# @mcp.tool()
# def repost_post(
#     ctx: Context,
#     uri: str,
#     cid: str,
# ) -> Dict:
#     """Repost another user's post.

#     Args:
#         ctx: MCP context
#         uri: URI of the post to repost
#         cid: CID of the post to repost

#     Returns:
#         Status of the repost operation
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         repost_response = client.repost(uri, cid)
#         return {
#             "status": "success",
#             "message": "Post reposted successfully",
#             "repost_uri": repost_response.uri,
#             "repost_cid": repost_response.cid,
#         }
#     except Exception as e:
#         error_msg = f"Failed to repost: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def unrepost_post(
#     ctx: Context,
#     uri: str,
#     cid: str,
# ) -> Dict:
#     """Remove a repost of another user's post.

#     Args:
#         ctx: MCP context
#         uri: URI of the post to unrepost
#         cid: CID of the post to unrepost

#     Returns:
#         Status of the unrepost operation
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         client.unrepost(uri, cid)
#         return {
#             "status": "success",
#             "message": "Post unreposted successfully",
#         }
#     except Exception as e:
#         error_msg = f"Failed to unrepost: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


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


# @mcp.tool()
# def get_reposted_by(
#     ctx: Context,
#     uri: str,
#     cid: Optional[str] = None,
#     limit: Union[int, str] = 50,
#     cursor: Optional[str] = None,
# ) -> Dict:
#     """Get users who reposted a post.

#     Args:
#         ctx: MCP context
#         uri: URI of the post to get reposts for
#         cid: Optional CID of the post (not strictly required)
#         limit: Maximum number of results to return (1-100)
#         cursor: Optional pagination cursor

#     Returns:
#         List of users who reposted the post
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         params = {"uri": uri, "limit": max(1, min(100, limit))}
#         if cursor:
#             params["cursor"] = cursor

#         reposts_response = client.get_reposted_by(params)
#         reposts_data = reposts_response.dict()

#         return {"status": "success", "reposts": reposts_data}
#     except Exception as e:
#         error_msg = f"Failed to get reposts: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def send_image(
#     ctx: Context,
#     text: str,
#     image_data: str,
#     alt_text: str = "",
#     reply_to: Optional[Dict] = None,
# ) -> Dict:
#     """Send a post with a single image.

#     Args:
#         ctx: MCP context
#         text: Text content of the post
#         image_data: Base64-encoded image data
#         alt_text: Alternative text description for the image
#         reply_to: Optional reply information dict with keys uri and cid

#     Returns:
#         Status of the post creation
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         # Decode base64 image
#         try:
#             img_bytes = BytesIO(base64.b64decode(image_data))
#             image = img_bytes.read()
#         except Exception as e:
#             return {
#                 "status": "error",
#                 "message": f"Failed to decode image data: {str(e)}",
#             }

#         # Prepare reply parameters if needed
#         reply_params = {}
#         if reply_to and "uri" in reply_to and "cid" in reply_to:
#             reply_params = {
#                 "reply_to": {
#                     "uri": reply_to["uri"],
#                     "cid": reply_to["cid"]
#                 }
#             }

#             # Handle root if provided
#             if "root_uri" in reply_to and "root_cid" in reply_to:
#                 reply_params["reply_to"]["root"] = {
#                     "uri": reply_to["root_uri"],
#                     "cid": reply_to["root_cid"]
#                 }

#         # Send the post with image
#         post_response = client.send_image(
#             text=text,
#             image=image,
#             image_alt=alt_text,
#             **reply_params
#         )

#         return {
#             "status": "success",
#             "message": "Post with image created successfully",
#             "post_uri": post_response.uri,
#             "post_cid": post_response.cid,
#         }
#     except Exception as e:
#         error_msg = f"Failed to create post with image: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def send_images(
#     ctx: Context,
#     text: str,
#     images: List[Dict[str, str]],
#     reply_to: Optional[Dict] = None,
# ) -> Dict:
#     """Send a post with multiple images (up to 4).

#     Args:
#         ctx: MCP context
#         text: Text content of the post
#         images: List of image dicts, each with "image_data" (base64) and "alt" keys
#         reply_to: Optional reply information dict with keys uri and cid

#     Returns:
#         Status of the post creation
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         # Verify we have 1-4 images
#         if not images:
#             return {
#                 "status": "error",
#                 "message": "At least one image is required",
#             }

#         if len(images) > 4:
#             return {
#                 "status": "error",
#                 "message": "Maximum of 4 images allowed",
#             }

#         # Process images
#         image_bytes_list = []
#         alt_texts = []

#         for img in images:
#             if "image_data" not in img:
#                 return {
#                     "status": "error",
#                     "message": "Each image must contain 'image_data' with base64 encoded content"
#                 }

#             # Decode base64 image
#             try:
#                 img_bytes = BytesIO(base64.b64decode(img["image_data"]))
#                 image_bytes_list.append(img_bytes.read())

#                 # Add alt text
#                 alt_texts.append(img.get("alt", ""))
#             except Exception as e:
#                 return {
#                     "status": "error",
#                     "message": f"Failed to decode image data: {str(e)}",
#                 }

#         # Prepare reply parameters if needed
#         reply_params = {}
#         if reply_to and "uri" in reply_to and "cid" in reply_to:
#             reply_params = {
#                 "reply_to": {
#                     "uri": reply_to["uri"],
#                     "cid": reply_to["cid"]
#                 }
#             }

#             # Handle root if provided
#             if "root_uri" in reply_to and "root_cid" in reply_to:
#                 reply_params["reply_to"]["root"] = {
#                     "uri": reply_to["root_uri"],
#                     "cid": reply_to["root_cid"]
#                 }

#         # Send the post with images
#         post_response = client.send_images(
#             text=text,
#             image=image_bytes_list,
#             alt_text=alt_texts,
#             **reply_params
#         )

#         return {
#             "status": "success",
#             "message": "Post with images created successfully",
#             "post_uri": post_response.uri,
#             "post_cid": post_response.cid,
#         }
#     except Exception as e:
#         error_msg = f"Failed to create post with images: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def send_video(
#     ctx: Context,
#     text: str,
#     video_data: str,
#     alt_text: str = "",
#     reply_to: Optional[Dict] = None,
# ) -> Dict:
#     """Send a post with a video.

#     Args:
#         ctx: MCP context
#         text: Text content of the post
#         video_data: Base64-encoded video data
#         alt_text: Alternative text description for the video
#         reply_to: Optional reply information dict with keys uri and cid

#     Returns:
#         Status of the post creation
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         # Decode base64 video
#         try:
#             video_bytes = BytesIO(base64.b64decode(video_data))
#             video = video_bytes.read()
#         except Exception as e:
#             return {
#                 "status": "error",
#                 "message": f"Failed to decode video data: {str(e)}",
#             }

#         # Prepare reply parameters if needed
#         reply_params = {}
#         if reply_to and "uri" in reply_to and "cid" in reply_to:
#             reply_params = {
#                 "reply_to": {
#                     "uri": reply_to["uri"],
#                     "cid": reply_to["cid"]
#                 }
#             }

#             # Handle root if provided
#             if "root_uri" in reply_to and "root_cid" in reply_to:
#                 reply_params["reply_to"]["root"] = {
#                     "uri": reply_to["root_uri"],
#                     "cid": reply_to["root_cid"]
#                 }

#         # Send the post with video
#         post_response = client.send_video(
#             text=text,
#             video=video,
#             video_alt=alt_text,
#             **reply_params
#         )

#         return {
#             "status": "success",
#             "message": "Post with video created successfully",
#             "post_uri": post_response.uri,
#             "post_cid": post_response.cid,
#         }
#     except Exception as e:
#         error_msg = f"Failed to create post with video: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


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


# @mcp.tool()
# def search_posts(
#     ctx: Context,
#     query: str,
#     limit: Union[int, str] = 25,
#     cursor: Optional[str] = None,
#     sort: str = "top",
# ) -> Dict:
#     """Search for posts with a given query.

#     Args:
#         ctx: MCP context
#         query: Search query
#         limit: Maximum number of results to return (1-100)
#         cursor: Optional pagination cursor
#         sort: Sort order, either "top" or "latest"

#     Returns:
#         Search results
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager

#     client = auth_manager.get_client(ctx)

#     try:
#         params = {"q": query, "limit": max(1, min(100, limit))}
#         if cursor:
#             params["cursor"] = cursor

#         # The bluesky API only supports "recent" or default (relevance)
#         if sort.lower() == "latest":
#             params["sort"] = "recent"

#         search_response = client.app.bsky.feed.search_posts(params)
#         search_results = search_response.dict()
#         return {"status": "success", "search_results": search_results}
#     except Exception as e:
#         error_msg = f"Failed to search posts: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def search_people(
#     ctx: Context,
#     query: str,
#     limit: Union[int, str] = 25,
#     cursor: Optional[str] = None,
# ) -> Dict:
#     """Search for people with a given query.

#     Args:
#         ctx: MCP context
#         query: Search query
#         limit: Maximum number of results to return (1-100)
#         cursor: Optional pagination cursor

#     Returns:
#         Search results
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager

#     client = auth_manager.get_client(ctx)

#     try:
#         params = {"term": query, "limit": max(1, min(100, limit))}
#         if cursor:
#             params["cursor"] = cursor

#         search_response = client.app.bsky.actor.search_actors(params)
#         search_results = search_response.dict()
#         return {"status": "success", "search_results": search_results}
#     except Exception as e:
#         error_msg = f"Failed to search people: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def search_feeds(
#     ctx: Context,
#     query: str,
#     limit: Union[int, str] = 25,
#     cursor: Optional[str] = None,
# ) -> Dict:
#     """Search for feeds with a given query.

#     Args:
#         ctx: MCP context
#         query: Search query
#         limit: Maximum number of results to return (1-100)
#         cursor: Optional pagination cursor

#     Returns:
#         Search results
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager

#     client = auth_manager.get_client(ctx)

#     try:
#         params = {"query": query, "limit": max(1, min(100, limit))}
#         if cursor:
#             params["cursor"] = cursor

#         search_response = client.app.bsky.feed.search_feeds(params)
#         search_results = search_response.dict()
#         return {"status": "success", "search_results": search_results}
#     except Exception as e:
#         error_msg = f"Failed to search feeds: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def block_user(
#     ctx: Context,
#     handle: str,
# ) -> Dict:
#     """Block a user.

#     Args:
#         ctx: MCP context
#         handle: Handle of the user to block

#     Returns:
#         Status of the block operation
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         # First resolve the handle to a DID
#         resolved = client.resolve_handle(handle)
#         did = resolved.did

#         # Now block the user
#         block_response = client.app.bsky.graph.block.create(
#             client.me.did,
#             {"subject": did, "createdAt": client.get_current_time_iso()},
#         )

#         return {
#             "status": "success",
#             "message": f"Blocked user @{handle}",
#             "block_uri": block_response.uri,
#         }
#     except Exception as e:
#         error_msg = f"Failed to block user: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def unblock_user(
#     ctx: Context,
#     handle: str,
# ) -> Dict:
#     """Unblock a previously blocked user.

#     Args:
#         ctx: MCP context
#         handle: Handle of the user to unblock

#     Returns:
#         Status of the unblock operation
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         # First resolve the handle to a DID
#         resolved = client.resolve_handle(handle)
#         did = resolved.did

#         # Find the block record
#         blocks = client.app.bsky.graph.block.list(client.me.did, limit=100)

#         block_record = None
#         for uri, block in blocks.records.items():
#             if block.subject == did:
#                 block_record = uri
#                 break

#         if not block_record:
#             return {
#                 "status": "error",
#                 "message": f"No block record found for @{handle}",
#             }

#         # Extract the rkey from the AT URI
#         from atproto import AtUri
#         rkey = AtUri.from_str(block_record).rkey

#         # Delete the block
#         client.app.bsky.graph.block.delete(client.me.did, rkey)

#         return {
#             "status": "success",
#             "message": f"Unblocked user @{handle}",
#         }
#     except Exception as e:
#         error_msg = f"Failed to unblock user: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def get_blocks(
#     ctx: Context,
#     limit: Union[int, str] = 50,
#     cursor: Optional[str] = None,
# ) -> Dict:
#     """Get list of users blocked by the authenticated user.

#     Args:
#         ctx: MCP context
#         limit: Maximum number of results to return (1-100)
#         cursor: Optional pagination cursor

#     Returns:
#         List of blocked users
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         params = {"limit": max(1, min(100, limit))}
#         if cursor:
#             params["cursor"] = cursor

#         blocks_response = client.app.bsky.graph.block.list(client.me.did, **params)

#         # Extract and enhance the block records
#         blocks_data = []
#         for uri, block in blocks_response.records.items():
#             try:
#                 # Try to get profile info for each blocked user
#                 profile = client.app.bsky.actor.get_profile({"actor": block.subject}).dict()
#                 blocks_data.append({
#                     "uri": uri,
#                     "did": block.subject,
#                     "profile": profile,
#                 })
#             except Exception:
#                 # If profile fetch fails, just include the basic info
#                 blocks_data.append({
#                     "uri": uri,
#                     "did": block.subject,
#                 })

#         result = {
#             "blocks": blocks_data,
#             "cursor": blocks_response.cursor if hasattr(blocks_response, "cursor") else None,
#         }

#         return {"status": "success", "blocks_data": result}
#     except Exception as e:
#         error_msg = f"Failed to get blocks: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def mute_user(
#     ctx: Context,
#     handle: str,
# ) -> Dict:
#     """Mute a user.

#     Args:
#         ctx: MCP context
#         handle: Handle of the user to mute

#     Returns:
#         Status of the mute operation
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         # First resolve the handle to a DID
#         resolved = client.resolve_handle(handle)
#         did = resolved.did

#         # Mute the user
#         client.app.bsky.graph.mute_actor({"actor": did})

#         return {
#             "status": "success",
#             "message": f"Muted user @{handle}",
#         }
#     except Exception as e:
#         error_msg = f"Failed to mute user: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def unmute_user(
#     ctx: Context,
#     handle: str,
# ) -> Dict:
#     """Unmute a previously muted user.

#     Args:
#         ctx: MCP context
#         handle: Handle of the user to unmute

#     Returns:
#         Status of the unmute operation
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         # First resolve the handle to a DID
#         resolved = client.resolve_handle(handle)
#         did = resolved.did

#         # Unmute the user
#         client.app.bsky.graph.unmute_actor({"actor": did})

#         return {
#             "status": "success",
#             "message": f"Unmuted user @{handle}",
#         }
#     except Exception as e:
#         error_msg = f"Failed to unmute user: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def get_mutes(
#     ctx: Context,
#     limit: Union[int, str] = 50,
#     cursor: Optional[str] = None,
# ) -> Dict:
#     """Get list of users muted by the authenticated user.

#     Args:
#         ctx: MCP context
#         limit: Maximum number of results to return (1-100)
#         cursor: Optional pagination cursor

#     Returns:
#         List of muted users
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         params = {"limit": max(1, min(100, limit))}
#         if cursor:
#             params["cursor"] = cursor

#         mutes_response = client.app.bsky.graph.get_mutes(params)
#         mutes_data = mutes_response.dict()

#         return {"status": "success", "mutes": mutes_data}
#     except Exception as e:
#         error_msg = f"Failed to get mutes: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def get_notifications(
#     ctx: Context,
#     limit: Union[int, str] = 50,
#     cursor: Optional[str] = None,
#     seen_at: Optional[str] = None,
#     filter: Optional[str] = None,
# ) -> Dict:
#     """Get notifications for the authenticated user.

#     Args:
#         ctx: MCP context
#         limit: Maximum number of results to return (1-100)
#         cursor: Optional pagination cursor
#         seen_at: RFC3339 timestamp to mark notifications as seen up to
#         filter: Optional filter for notification type ('mentions', 'replies', 'quotes', 'reposts', 'follows', 'likes')

#     Returns:
#         List of notifications
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         params = {"limit": max(1, min(100, limit))}
#         if cursor:
#             params["cursor"] = cursor
#         if seen_at:
#             params["seenAt"] = seen_at

#         # Handle filter types
#         valid_filters = {'mentions', 'replies', 'quotes', 'reposts', 'follows', 'likes'}
#         if filter and filter in valid_filters:
#             # Only include if it's a valid filter
#             params["filter"] = filter

#         notifications_response = client.app.bsky.notification.list_notifications(params)
#         notifications_data = notifications_response.dict()

#         return {"status": "success", "notifications": notifications_data}
#     except Exception as e:
#         error_msg = f"Failed to get notifications: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def count_unread_notifications(ctx: Context) -> Dict:
#     """Count unread notifications for the authenticated user.

#     Args:
#         ctx: MCP context

#     Returns:
#         Count of unread notifications
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         count_response = client.app.bsky.notification.get_unread_count({})

#         return {
#             "status": "success",
#             "count": count_response.count,
#             "last_seen_at": getattr(count_response, "last_seen", None),
#         }
#     except Exception as e:
#         error_msg = f"Failed to count unread notifications: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def mark_notifications_seen(ctx: Context) -> Dict:
#     """Mark all notifications as seen.

#     Args:
#         ctx: MCP context

#     Returns:
#         Status of the operation
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         # Get current time as ISO string
#         timestamp = client.get_current_time_iso()

#         # Mark notifications as seen
#         client.app.bsky.notification.update_seen({"seenAt": timestamp})

#         return {
#             "status": "success",
#             "message": "Notifications marked as seen",
#             "seen_at": timestamp,
#         }
#     except Exception as e:
#         error_msg = f"Failed to mark notifications as seen: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def get_notification_preferences(ctx: Context) -> Dict:
#     """Get notification preferences for the authenticated user.

#     Args:
#         ctx: MCP context

#     Returns:
#         Notification preferences
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager
#     client = auth_manager.get_client(ctx)

#     try:
#         # Get user preferences
#         prefs_response = client.app.bsky.actor.get_preferences({})

#         # Extract notification preferences
#         notification_prefs = {}
#         for pref in prefs_response.preferences:
#             # Look for notification-specific preferences
#             if pref.type == "app.bsky.actor.defs#notificationPref":
#                 notification_prefs = pref.dict()
#                 break

#         # If no notification preferences found, return empty default
#         if not notification_prefs:
#             notification_prefs = {"enabled": True}

#         return {
#             "status": "success",
#             "preferences": notification_prefs,
#         }
#     except Exception as e:
#         error_msg = f"Failed to get notification preferences: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def resolve_handle(
#     ctx: Context,
#     handle: str,
# ) -> Dict:
#     """Resolve a handle to a DID.

#     This tool does not require authentication and can be used to convert
#     a Bluesky handle (like username.bsky.social) to a DID.

#     Args:
#         ctx: MCP context
#         handle: User handle to resolve

#     Returns:
#         Resolved DID information
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager

#     # Try to use existing client if authenticated
#     client = None
#     if auth_manager.is_authenticated(ctx):
#         client = auth_manager.get_client(ctx)
#     else:
#         # Create a temporary client instance for unauthenticated use
#         from atproto import Client
#         client = Client()

#     try:
#         resolved = client.resolve_handle(handle)

#         return {
#             "status": "success",
#             "handle": handle,
#             "did": resolved.did,
#         }
#     except Exception as e:
#         error_msg = f"Failed to resolve handle: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def get_post_thread(
#     ctx: Context,
#     uri: str,
#     depth: int = 6,
#     parent_height: int = 80,
# ) -> Dict:
#     """Get a thread from a post URI.

#     Args:
#         ctx: MCP context
#         uri: URI of the post to get the thread for
#         depth: Maximum depth to retrieve (for replies)
#         parent_height: Maximum height to retrieve (for parents)

#     Returns:
#         Thread data
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager

#     client = auth_manager.get_client(ctx)

#     try:
#         params = {
#             "uri": uri,
#             "depth": max(0, min(1000, depth)),
#             "parentHeight": max(0, min(1000, parent_height)),
#         }

#         thread_response = client.app.bsky.feed.get_post_thread(params)
#         thread = thread_response.dict()
#         return {"status": "success", "thread": thread}
#     except Exception as e:
#         error_msg = f"Failed to get post thread: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def convert_url_to_uri(
#     ctx: Context,
#     url: str,
# ) -> Dict:
#     """Convert a Bluesky web URL to an AT URI.

#     Args:
#         ctx: MCP context
#         url: URL to convert (e.g., https://bsky.app/profile/username.bsky.social/post/abcdef)

#     Returns:
#         AT URI
#     """
#     try:
#         # Extract the key components from the URL
#         # Handle post URLs
#         post_pattern = r"https?://(?:www\.)?bsky\.app/profile/([^/]+)/post/([^/]+)"
#         post_match = re.match(post_pattern, url)

#         if post_match:
#             handle = post_match.group(1)
#             post_id = post_match.group(2)

#             auth_manager = ctx.request_context.lifespan_context.auth_manager
#             client = None

#             # If authenticated, use the client
#             if auth_manager.is_authenticated(ctx):
#                 client = auth_manager.get_client(ctx)
#             else:
#                 # Create a temporary non-authenticated client
#                 client = Client()

#             # Resolve handle to DID
#             resolved = client.resolve_handle(handle)
#             did = resolved.did

#             # Construct the AT URI
#             at_uri = f"at://{did}/app.bsky.feed.post/{post_id}"
#             return {"status": "success", "uri": at_uri}

#         # Handle profile URLs
#         profile_pattern = r"https?://(?:www\.)?bsky\.app/profile/([^/]+)"
#         profile_match = re.match(profile_pattern, url)

#         if profile_match:
#             handle = profile_match.group(1)

#             auth_manager = ctx.request_context.lifespan_context.auth_manager
#             client = None

#             # If authenticated, use the client
#             if auth_manager.is_authenticated(ctx):
#                 client = auth_manager.get_client(ctx)
#             else:
#                 # Create a temporary non-authenticated client
#                 client = Client()

#             # Resolve handle to DID
#             resolved = client.resolve_handle(handle)
#             did = resolved.did

#             # Return the DID
#             return {"status": "success", "uri": did}

#         return {"status": "error", "message": "Unsupported URL format"}
#     except Exception as e:
#         error_msg = f"Failed to convert URL to URI: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def get_trends(
#     ctx: Context,
# ) -> Dict:
#     """Get current trending topics on Bluesky.

#     Args:
#         ctx: MCP context

#     Returns:
#         Trending topics with post counts
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager

#     client = auth_manager.get_client(ctx)

#     try:
#         # Get popular posts
#         popular_params = {"limit": 100}
#         popular_response = client.app.bsky.unspecced.get_popular(popular_params)
#         popular_posts = popular_response.dict()

#         # Extract and count hashtags
#         hashtags: Dict[str, int] = {}
#         feed_items = popular_posts.get("feed", [])

#         for post in feed_items:
#             if "post" in post and "record" in post["post"]:
#                 record = post["post"]["record"]
#                 if "text" in record:
#                     # Extract hashtags with regex
#                     text = record["text"]
#                     if isinstance(text, str):
#                         tags = re.findall(r"#(\w+)", text)
#                         for tag in tags:
#                             tag_lower = tag.lower()
#                             if tag_lower in hashtags:
#                                 hashtags[tag_lower] += 1
#                             else:
#                                 hashtags[tag_lower] = 1

#         # Sort by count
#         sorted_tags = [
#             {"tag": tag, "count": count}
#             for tag, count in sorted(hashtags.items(), key=lambda x: x[1], reverse=True)
#         ]

#         return {
#             "status": "success",
#             "trends": sorted_tags[:20],  # Return top 20 trending tags
#         }
#     except Exception as e:
#         error_msg = f"Failed to get trends: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


# @mcp.tool()
# def get_pinned_feeds(
#     ctx: Context,
# ) -> Dict:
#     """Get pinned feeds from user preferences.

#     Args:
#         ctx: MCP context

#     Returns:
#         Pinned feeds
#     """
#     auth_manager = ctx.request_context.lifespan_context.auth_manager

#     client = auth_manager.get_client(ctx)

#     try:
#         # Get user preferences
#         prefs_response = client.app.bsky.actor.get_preferences({})

#         # Find pinned feeds in preferences
#         pinned_feeds = []
#         for pref in prefs_response.preferences:
#             if pref.type == "app.bsky.actor.defs#savedFeedsPref":
#                 if hasattr(pref, "saved"):
#                     pinned_feeds = pref.saved
#                     break

#         # If feeds are found, fetch details for each one
#         feed_details = []
#         if pinned_feeds:
#             for feed_uri in pinned_feeds:
#                 try:
#                     # Extract the feed generator DID and feed name
#                     feed_match = re.match(
#                         r"at://([^/]+)/app\.bsky\.feed\.generator/([^/]+)", feed_uri
#                     )

#                     if feed_match:
#                         # Extract feed components (captured but not used directly)
#                         feed_did: str = feed_match.group(1)
#                         feed_id: str = feed_match.group(2)

#                         # Variables are used indirectly through feed_uri in the API call below
#                         _ = feed_did, feed_id  # Mark as used to satisfy linters

#                         # Get feed info
#                         feed_info = client.app.bsky.feed.get_feed_generator(
#                             {"feed": feed_uri}
#                         )

#                         feed_details.append({"uri": feed_uri, "info": feed_info.dict()})
#                 except Exception as feed_err:
#                     # Skip failed feeds
#                     ctx.error(
#                         f"Failed to get feed details for {feed_uri}: {str(feed_err)}"
#                     )
#                     continue

#         return {"status": "success", "pinned_feeds": feed_details}
#     except Exception as e:
#         error_msg = f"Failed to get pinned feeds: {str(e)}"
#         ctx.error(error_msg)
#         return {"status": "error", "message": error_msg}


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
