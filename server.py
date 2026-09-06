import os
import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "YouTube Statistics",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "10000"))
)

YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]


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


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
