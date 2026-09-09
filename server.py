import os
import requests
from mcp.server.fastmcp import FastMCP


PORT = int(os.environ.get("PORT", "10000"))
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

if not YOUTUBE_API_KEY:
    raise RuntimeError("YOUTUBE_API_KEY is not set")


mcp = FastMCP(
    "YouTube Statistics",
    host="0.0.0.0",
    port=PORT,
)


YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


def youtube_get(endpoint, params):
    params = dict(params)
    params["key"] = YOUTUBE_API_KEY

    try:
        response = requests.get(
            f"{YOUTUBE_API_BASE}/{endpoint}",
            params=params,
            timeout=30,
        )

        response.raise_for_status()
        return response.json()

    except Exception as error:
        print(
            "YOUTUBE_GET_ERROR",
            {
                "endpoint": endpoint,
                "params": params,
                "error_type": type(error).__name__,
                "error": str(error),
            },
            flush=True,
        )

        raise


@mcp.tool()
def get_video_stats(video_ids: list[str]) -> list[dict]:
    """
    Get statistics and basic information for up to 50 YouTube videos.
    """

    if not video_ids:
        return []

    if len(video_ids) > 50:
        raise ValueError("Maximum 50 video IDs are allowed")

    data = youtube_get(
        "videos",
        {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(video_ids),
        },
    )

    result = []

    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})

        result.append(
            {
                "video_id": item.get("id"),
                "title": snippet.get("title"),
                "channel_id": snippet.get("channelId"),
                "channel_title": snippet.get("channelTitle"),
                "published_at": snippet.get("publishedAt"),
                "views": int(statistics.get("viewCount", 0)),
                "likes": int(statistics.get("likeCount", 0)),
                "comments": int(statistics.get("commentCount", 0)),
                "duration": content_details.get("duration"),
            }
        )

    return result


@mcp.tool()
def get_channel_stats(channel_id: str) -> dict:
    """
    Get statistics and basic information about a YouTube channel.
    """

    if not channel_id:
        raise ValueError("channel_id is required")

    data = youtube_get(
        "channels",
        {
            "part": "snippet,statistics",
            "id": channel_id,
        },
    )

    items = data.get("items", [])

    if not items:
        return {
            "channel_id": channel_id,
            "found": False,
        }

    item = items[0]
    snippet = item.get("snippet", {})
    statistics = item.get("statistics", {})

    return {
        "channel_id": item.get("id"),
        "found": True,
        "title": snippet.get("title"),
        "description": snippet.get("description"),
        "published_at": snippet.get("publishedAt"),
        "subscribers": int(statistics.get("subscriberCount", 0)),
        "views": int(statistics.get("viewCount", 0)),
        "videos": int(statistics.get("videoCount", 0)),
    }


@mcp.tool()
def search_channels(
    query: str,
    max_results: int = 10,
) -> list[dict]:
    """
    Search YouTube channels by keyword.
    """

    if not query:
        raise ValueError("query is required")

    max_results = max(1, min(max_results, 50))

    data = youtube_get(
        "search",
        {
            "part": "snippet",
            "q": query,
            "type": "channel",
            "maxResults": max_results,
        },
    )

    result = []

    for item in data.get("items", []):
        snippet = item.get("snippet", {})

        result.append(
            {
                "channel_id": item.get("snippet", {}).get("channelId"),
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "published_at": snippet.get("publishedAt"),
            }
        )

    return result


@mcp.tool()
def search_videos(
    query: str,
    max_results: int = 10,
    published_after: str | None = None,
    published_before: str | None = None,
    region_code: str | None = None,
    relevance_language: str | None = None,
    order: str = "viewCount",
) -> list[dict]:
    """
    Search YouTube videos and return their statistics.
    """

    if not query:
        raise ValueError("query is required")

    max_results = max(1, min(max_results, 50))

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": order,
    }

    if published_after:
        params["publishedAfter"] = published_after

    if published_before:
        params["publishedBefore"] = published_before

    if region_code:
        params["regionCode"] = region_code

    if relevance_language:
        params["relevanceLanguage"] = relevance_language

    search_data = youtube_get("search", params)

    video_ids = [
        item.get("id", {}).get("videoId")
        for item in search_data.get("items", [])
        if item.get("id", {}).get("videoId")
    ]

    if not video_ids:
        return []

    return get_video_stats(video_ids)


