import os
import requests

from datetime import datetime, timedelta, timezone

from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI


# =========================================================
# MCP
# =========================================================

mcp = FastMCP(
    "YouTube Statistics",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "10000"))
)


YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]


# =========================================================
# РЕГИОНЫ И ЯЗЫКИ
# =========================================================

REGION_CONFIG = {
    "US": {
        "language": "en",
        "queries": [
            "how to|review|tutorial|tips|ideas",
            "new|best|interesting|amazing|experiment",
            "technology|business|science|education",
            "food|travel|fitness|home|DIY",
            "animals|gaming|cars|beauty|lifestyle",
        ],
    },

    "RU": {
        "language": "ru",
        "queries": [
            "как сделать|обзор|урок|советы|идеи",
            "новое|лучшее|интересное|эксперимент",
            "технологии|бизнес|наука|образование",
            "еда|путешествия|фитнес|дом|DIY",
            "животные|игры|авто|красота|лайфстайл",
        ],
    },

    "IN": {
        "language": "en",
        "queries": [
            "how to|review|tutorial|tips|ideas",
            "new|best|interesting|amazing|experiment",
            "technology|business|science|education",
            "food|travel|fitness|home|DIY",
            "gaming|cars|beauty|lifestyle|india",
        ],
    },

    "ZA": {
        "language": "en",
        "queries": [
            "how to|review|tutorial|tips|ideas",
            "new|best|interesting|amazing|experiment",
            "technology|business|science|education",
            "food|travel|fitness|home|DIY",
            "animals|gaming|cars|beauty|lifestyle",
        ],
    },

    "CN": {
        "language": "zh-Hans",
        "queries": [
            "怎么做|教程|技巧|方法|创意",
            "最新|最好|有趣|实验|推荐",
            "科技|商业|科学|教育",
            "美食|旅行|健身|家居|DIY",
            "动物|游戏|汽车|美容|生活",
        ],
    },
}


# =========================================================
# ИСКЛЮЧЕНИЯ
# =========================================================

EXCLUDED_WORDS = [
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

    "政治",
    "新闻",
    "播客",
    "直播",
]

EXCLUDED_CATEGORY_IDS = {"25"}


# =========================================================
# СТАТИСТИКА КАНАЛА
# =========================================================

@mcp.tool()
def get_channel_stats(channel_id: str) -> dict:

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
        return {
            "error": "Канал не найден"
        }

    channel = data["items"][0]

    snippet = channel.get("snippet", {})
    statistics = channel.get("statistics", {})

    return {
        "channel_id": channel.get("id"),
        "title": snippet.get("title"),
        "description": snippet.get("description"),
        "published_at": snippet.get("publishedAt"),
        "subscribers": statistics.get("subscriberCount"),
        "views": statistics.get("viewCount"),
        "videos": statistics.get("videoCount"),
    }


# =========================================================
# ПОИСК КАНАЛОВ
# =========================================================

@mcp.tool()
def search_channels(
    query: str,
    max_results: int = 20
) -> dict:

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

        snippet = item.get("snippet", {})

        channels.append({
            "channel_id": item.get("id", {}).get("channelId"),
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "published_at": snippet.get("publishedAt"),
        })

    return {
        "query": query,
        "count": len(channels),
        "channels": channels,
    }


# =========================================================
# ПОИСК ВИДЕО
# =========================================================

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

    max_results = min(max(1, max_results), 50)

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

    videos = []

    video_ids = []

    for item in data.get("items", []):

        video_id = item.get("id", {}).get("videoId")

        if not video_id:
            continue

        video_ids.append(video_id)

        snippet = item.get("snippet", {})

        videos.append({
            "video_id": video_id,
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "channel_id": snippet.get("channelId"),
            "channel_title": snippet.get("channelTitle", ""),
            "published_at": snippet.get("publishedAt"),
        })


    if not video_ids:

        return {
            "query": query,
            "count": 0,
            "videos": [],
        }


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


    result_videos = []

    for video in videos:

        detailed = detailed_videos.get(
            video["video_id"]
        )

        if not detailed:
            continue

        snippet = detailed.get("snippet", {})
        statistics = detailed.get("statistics", {})
        content_details = detailed.get("contentDetails", {})

        result_videos.append({
            **video,
            "views": statistics.get("viewCount"),
            "likes": statistics.get("likeCount"),
            "comments": statistics.get("commentCount"),
            "duration": content_details.get("duration"),
            "category_id": snippet.get("categoryId"),
        })


    return {
        "query": query,
        "count": len(result_videos),
        "videos": result_videos,
    }


# =========================================================
# 🔥 ТРЕНДЫ YOUTUBE
# =========================================================

@mcp.tool()
def search_trending_videos(
    max_results: int = 50,
    region_code: str = "US",
) -> dict:

    max_results = min(max(1, max_results), 50)

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

        if category_id in EXCLUDED_CATEGORY_IDS:
            continue

        if any(
            word in searchable_text
            for word in EXCLUDED_WORDS
        ):
            continue

        videos.append({
            "video_id": video.get("id"),
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
        })

    return {
        "region_code": region_code,
        "count": len(videos),
        "videos": videos,
    }


