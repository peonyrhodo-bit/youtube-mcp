import os
import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "YouTube Statistics",
    stateless_http=True,
    json_response=True,
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


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http"
    )