@mcp.tool()
def search_trending_videos(
    max_results: int = 50,
    region_code: str = "US",
) -> list[dict]:
    """
    Get currently popular YouTube videos for a region.
    """

    max_results = max(1, min(max_results, 50))

    data = youtube_get(
        "videos",
        {
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": region_code,
            "maxResults": max_results,
        },
    )

    result = []

    excluded_words = [
        "politics",
        "political",
        "news",
        "podcast",
        "live",
        "election",
        "president",
        "government",
        "политика",
        "новости",
        "подкаст",
        "прямой эфир",
    ]

    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})

        title = snippet.get("title", "")
        description = snippet.get("description", "")

        text = f"{title} {description}".lower()

        if any(word in text for word in excluded_words):
            continue

        category_id = snippet.get("categoryId")

        if category_id == "25":
            continue

        result.append(
            {
                "video_id": item.get("id"),
                "title": title,
                "channel_id": snippet.get("channelId"),
                "channel_title": snippet.get("channelTitle"),
                "published_at": snippet.get("publishedAt"),
                "views": int(statistics.get("viewCount", 0)),
                "likes": int(statistics.get("likeCount", 0)),
                "comments": int(statistics.get("commentCount", 0)),
                "duration": content_details.get("duration"),
                "category_id": category_id,
            }
        )

    return result


LANGUAGE_CONFIG = {
    "ru": [
        "новинки",
        "интересное",
        "тренды",
        "истории",
        "фильмы",
        "технологии",
        "искусственный интеллект",
        "обучение",
    ],
    "en": [
        "trending",
        "interesting",
        "stories",
        "movies",
        "technology",
        "artificial intelligence",
        "education",
    ],
    "hi": [
        "trending",
        "interesting",
        "stories",
        "technology",
        "education",
    ],
    "zh-Hans": [
        "热门",
        "趋势",
        "故事",
        "电影",
        "科技",
        "人工智能",
        "教育",
    ],
}


RADAR_EXCLUDED_WORDS = [
    "politics",
    "political",
    "election",
    "president",
    "government",
    "news",
    "breaking news",
    "политика",
    "политический",
    "выборы",
    "президент",
    "правительство",
    "новости",
    "срочные новости",
    "政治",
    "选举",
    "总统",
    "政府",
    "新闻",
]


RADAR_EXCLUDED_CATEGORY_IDS = {"25"}


@mcp.tool()
def search_radar_videos(
    max_results: int = 50,
    language: str = "ru",
    hours_back: int = 72,
) -> list[dict]:
    """
    Search recently published videos and rank them by views per hour.
    This is an early Growth Radar implementation.
    """

    max_results = max(1, min(max_results, 50))

    if language not in LANGUAGE_CONFIG:
        language = "ru"

    hours_back = max(1, min(hours_back, 24 * 30))

    from datetime import datetime, timedelta, timezone

    now_utc = datetime.now(timezone.utc)
    published_after = now_utc - timedelta(hours=hours_back)

    all_videos = []

    query_groups = LANGUAGE_CONFIG[language]

    per_query = max(5, min(20, max_results))

    for query in query_groups[:10]:
        try:
            videos = search_videos(
                query=query,
                max_results=per_query,
                published_after=published_after.isoformat(),
                relevance_language=language,
                order="date",
            )

            all_videos.extend(videos)

        except Exception:
            continue

    unique = {}

    for video in all_videos:
        video_id = video.get("video_id")

        if not video_id:
            continue

        unique[video_id] = video

    result = []

    for video in unique.values():
        title = video.get("title", "")
        description = video.get("description", "")

        text = f"{title} {description}".lower()

        if any(word in text for word in RADAR_EXCLUDED_WORDS):
            continue

        category_id = video.get("category_id")

        if category_id in RADAR_EXCLUDED_CATEGORY_IDS:
            continue

        published_at = video.get("published_at")

        if not published_at:
            continue

        try:
            published_dt = datetime.fromisoformat(
                published_at.replace("Z", "+00:00")
            )

            age_hours = max(
                (now_utc - published_dt).total_seconds() / 3600,
                0.05,
            )

        except Exception:
            continue

        views = int(video.get("views", 0))

        views_per_hour = views / age_hours

        likes = int(video.get("likes", 0))
        comments = int(video.get("comments", 0))

        engagement = 0.0

        if views > 0:
            engagement = (likes + comments) / views

        video["age_hours"] = round(age_hours, 2)
        video["views_per_hour"] = round(views_per_hour, 2)
        video["engagement_rate"] = round(engagement, 6)

        result.append(video)

    result.sort(
        key=lambda item: (
            item.get("views_per_hour", 0),
            item.get("views", 0),
        ),
        reverse=True,
    )

    return result[:max_results]


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