# =========================================================
# 🚀 РАДАР РОСТА
# =========================================================

@mcp.tool()
def search_radar_videos(
    max_results: int = 50,
    region_code: str = "US",
    hours_back: int = 72,
) -> dict:

    max_results = min(max(1, max_results), 50)

    hours_back = min(
        max(1, hours_back),
        168
    )


    region_code = region_code.upper()

    config = REGION_CONFIG.get(
        region_code,
        REGION_CONFIG["US"]
    )

    relevance_language = config["language"]

    query_groups = config["queries"]


    published_after = (
        datetime.now(timezone.utc)
        - timedelta(hours=hours_back)
    ).isoformat().replace("+00:00", "Z")


    found_videos = {}


    # ---------------------------------------------------------
    # Ищем свежие видео по нескольким тематическим группам
    # ---------------------------------------------------------

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
                "relevanceLanguage": relevance_language,
                "key": YOUTUBE_API_KEY,
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()


        for item in data.get("items", []):

            video_id = item.get(
                "id",
                {}
            ).get("videoId")

            if not video_id:
                continue


            snippet = item.get(
                "snippet",
                {}
            )


            found_videos[video_id] = {
                "video_id": video_id,
                "title": snippet.get(
                    "title",
                    ""
                ),
                "description": snippet.get(
                    "description",
                    ""
                ),
                "channel_id": snippet.get(
                    "channelId"
                ),
                "channel_title": snippet.get(
                    "channelTitle",
                    ""
                ),
                "published_at": snippet.get(
                    "publishedAt"
                ),
            }


    if not found_videos:

        return {
            "region_code": region_code,
            "language": relevance_language,
            "hours_back": hours_back,
            "count": 0,
            "videos": [],
        }


    # ---------------------------------------------------------
    # Получаем подробную статистику
    # ---------------------------------------------------------

    video_ids = list(
        found_videos.keys()
    )

    detailed_videos = {}


    for start in range(
        0,
        len(video_ids),
        50
    ):

        batch = video_ids[
            start:start + 50
        ]


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


        for video in stats_data.get(
            "items",
            []
        ):

            detailed_videos[
                video["id"]
            ] = video


    # ---------------------------------------------------------
    # Рассчитываем скорость роста
    # ---------------------------------------------------------

    now = datetime.now(
        timezone.utc
    )

    radar_videos = []


    for video_id, base_video in found_videos.items():

        video = detailed_videos.get(
            video_id
        )

        if not video:
            continue


        snippet = video.get(
            "snippet",
            {}
        )

        statistics = video.get(
            "statistics",
            {}
        )

        content_details = video.get(
            "contentDetails",
            {}
        )


        title = snippet.get(
            "title",
            base_video["title"]
        )

        description = snippet.get(
            "description",
            base_video["description"]
        )

        channel_title = snippet.get(
            "channelTitle",
            base_video["channel_title"]
        )

        category_id = snippet.get(
            "categoryId"
        )


        searchable_text = (
            f"{title} "
            f"{description} "
            f"{channel_title}"
        ).lower()


        # -----------------------------------------------------
        # Исключаем новости / политику / подкасты / стримы
        # -----------------------------------------------------

        if category_id in EXCLUDED_CATEGORY_IDS:
            continue


        if any(
            word in searchable_text
            for word in EXCLUDED_WORDS
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
                published_at.replace(
                    "Z",
                    "+00:00"
                )
            )

        except ValueError:

            continue


        age_hours = (
            now - published_dt
        ).total_seconds() / 3600


        age_hours = max(
            age_hours,
            0.1
        )


        try:

            views = int(
                statistics.get(
                    "viewCount",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            views = 0


        # -----------------------------------------------------
        # Минимальный порог просмотров
        # -----------------------------------------------------

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


        # -----------------------------------------------------
        # Скорость
        # -----------------------------------------------------

        views_per_hour = (
            views / age_hours
        )


        radar_videos.append({

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

            "likes": statistics.get(
                "likeCount"
            ),

            "comments": statistics.get(
                "commentCount"
            ),

            "duration": content_details.get(
                "duration"
            ),

            "category_id": category_id,

            "age_hours": round(
                age_hours,
                1
            ),

            "views_per_hour": round(
                views_per_hour
            ),

        })


    # ---------------------------------------------------------
    # Сортировка по скорости
    # ---------------------------------------------------------

    radar_videos.sort(
        key=lambda video:
            video["views_per_hour"],
        reverse=True
    )


    radar_videos = radar_videos[
        :max_results
    ]


    return {

        "region_code": region_code,

        "language": relevance_language,

        "hours_back": hours_back,

        "count": len(
            radar_videos
        ),

        "videos": radar_videos,

    }


# =========================================================
# ТЕСТОВЫЙ FASTAPI
# =========================================================

app = FastAPI()


@app.get("/mcp-tools")
async def mcp_tools():

    return {
        "message": "MCP server is running"
    }


# =========================================================
# ЗАПУСК
# =========================================================

if __name__ == "__main__":

    mcp.run(
        transport="streamable-http"
    )
