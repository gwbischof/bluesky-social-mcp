"""Tools for interacting with Bluesky API."""

from typing import Dict, List, Optional, Union, Any

from mcp.server.fastmcp import Context


def require_auth(func):
    """Decorator to require authentication for a tool.

    Args:
        func: The function to decorate

    Returns:
        Decorated function
    """

    def wrapper(ctx: Context, *args, **kwargs):
        """Check authentication before calling the function."""
        auth_manager = ctx.request_context.lifespan_context.auth_manager
        if not auth_manager.is_authenticated(ctx):
            return {"status": "error", "message": "Authentication required"}
        return func(ctx, *args, **kwargs)

    return wrapper


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


@require_auth
def get_follows(
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


@require_auth
def get_followers(
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


@require_auth
def get_timeline_posts(
    ctx: Context, 
    limit: int = 50, 
    cursor: Optional[str] = None,
    algorithm: Optional[str] = None
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


@require_auth
def get_feed_posts(
    ctx: Context,
    feed: str,
    limit: int = 50,
    cursor: Optional[str] = None
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


@require_auth
def get_list_posts(
    ctx: Context,
    list_uri: str,
    limit: int = 50,
    cursor: Optional[str] = None
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


@require_auth
def get_user_posts(
    ctx: Context,
    handle: Optional[str] = None,
    limit: int = 50,
    cursor: Optional[str] = None,
    filter: Optional[str] = None
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


@require_auth
def get_liked_posts(
    ctx: Context,
    handle: Optional[str] = None,
    limit: int = 50,
    cursor: Optional[str] = None
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


@require_auth
def like_post(
    ctx: Context,
    uri: str,
    cid: str
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
            "like_cid": like_response.cid
        }
    except Exception as e:
        error_msg = f"Failed to like post: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@require_auth
def create_post(
    ctx: Context,
    text: str,
    reply_to: Optional[Dict] = None,
    images: Optional[List[Dict]] = None,
    quotes: Optional[Dict] = None,
    links: Optional[List[Dict]] = None
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
            post_params["reply"] = {
                "root": {"uri": reply_to.get("root_uri"), "cid": reply_to.get("root_cid")},
                "parent": {"uri": reply_to.get("uri"), "cid": reply_to.get("cid")}
            }
        
        # Handle images
        if images:
            image_uploads = []
            for img_data in images:
                if "image_data" in img_data and "alt" in img_data:
                    # Assuming image_data is base64 encoded
                    import base64
                    from io import BytesIO
                    
                    img_bytes = BytesIO(base64.b64decode(img_data["image_data"]))
                    upload = client.upload_blob(img_bytes.read())
                    
                    image_uploads.append({
                        "image": upload.blob,
                        "alt": img_data["alt"]
                    })
            
            post_params["images"] = image_uploads
            
        # Handle quote post
        if quotes and "uri" in quotes and "cid" in quotes:
            post_params["quote"] = {"uri": quotes["uri"], "cid": quotes["cid"]}
            
        # Create the post
        post_response = client.send_post(**post_params)
        return {
            "status": "success",
            "message": "Post created successfully",
            "post_uri": post_response.uri,
            "post_cid": post_response.cid
        }
    except Exception as e:
        error_msg = f"Failed to create post: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@require_auth
def follow_user(
    ctx: Context,
    handle: str
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
            "follow_uri": follow_response.uri
        }
    except Exception as e:
        error_msg = f"Failed to follow user: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@require_auth
def search_posts(
    ctx: Context,
    query: str,
    limit: int = 25,
    cursor: Optional[str] = None,
    sort: str = "top"  # "top" or "latest"
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
        params = {
            "q": query, 
            "limit": max(1, min(100, limit))
        }
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


@require_auth
def search_people(
    ctx: Context,
    query: str,
    limit: int = 25,
    cursor: Optional[str] = None
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
        params = {
            "term": query, 
            "limit": max(1, min(100, limit))
        }
        if cursor:
            params["cursor"] = cursor
            
        search_response = client.app.bsky.actor.search_actors(params)
        search_results = search_response.dict()
        return {"status": "success", "search_results": search_results}
    except Exception as e:
        error_msg = f"Failed to search people: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@require_auth
def search_feeds(
    ctx: Context,
    query: str,
    limit: int = 25,
    cursor: Optional[str] = None
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
        params = {
            "query": query, 
            "limit": max(1, min(100, limit))
        }
        if cursor:
            params["cursor"] = cursor
            
        search_response = client.app.bsky.feed.search_feeds(params)
        search_results = search_response.dict()
        return {"status": "success", "search_results": search_results}
    except Exception as e:
        error_msg = f"Failed to search feeds: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@require_auth
def get_post_thread(
    ctx: Context,
    uri: str,
    depth: int = 6,
    parent_height: int = 80
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
            "parentHeight": max(0, min(1000, parent_height))
        }
            
        thread_response = client.app.bsky.feed.get_post_thread(params)
        thread = thread_response.dict()
        return {"status": "success", "thread": thread}
    except Exception as e:
        error_msg = f"Failed to get post thread: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


def convert_url_to_uri(
    ctx: Context,
    url: str
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
        import re
        # Handle post URLs
        post_pattern = r'https?://(?:www\.)?bsky\.app/profile/([^/]+)/post/([^/]+)'
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
                from atproto import Client
                client = Client()
            
            # Resolve handle to DID
            resolved = client.resolve_handle(handle)
            did = resolved.did
            
            # Construct the AT URI
            at_uri = f"at://{did}/app.bsky.feed.post/{post_id}"
            return {"status": "success", "uri": at_uri}
        
        # Handle profile URLs
        profile_pattern = r'https?://(?:www\.)?bsky\.app/profile/([^/]+)'
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
                from atproto import Client
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


@require_auth
def get_trends(ctx: Context) -> Dict:
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
        hashtags = {}
        for post in popular_posts.get("feed", []):
            if "post" in post and "record" in post["post"]:
                record = post["post"]["record"]
                if "text" in record:
                    # Extract hashtags with regex
                    import re
                    tags = re.findall(r'#(\w+)', record["text"])
                    for tag in tags:
                        tag = tag.lower()
                        if tag in hashtags:
                            hashtags[tag] += 1
                        else:
                            hashtags[tag] = 1
        
        # Sort by count
        sorted_tags = [{"tag": tag, "count": count} for tag, count in 
                      sorted(hashtags.items(), key=lambda x: x[1], reverse=True)]
        
        return {
            "status": "success", 
            "trends": sorted_tags[:20]  # Return top 20 trending tags
        }
    except Exception as e:
        error_msg = f"Failed to get trends: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}


@require_auth
def get_pinned_feeds(ctx: Context) -> Dict:
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
                    import re
                    feed_match = re.match(r'at://([^/]+)/app\.bsky\.feed\.generator/([^/]+)', feed_uri)
                    
                    if feed_match:
                        did = feed_match.group(1)
                        feed_id = feed_match.group(2)
                        
                        # Get feed info
                        feed_info = client.app.bsky.feed.get_feed_generator({
                            "feed": feed_uri
                        })
                        
                        feed_details.append({
                            "uri": feed_uri,
                            "info": feed_info.dict()
                        })
                except Exception as feed_err:
                    # Skip failed feeds
                    ctx.error(f"Failed to get feed details for {feed_uri}: {str(feed_err)}")
                    continue
        
        return {
            "status": "success", 
            "pinned_feeds": feed_details
        }
    except Exception as e:
        error_msg = f"Failed to get pinned feeds: {str(e)}"
        ctx.error(error_msg)
        return {"status": "error", "message": error_msg}
