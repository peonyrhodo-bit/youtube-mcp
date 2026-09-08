python
import os
import requests

from datetime import datetime, timedelta, timezone

from mcp.server.fastmcp import FastMCP


mcp = FastMCP(
    "YouTube Statistics",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "10000")),
)


YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]


def youtube_get(endpoint: str, params: dict) -> dict:
    params = dict(params)
    params["key"] = YOUTUBE_API_KEY

    response = requests.get(
        f"https://www.googleapis.com/youtube/v3/{endpoint}",
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


@mcp.tool()
def get_video_stats(video_ids: list[str]) -> dict:
    """
    Получает свежую статистику для списка YouTube video IDs.

    Максимум 50 видео за один запрос.
    """

    if not video_ids:
        return {
            "videos": []
        }

    video_ids = video_ids[:50]

    data = youtube_get(
        "videos",
        {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(video_ids),
        },
    )

    videos = []

    for item in data.get("items", []):
        statistics = item.get("statistics", {})
        snippet = item.get("snippet", {})
        content_details = item.get("contentDetails", {})

        videos.append(
            {
                "video_id": item["id"],
                "title": snippet.get("title", ""),
                "channel_id": snippet.get("channelId"),
                "channel_title": snippet.get("channelTitle", ""),
                "published_at": snippet.get("publishedAt"),
                "views": int(statistics.get("viewCount", 0) or 0),
                "likes": int(statistics.get("likeCount", 0) or 0),
                "comments": int(statistics.get("commentCount", 0) or 0),
                "duration": content_details.get("duration"),
            }
        )

    return {
        "videos": videos
    }


@mcp.tool()
def get_channel_stats(channel_id: str) -> dict:
    """Получить статистику YouTube-канала."""

    channel_id = channel_id.strip()

    if not channel_id:
        return {
            "error": "channel_id не может быть пустым"
        }

    data = youtube_get(
        "channels",
        {
            "part": "snippet,statistics",
            "id": channel_id,
        },
    )

    if not data.get("items"):
        return {
            "error": "Канал не найден",
            "channel_id": channel_id,
        }

    channel = data["items"][0]

    snippet = channel.get("snippet", {})
    statistics = channel.get("statistics", {})

    return {
        "channel_id": channel_id,
        "title": snippet.get("title"),
        "description": snippet.get("description"),
        "published_at": snippet.get("publishedAt"),
        "subscribers": statistics.get("subscriberCount"),
        "views": statistics.get("viewCount"),
        "videos": statistics.get("videoCount"),
    }


@mcp.tool()
def search_channels(
    query: str,
    max_results: int = 20,
) -> dict:
    """Найти YouTube-каналы по поисковому запросу."""

    query = query.strip()

    if not query:
        return {
            "error": "query не может быть пустым"
        }

    max_results = min(max(1, max_results), 50)

    data = youtube_get(
        "search",
        {
            "part": "snippet",
            "q": query,
            "type": "channel",
            "maxResults": max_results,
        },
    )

    channels = []

    for item in data.get("items", []):
        snippet = item.get("snippet", {})

        channels.append(
            {
                "channel_id": item.get("id", {}).get("channelId"),
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "published_at": snippet.get("publishedAt"),
            }
        )

    return {
        "query": query,
        "count": len(channels),
        "channels": channels,
    }


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

    query = query.strip()

    if not query:
        return {
            "error": "query не может быть пустым"
        }

    max_results = min(max(1, max_results), 50)

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

    search_data = youtube_get(
        "search",
        params,
    )

    video_ids = []
    basic_videos = {}

    for item in search_data.get("items", []):
        video_id = item.get("id", {}).get("videoId")

        if not video_id:
            continue

        snippet = item.get("snippet", {})

        video_ids.append(video_id)

        basic_videos[video_id] = {
            "video_id": video_id,
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "channel_id": snippet.get("channelId"),
            "channel_title": snippet.get("channelTitle", ""),
            "published_at": snippet.get("publishedAt"),
        }

    if not video_ids:
        return {
            "query": query,
            "count": 0,
            "videos": [],
        }

    detailed_videos = {}

    for start in range(0, len(video_ids), 50):
        batch = video_ids[start:start + 50]

        data = youtube_get(
            "videos",
            {
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(batch),
            },
        )

        for video in data.get("items", []):
            detailed_videos[video["id"]] = video

    videos = []

    for video_id in video_ids:
        video = detailed_videos.get(video_id)

        if not video:
            continue

        snippet = video.get("snippet", {})
        statistics = video.get("statistics", {})
        content_details = video.get("contentDetails", {})

        videos.append(
            {
                "video_id": video_id,
                "title": snippet.get(
                    "title",
                    basic_videos[video_id]["title"],
                ),
                "description": snippet.get(
                    "description",
                    basic_videos[video_id]["description"],
                ),
                "channel_id": snippet.get(
                    "channelId",
                    basic_videos[video_id]["channel_id"],
                ),
                "channel_title": snippet.get(
                    "channelTitle",
                    basic_videos[video_id]["channel_title"],
                ),
                "published_at": snippet.get(
                    "publishedAt",
                    basic_videos[video_id]["published_at"],
                ),
                "views": statistics.get("viewCount"),
                "likes": statistics.get("likeCount"),
                "comments": statistics.get("commentCount"),
                "duration": content_details.get("duration"),
                "category_id": snippet.get("categoryId"),
                "default_language": snippet.get("defaultLanguage"),
            }
        )

    return {
        "query": query,
        "count": len(videos),
        "videos": videos,
    }


@mcp.tool()
def search_trending_videos(
    max_results: int = 50,
    region_code: str = "US",
) -> dict:
    """Получить актуальные YouTube-тренды по региону."""

    max_results = min(max(1, max_results), 50)

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

    excluded_category_ids = {
        "25"
    }

    data = youtube_get(
        "videos",
        {
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": region_code,
            "maxResults": max_results,
        },
    )

    videos = []

    for video in data.get("items", []):
        video_id = video.get("id")
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

        if category_id in excluded_category_ids:
            continue

        if any(
            word in searchable_text
            for word in excluded_words
        ):
            continue

        videos.append(
            {
                "video_id": video_id,
                "title": title,
                "description": description,
                "channel_id": snippet.get("channelId"),
                "channel_title": channel_title,
                "published_at": snippet.get("publishedAt"),
                "views": statistics.get("viewCount"),
                "likes": statistics.get("likeCount"),
                "comments": statistics.get("commentCount"),
                "duration": content_details.get("duration"),
                "category_id": category_id,
                "default_language": snippet.get("defaultLanguage"),
            }
        )

    return {
        "region_code": region_code,
        "count": len(videos),
        "videos": videos,
    }


LANGUAGE_CONFIG = {
    "ru": {
        "label": "Русский",
        "relevance_language": "ru",
        "query_groups": [
            "как|обзор|урок|советы|идеи",
            "новый|лучший|интересный|эксперимент",
            "технологии|бизнес|наука|образование",
            "еда|путешествия|фитнес|дом|DIY",
            "животные|игры|авто|красота|лайфстайл",
        ],
    },
    "en": {
        "label": "English",
        "relevance_language": "en",
        "query_groups": [
            "how to|review|tutorial|tips|ideas",
            "new|best|interesting|amazing|experiment",
            "technology|business|science|education",
            "food|travel|fitness|home|DIY",
            "animals|gaming|cars|beauty|lifestyle",
        ],
    },
    "hi": {
        "label": "हिन्दी",
        "relevance_language": "hi",
        "query_groups": [
            "कैसे|समीक्षा|ट्यूटोरियल|सलाह|विचार",
            "नया|सबसे अच्छा|रोचक|प्रयोग",
            "तकनीक|बिजनेस|विज्ञान|शिक्षा",
            "खाना|यात्रा|फिटनेस|घर|DIY",
            "जानवर|गेमिंग|कार|ब्यूटी|लाइफस्टाइल",
        ],
    },
    "zh-Hans": {
        "label": "中文",
        "relevance_language": "zh-Hans",
        "query_groups": [
            "教程|评测|技巧|建议|创意",
            "最新|最好|有趣|实验",
            "科技|商业|科学|教育",
            "美食|旅行|健身|家居|DIY",
            "动物|游戏|汽车|美容|生活",
        ],
    },
}


RADAR_EXCLUDED_WORDS = [
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

RADAR_EXCLUDED_CATEGORY_IDS = {
    "25"
}


@mcp.tool()
def search_radar_videos(
    max_results: int = 50,
    language: str = "ru",
    hours_back: int = 72,
) -> dict:
    """Найти свежие быстрорастущие YouTube-видео."""

    max_results = min(max(1, max_results), 50)
    hours_back = min(max(1, hours_back), 168)

    if language not in LANGUAGE_CONFIG:
        language = "en"

    config = LANGUAGE_CONFIG[language]

    published_after = (
        datetime.now(timezone.utc)
        - timedelta(hours=hours_back)
    ).isoformat().replace(
        "+00:00",
        "Z",
    )

    found_videos = {}

    for query in config["query_groups"]:
        search_data = youtube_get(
            "search",
            {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": 50,
                "order": "viewCount",
                "publishedAfter": published_after,
                "relevanceLanguage": config["relevance_language"],
            },
        )

        for item in search_data.get("items", []):
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
            "language": language,
            "language_label": config["label"],
            "hours_back": hours_back,
            "count": 0,
            "videos": [],
        }

    video_ids = list(found_videos.keys())
    detailed_videos = {}

    for start in range(0, len(video_ids), 50):
        batch = video_ids[start:start + 50]

        stats_data = youtube_get(
            "videos",
            {
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(batch),
            },
        )

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

        title = snippet.get(
            "title",
            base_video["title"],
        )

        description = snippet.get(
            "description",
            base_video["description"],
        )

        channel_title = snippet.get(
            "channelTitle",
            base_video["channel_title"],
        )

        category_id = snippet.get("categoryId")

        searchable_text = (
            f"{title} "
            f"{description} "
            f"{channel_title}"
        ).lower()

        if category_id in RADAR_EXCLUDED_CATEGORY_IDS:
            continue

        if any(
            word in searchable_text
            for word in RADAR_EXCLUDED_WORDS
        ):
            continue

        published_at = snippet.get(
            "publishedAt",
            base_video["published_at"],
        )

        if not published_at:
            continue

        try:
            published_dt = datetime.fromisoformat(
                published_at.replace(
                    "Z",
                    "+00:00",
                )
            )
        except ValueError:
            continue

        age_hours = (
            now - published_dt
        ).total_seconds() / 3600

        age_hours = max(
            age_hours,
            0.1,
        )

        try:
            views = int(
                statistics.get(
                    "viewCount",
                    0,
                )
            )
        except (TypeError, ValueError):
            views = 0

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

        if views < min_views:
            continue

        views_per_hour = views / age_hours

        radar_videos.append(
            {
                "video_id": video_id,
                "title": title,
                "description": description,
                "channel_id": snippet.get(
                    "channelId",
                    base_video["channel_id"],
                ),
                "channel_title": channel_title,
                "published_at": published_at,
                "views": views,
                "likes": statistics.get("likeCount"),
                "comments": statistics.get("commentCount"),
                "duration": content_details.get("duration"),
                "category_id": category_id,
                "default_language": snippet.get(
                    "defaultLanguage"
                ),
                "age_hours": round(
                    age_hours,
                    1,
                ),
                "views_per_hour": round(
                    views_per_hour
                ),
            }
        )

    radar_videos.sort(
        key=lambda video: video["views_per_hour"],
        reverse=True,
    )

    radar_videos = radar_videos[:max_results]

    return {
        "language": language,
        "language_label": config["label"],
        "hours_back": hours_back,
        "count": len(radar_videos),
        "videos": radar_videos,
    }


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http"
    )
