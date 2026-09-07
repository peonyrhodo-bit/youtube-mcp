import os
import requests
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI


# ============================================================
# MCP SERVER
# ============================================================

mcp = FastMCP(
    "YouTube Statistics",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "10000"))
)

YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]


# ============================================================
# TOOL: GET CHANNEL STATS
# ============================================================

@mcp.tool()
def get_channel_stats(channel_id: str) -> dict:
    """Получить основную статистику YouTube-канала по его ID."""

    response = requests.get(
        "https://www.googleapis.com/youtube/v3/channels",
        params={
            "part": "snippet,statistics",
            "id": channel_id,
            "key": YOUTUBE_API_KEY,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    if not data.get("items"):
        return {"error": "Канал не найден"}

    channel = data["items"][0]

    return {
        "channel_id": channel["id"],
        "title": channel["snippet"]["title"],
        "description": channel["snippet"].get("description", ""),
        "published_at": channel["snippet"]["publishedAt"],
        "subscribers": channel["statistics"].get("subscriberCount"),
        "views": channel["statistics"].get("viewCount"),
        "videos": channel["statistics"].get("videoCount"),
    }


# ============================================================
# TOOL: SEARCH CHANNELS
# ============================================================

@mcp.tool()
def search_channels(query: str, max_results: int = 20) -> dict:
    """Найти YouTube-каналы по поисковому запросу."""

    max_results = min(max(1, max_results), 50)

    response = requests.get(
        "https://www.googleapis.com/youtube/v3/search",
        params={
            "part": "snippet",
            "q": query,
            "type": "channel",
            "maxResults": max_results,
            "key": YOUTUBE_API_KEY,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    channels = []

    for item in data.get("items", []):
        snippet = item["snippet"]

        channels.append({
            "channel_id": item["id"]["channelId"],
            "title": snippet["title"],
            "description": snippet.get("description", ""),
            "published_at": snippet.get("publishedAt"),
        })

    return {
        "query": query,
        "count": len(channels),
        "channels": channels,
    }


# ============================================================
# TOOL: SEARCH VIDEOS
# ============================================================

@mcp.tool()
def search_videos(
    query: str,
    max_results: int = 20,
    published_after: str | None = None,
    published_before: str | None = None,
    region_code: str | None = None,
    relevance_language: str | None = None,
    order: str = "viewCount",
) -> dict:
    """Найти YouTube-видео и получить их статистику."""

    max_results = min(max(1, max_results), 50)

    allowed_orders = {
        "date",
        "rating",
        "relevance",
        "title",
        "viewCount",
    }

    if order not in allowed_orders:
        order = "viewCount"

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": order,
        "key": YOUTUBE_API_KEY,
    }

    if published_after:
        params["publishedAfter"] = published_after

    if published_before:
        params["publishedBefore"] = published_before

    if region_code:
        params["regionCode"] = region_code

    if relevance_language:
        params["relevanceLanguage"] = relevance_language

    response = requests.get(
        "https://www.googleapis.com/youtube/v3/search",
        params=params,
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    search_results = data.get("items", [])

    if not search_results:
        return {
            "query": query,
            "count": 0,
            "videos": [],
        }

    video_ids = [
        item["id"]["videoId"]
        for item in search_results
        if item.get("id", {}).get("videoId")
    ]

    if not video_ids:
        return {
            "query": query,
            "count": 0,
            "videos": [],
        }

    # Получаем подробную статистику найденных видео
    stats_response = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(video_ids),
            "key": YOUTUBE_API_KEY,
        },
        timeout=30,
    )

    stats_response.raise_for_status()
    stats_data = stats_response.json()

    detailed_videos = {}

    for video in stats_data.get("items", []):
        video_id = video["id"]

        detailed_videos[video_id] = {
            "views": video.get("statistics", {}).get("viewCount"),
            "likes": video.get("statistics", {}).get("likeCount"),
            "comments": video.get("statistics", {}).get("commentCount"),
            "duration": video.get("contentDetails", {}).get("duration"),
        }

    videos = []

    for item in search_results:
        video_id = item["id"].get("videoId")

        if not video_id:
            continue

        snippet = item["snippet"]

        video = {
            "video_id": video_id,
            "title": snippet["title"],
            "description": snippet.get("description", ""),
            "channel_id": snippet["channelId"],
            "channel_title": snippet["channelTitle"],
            "published_at": snippet.get("publishedAt"),
        }

        video.update(
            detailed_videos.get(
                video_id,
                {
                    "views": None,
                    "likes": None,
                    "comments": None,
                    "duration": None,
                },
            )
        )

        videos.append(video)

    return {
        "query": query,
        "count": len(videos),
        "videos": videos,
    }

# ============================================================
# TOOL: SEARCH TRENDING VIDEOS
# ============================================================

@mcp.tool()
def search_trending_videos(
    max_results: int = 50,
    region_code: str = "US",
) -> dict:
    """Получить популярные YouTube-видео и исключить нежелательные темы."""

    max_results = min(max(1, max_results), 50)

    # Получаем популярные видео YouTube по региону.
    response = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": region_code,
            "maxResults": max_results,
            "key": YOUTUBE_API_KEY,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    # Темы, которые мы пока не изучаем.
    excluded_words = [
        "politics",
        "political",
        "news",
        "breaking news",
        "podcast",
        "podcasts",
        "stream",
        "streams",
        "livestream",
        "live stream",
        "live streaming",
        "стрим",
        "стримы",
        "стриминг",
        "прямой эфир",
        "политика",
        "политический",
        "новости",
        "подкаст",
    ]

    # Категория News & Politics.
    excluded_category_ids = {
        "25",
    }

    videos = []

    for video in data.get("items", []):

        snippet = video.get("snippet", {})
        statistics = video.get("statistics", {})
        content_details = video.get("contentDetails", {})

        title = snippet.get("title", "")
        description = snippet.get("description", "")
        channel_title = snippet.get("channelTitle", "")
        category_id = snippet.get("categoryId")

        searchable_text = (
            f"{title} "
            f"{description} "
            f"{channel_title}"
        ).lower()

        # ----------------------------------------------------
        # ИСКЛЮЧАЕМ NEWS & POLITICS
        # ----------------------------------------------------

        if category_id in excluded_category_ids:
            continue

        # ----------------------------------------------------
        # ИСКЛЮЧАЕМ НЕЖЕЛАТЕЛЬНЫЕ ТЕМЫ ПО СЛОВАМ
        # ----------------------------------------------------

        if any(
            word in searchable_text
            for word in excluded_words
        ):
            continue

        # ----------------------------------------------------
        # СОХРАНЯЕМ ВИДЕО
        # ----------------------------------------------------

        videos.append({
            "video_id": video["id"],
            "title": title,
            "description": description,
            "channel_id": snippet.get("channelId"),
            "channel_title": channel_title,
            "published_at": snippet.get("publishedAt"),
            "category_id": category_id,
            "views": statistics.get("viewCount"),
            "likes": statistics.get("likeCount"),
            "comments": statistics.get("commentCount"),
            "duration": content_details.get("duration"),
        })

    return {
        "region_code": region_code,
        "count": len(videos),
        "videos": videos,
    }

# ============================================================
# SIMPLE HTTP ENDPOINT FOR CHECKING MCP TOOLS
# ============================================================

app = FastAPI()


@app.get("/mcp-tools")
async def mcp_tools():
    """
    Показать список зарегистрированных MCP-инструментов.
    Используется только для проверки сервера.
    """

    tools = []

    for tool in await mcp.list_tools():
        tools.append({
            "name": tool.name,
            "description": tool.description,
        })

    return {
        "count": len(tools),
        "tools": tools,
    }


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))

    mcp.run(
        transport="streamable-http"
    )
