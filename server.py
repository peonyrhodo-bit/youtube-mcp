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

from datetime import datetime, timedelta, timezone


@mcp.tool()
def search_radar_videos(
    max_results: int = 50,
    region_code: str = "US",
    hours_back: int = 72,
) -> dict:
    """Найти свежие быстрорастущие YouTube-видео и посчитать их текущий темп."""

    max_results = min(max(1, max_results), 50)
    hours_back = min(max(1, hours_back), 168)

    published_after = (
        datetime.now(timezone.utc) - timedelta(hours=hours_back)
    ).isoformat().replace("+00:00", "Z")

    # Несколько широких поисковых направлений,
    # чтобы радар не зависел от одной темы.
    query_groups = [
        "how to|review|tutorial|tips|ideas",
        "new|best|interesting|amazing|experiment",
        "technology|business|science|education",
        "food|travel|fitness|home|DIY",
        "animals|gaming|cars|beauty|lifestyle",
    ]

    # Что не хотим видеть в радаре.
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
    excluded_category_ids = {"25"}

    # Здесь собираем уникальные видео.
    found_videos = {}

    for query in query_groups:
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": 50,
                "order": "viewCount",
                "publishedAfter": published_after,
                "regionCode": region_code,
                "key": YOUTUBE_API_KEY,
            },
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

        for item in data.get("items", []):
            video_id = item.get("id", {}).get("videoId")

            if not video_id:
                continue

            snippet = item.get("snippet", {})

            found_videos[video_id] = {
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "channel_id": snippet.get("channelId"),
                "channel_title": snippet.get("channelTitle", ""),
                "published_at": snippet.get("publishedAt"),
            }

    if not found_videos:
        return {
            "region_code": region_code,
            "hours_back": hours_back,
            "count": 0,
            "videos": [],
        }

    # Получаем подробную статистику по найденным видео.
    video_ids = list(found_videos.keys())
    detailed_videos = {}

    for start in range(0, len(video_ids), 50):
        batch = video_ids[start:start + 50]

        stats_response = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(batch),
                "key": YOUTUBE_API_KEY,
            },
            timeout=30,
        )

        stats_response.raise_for_status()
        stats_data = stats_response.json()

        for video in stats_data.get("items", []):
            detailed_videos[video["id"]] = video

    now = datetime.now(timezone.utc)

    radar_videos = []

    for video_id, base_video in found_videos.items():
        video = detailed_videos.get(video_id)

        if not video:
            continue

        snippet = video.get("snippet", {})
        statistics = video.get("statistics", {})
        content_details = video.get("contentDetails", {})

        title = snippet.get("title", base_video["title"])
        description = snippet.get(
            "description",
            base_video["description"]
        )

        channel_title = snippet.get(
            "channelTitle",
            base_video["channel_title"]
        )

        category_id = snippet.get("categoryId")

        # Текст, по которому дополнительно отсеиваем
        # новости, политику, подкасты и стримы.
        searchable_text = (
            f"{title} {description} {channel_title}"
        ).lower()

        if category_id in excluded_category_ids:
            continue

        if any(
            word in searchable_text
            for word in excluded_words
        ):
            continue

        published_at = snippet.get(
            "publishedAt",
            base_video["published_at"]
        )

        if not published_at:
            continue

        try:
            published_dt = datetime.fromisoformat(
                published_at.replace("Z", "+00:00")
            )
        except ValueError:
            continue

        # Возраст видео в часах.
        age_hours = (
            now - published_dt
        ).total_seconds() / 3600

        # Защита от деления на слишком маленькое число.
        age_hours = max(age_hours, 0.1)

        # Количество просмотров.
        try:
            views = int(
                statistics.get("viewCount", 0)
            )
        except (TypeError, ValueError):
            views = 0

        # -------------------------------------------------
        # ФИЛЬТР СЛАБЫХ ВИДЕО
        # -------------------------------------------------
        #
        # Чем старше видео, тем больше просмотров
        # мы ожидаем от него.
        #
        if age_hours <= 6:
            min_views = 100

        elif age_hours <= 12:
            min_views = 300

        elif age_hours <= 24:
            min_views = 500

        elif age_hours <= 48:
            min_views = 1000

        else:
            min_views = 2000

        # Если видео слишком слабое для своего возраста —
        # вообще не отправляем его в радар.
        if views < min_views:
            continue

        # -------------------------------------------------
        # РАСЧЁТ ТЕМПА
        # -------------------------------------------------

        # Это не прогноз.
        # Это текущая нормализация:
        # сколько просмотров в среднем приходится
        # на один час жизни видео.
        views_per_hour = views / age_hours

        # Условный эквивалент текущего темпа за 24 часа.
        # Это тоже НЕ прогноз.
        views_per_24h = views_per_hour * 24

        radar_videos.append(
            {
                "video_id": video_id,
                "title": title,
                "description": description,
                "channel_id": snippet.get(
                    "channelId",
                    base_video["channel_id"]
                ),
                "channel_title": channel_title,
                "published_at": published_at,

                "views": views,

                "likes": statistics.get("likeCount"),

                "comments": statistics.get(
                    "commentCount"
                ),

                "duration": content_details.get(
                    "duration"
                ),

                "category_id": category_id,

                # Возраст видео в часах.
                "age_hours": round(age_hours, 1),

                # Текущий темп просмотров.
                "views_per_hour": round(
                    views_per_hour
                ),

                # Эквивалент текущего темпа
                # за 24 часа.
                "views_per_24h": round(
                    views_per_24h
                ),
            }
        )

    # Самые быстрые видео — наверх.
    radar_videos.sort(
        key=lambda video: video["views_per_hour"],
        reverse=True,
    )

    # Оставляем только нужное количество.
    radar_videos = radar_videos[:max_results]

    return {
        "region_code": region_code,
        "hours_back": hours_back,
        "count": len(radar_videos),
        "videos": radar_videos,
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
