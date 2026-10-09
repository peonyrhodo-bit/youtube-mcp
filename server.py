import os
import logging
from typing import Any

import requests
from mcp.server.fastmcp import FastMCP


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

PORT = int(os.getenv("PORT", "8000"))
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger("youtube-mcp")


# ---------------------------------------------------------
# Errors
# ---------------------------------------------------------

class YouTubeQuotaError(Exception):
    """Raised when YouTube API quota/rate limit is reached."""


# ---------------------------------------------------------
# MCP
# ---------------------------------------------------------

mcp = FastMCP(
    "YouTube Statistics",
    host="0.0.0.0",
    port=PORT,
)


# ---------------------------------------------------------
# YouTube API helper
# ---------------------------------------------------------

def youtube_get(
    endpoint: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not YOUTUBE_API_KEY:
        raise RuntimeError("YOUTUBE_API_KEY is not configured")

    safe_params = dict(params or {})
    safe_params["key"] = YOUTUBE_API_KEY

    url = f"{YOUTUBE_API_BASE}/{endpoint}"

    try:
        response = requests.get(
            url,
            params=safe_params,
            timeout=30,
        )

    except requests.RequestException as exc:
        logger.error(
            "YouTube request failed: %s",
            type(exc).__name__,
        )
        raise RuntimeError("YouTube API request failed") from exc

    if response.status_code in (403, 429):
        try:
            data = response.json()
        except Exception:
            data = {}

        reasons = []

        for error in data.get("error", {}).get("errors", []):
            reason = error.get("reason")
            if reason:
                reasons.append(reason)

        message = data.get("error", {}).get("message", "")

        quota_reasons = {
            "quotaExceeded",
            "dailyLimitExceeded",
            "rateLimitExceeded",
            "userRateLimitExceeded",
        }

        if response.status_code == 429 or any(
            reason in quota_reasons for reason in reasons
        ):
            logger.warning(
                "YouTube quota/rate limit reached for endpoint=%s",
                endpoint,
            )
            raise YouTubeQuotaError(
                "YouTube API quota or rate limit reached"
            )

        logger.error(
            "YouTube API returned HTTP %s for endpoint=%s",
            response.status_code,
            endpoint,
        )

        raise RuntimeError(
            "YouTube API authorization/request error"
        )

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        logger.error(
            "YouTube API returned HTTP %s for endpoint=%s",
            response.status_code,
            endpoint,
        )
        raise RuntimeError(
            "YouTube API request failed"
        ) from exc

    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError(
            "YouTube API returned invalid JSON"
        ) from exc


# ---------------------------------------------------------
# Video statistics
# ---------------------------------------------------------

@mcp.tool()
def get_video_stats(video_ids: list[str]) -> dict[str, Any]:
    """
    Get statistics for up to 50 YouTube videos.
    """

    if not video_ids:
        return {"items": []}

    video_ids = list(dict.fromkeys(video_ids))[:50]

    result = youtube_get(
        "videos",
        {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(video_ids),
        },
    )
    result["_quota"] = {"search_calls": 0, "quota_units": 1, "videos_list_units": 1}
    return result


# ---------------------------------------------------------
# Channel statistics
# ---------------------------------------------------------

@mcp.tool()
def get_channel_stats(channel_id: str) -> dict[str, Any]:
    """
    Get statistics for one YouTube channel.
    """

    if not channel_id:
        raise ValueError("channel_id is required")

    result = youtube_get(
        "channels",
        {
            "part": "snippet,statistics,contentDetails",
            "id": channel_id,
        },
    )
    result["_quota"] = {"search_calls": 0, "quota_units": 1, "channels_list_units": 1}
    return result


# ---------------------------------------------------------
# Search channels
# ---------------------------------------------------------

@mcp.tool()
def search_channels(
    query: str,
    max_results: int = 10,
) -> dict[str, Any]:
    """
    Search YouTube channels.
    """

    max_results = max(1, min(max_results, 50))

    result = youtube_get(
        "search",
        {
            "part": "snippet",
            "q": query,
            "type": "channel",
            "maxResults": max_results,
        },
    )
    result["_quota"] = {"search_calls": 1, "quota_units": 100, "search_list_units": 100}
    return result


# ---------------------------------------------------------
# Search videos
# ---------------------------------------------------------

@mcp.tool()
def search_videos(
    query: str,
    max_results: int = 10,
    region_code: str | None = None,
    relevance_language: str | None = None,
    published_after: str | None = None,
    order: str = "relevance",
) -> dict[str, Any]:
    """
    Search YouTube videos and enrich results with statistics.
    """

    max_results = max(1, min(max_results, 50))

    params: dict[str, Any] = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": order,
    }

    if region_code:
        params["regionCode"] = region_code

    if relevance_language:
        params["relevanceLanguage"] = relevance_language

    if published_after:
        params["publishedAfter"] = published_after

    search_result = youtube_get(
        "search",
        params,
    )

    items = search_result.get("items", [])

    video_ids = [
        item.get("id", {}).get("videoId")
        for item in items
        if item.get("id", {}).get("videoId")
    ]

    if not video_ids:
        return {
            "items": items,
            "_quota": {
                "search_calls": 1,
                "quota_units": 100,
                "search_list_units": 100,
                "videos_list_units": 0,
            },
        }
    stats_result = get_video_stats(video_ids)

    stats_by_id = {
        item.get("id"): item
        for item in stats_result.get("items", [])
        if item.get("id")
    }

    enriched = []

    for item in items:
        video_id = item.get("id", {}).get("videoId")

        if video_id and video_id in stats_by_id:
            enriched.append(stats_by_id[video_id])
        else:
            enriched.append(item)

    return {
        "items": enriched,
        "_quota": {
            "search_calls": 1,
            "quota_units": 101,
            "search_list_units": 100,
            "videos_list_units": 1,
        },
    }


# ---------------------------------------------------------
# Trending videos
# ---------------------------------------------------------

@mcp.tool()
def search_trending_videos(
    max_results: int = 50,
    region_code: str = "US",
) -> dict[str, Any]:
    """
    Get trending YouTube videos.
    """

    max_results = max(1, min(max_results, 50))

    result = youtube_get(
        "videos",
        {
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": region_code,
            "maxResults": max_results,
        },
    )

    filtered = []

    excluded_categories = {"25"}

    excluded_words = {
        "politics",
        "political",
        "news",
        "breaking news",
        "election",
        "government",
        "president",
        "podcast",
        "live stream",
        "livestream",
    }

    for item in result.get("items", []):
        snippet = item.get("snippet", {})

        category_id = str(
            snippet.get("categoryId", "")
        )

        if category_id in excluded_categories:
            continue

        text = " ".join(
            [
                str(snippet.get("title", "")),
                str(snippet.get("description", "")),
            ]
        ).lower()

        if any(
            word in text
            for word in excluded_words
        ):
            continue

        filtered.append(item)

    result["items"] = filtered
    result["_quota"] = {"search_calls": 0, "quota_units": 1, "videos_list_units": 1}

    return result


# ---------------------------------------------------------
# Radar configuration
# ---------------------------------------------------------

LANGUAGE_CONFIG = {
    "ru": {
        "region_code": "RU",
        "relevance_language": "ru",
        "queries": [
            "тренды",
            "искусственный интеллект технологии",
            "новые технологии",
            "образование интересное",
        ],
    },
    "en": {
        "region_code": "US",
        "relevance_language": "en",
        "queries": [
            "trends",
            "artificial intelligence technology",
            "new technology",
            "interesting education",
        ],
    },
    "hi": {
        "region_code": "IN",
        "relevance_language": "hi",
        "queries": [
            "ट्रेंड",
            "कृत्रिम बुद्धिमत्ता तकनीक",
            "नई तकनीक",
            "शिक्षा रोचक",
        ],
    },
    "zh": {
        "region_code": "TW",
        "relevance_language": "zh",
        "queries": [
            "趋势",
            "人工智能 科技",
            "新技术",
            "有趣 教育",
        ],
    },
    "ja": {
        "region_code": "JP",
        "relevance_language": "ja",
        "queries": [
            "トレンド",
            "人工知能 テクノロジー",
            "最新技術",
            "面白い 教育",
        ],
    },
    "ko": {
        "region_code": "KR",
        "relevance_language": "ko",
        "queries": [
            "트렌드",
            "인공지능 기술",
            "최신 기술",
            "흥미로운 교육",
        ],
    },
    "es": {
        "region_code": "ES",
        "relevance_language": "es",
        "queries": [
            "tendencias",
            "inteligencia artificial tecnología",
            "nuevas tecnologías",
            "educación interesante",
        ],
    },
    "pt": {
        "region_code": "BR",
        "relevance_language": "pt",
        "queries": [
            "tendências",
            "inteligência artificial tecnologia",
            "novas tecnologias",
            "educação interessante",
        ],
    },
    "ar": {
        "region_code": "SA",
        "relevance_language": "ar",
        "queries": [
            "اتجاهات",
            "الذكاء الاصطناعي والتكنولوجيا",
            "تقنيات جديدة",
            "تعليم ممتع",
        ],
    },
    "de": {
        "region_code": "DE",
        "relevance_language": "de",
        "queries": [
            "Trends",
            "künstliche Intelligenz Technologie",
            "neue Technologien",
            "interessante Bildung",
        ],
    },
    "fr": {
        "region_code": "FR",
        "relevance_language": "fr",
        "queries": [
            "tendances",
            "intelligence artificielle technologie",
            "nouvelles technologies",
            "éducation intéressante",
        ],
    },
    "it": {
        "region_code": "IT",
        "relevance_language": "it",
        "queries": [
            "tendenze",
            "intelligenza artificiale tecnologia",
            "nuove tecnologie",
            "educazione interessante",
        ],
    },
    "tr": {
        "region_code": "TR",
        "relevance_language": "tr",
        "queries": [
            "trendler",
            "yapay zeka teknoloji",
            "yeni teknolojiler",
            "ilginç eğitim",
        ],
    },
    "id": {
        "region_code": "ID",
        "relevance_language": "id",
        "queries": [
            "tren",
            "kecerdasan buatan teknologi",
            "teknologi terbaru",
            "pendidikan menarik",
        ],
    },
    "vi": {
        "region_code": "VN",
        "relevance_language": "vi",
        "queries": [
            "xu hướng",
            "trí tuệ nhân tạo công nghệ",
            "công nghệ mới",
            "giáo dục thú vị",
        ],
    },
    "th": {
        "region_code": "TH",
        "relevance_language": "th",
        "queries": [
            "เทรนด์",
            "ปัญญาประดิษฐ์ เทคโนโลยี",
            "เทคโนโลยีใหม่",
            "การศึกษาน่าสนใจ",
        ],
    },
    "pl": {
        "region_code": "PL",
        "relevance_language": "pl",
        "queries": [
            "trendy",
            "sztuczna inteligencja technologia",
            "nowe technologie",
            "ciekawa edukacja",
        ],
    },
}

RADAR_EXCLUDED_WORDS = {
    "politics",
    "political",
    "election",
    "government",
    "president",
    "news",
    "breaking news",
}

RADAR_EXCLUDED_CATEGORY_IDS = {
    "25",
}


# ---------------------------------------------------------
# Radar
# ---------------------------------------------------------

@mcp.tool()
def search_radar_videos(
    languages: list[str] | None = None,
    queries: list[str] | None = None,
    max_results_per_query: int = 10,
) -> dict[str, Any]:

    """
    Search YouTube for emerging videos.

    The Director provides research languages and, when available,
    its own search queries.

    There is no artificial search-count limit here.
    Real YouTube quota protection remains handled by the
    underlying YouTube API / quota mechanism.
    """

    if languages is None:
        languages = ["ru"]

    max_results_per_query = max(
        1,
        min(
            max_results_per_query,
            10,
        ),
    )

    results: list[dict[str, Any]] = []

    search_calls_used = 0
    other_units_used = 0
    
    from datetime import datetime, timezone

    now = datetime.now(
        timezone.utc
    )

    for language in languages:

        config = LANGUAGE_CONFIG.get(
            language
        )

        if not config:
            continue

        if queries:
            language_queries = queries
        else:
            language_queries = config[
                "queries"
            ]

        for query in language_queries:

            try:

                data = search_videos(
                    query=query,
                    max_results=(
                        max_results_per_query
                    ),
                    region_code=config[
                        "region_code"
                    ],
                    relevance_language=config[
                        "relevance_language"
                    ],
                    order="date",
                )

                quota_data = data.get(
                    "_quota",
                    {},
                )

                search_calls_used += int(
                    quota_data.get(
                        "search_calls",
                        0,
                    )
                )

                other_units_used += int(
                    quota_data.get(
                        "other_units",
                        0,
                    )
                )
            
            except YouTubeQuotaError:

                logger.warning(
                    "Radar stopped because "
                    "YouTube quota was reached"
                )

                return {
                    "items": results,
                    "quota_exceeded": True,
                    "_quota": {
                        "search_calls": search_calls_used,
                        "other_units": other_units_used,
                    },
                    "message": (
                        "YouTube quota or rate limit reached"
                    ),
                }

            except Exception as exc:

                logger.warning(
                    "Radar query failed: %s (%s)",
                    query,
                    type(exc).__name__,
                )

                continue

            for item in data.get(
                "items",
                [],
            ):

                snippet = item.get(
                    "snippet",
                    {},
                )

                statistics = item.get(
                    "statistics",
                    {},
                )

                category_id = str(
                    snippet.get(
                        "categoryId",
                        "",
                    )
                )

                if (
                    category_id
                    in RADAR_EXCLUDED_CATEGORY_IDS
                ):
                    continue

                title = str(
                    snippet.get(
                        "title",
                        "",
                    )
                )

                description = str(
                    snippet.get(
                        "description",
                        "",
                    )
                )

                searchable_text = (
                    f"{title} {description}"
                ).lower()

                if any(
                    word in searchable_text
                    for word in RADAR_EXCLUDED_WORDS
                ):
                    continue

                published_at = snippet.get(
                    "publishedAt"
                )

                age_hours = None

                if published_at:

                    try:

                        published = (
                            datetime.fromisoformat(
                                published_at.replace(
                                    "Z",
                                    "+00:00",
                                )
                            )
                        )

                        age_hours = max(
                            (
                                now
                                - published
                            ).total_seconds()
                            / 3600,
                            0.01,
                        )

                    except Exception:

                        age_hours = None

                try:

                    views = int(
                        statistics.get(
                            "viewCount",
                            0,
                        )
                    )

                except Exception:

                    views = 0

                try:

                    likes = int(
                        statistics.get(
                            "likeCount",
                            0,
                        )
                    )

                except Exception:

                    likes = 0

                try:

                    comments = int(
                        statistics.get(
                            "commentCount",
                            0,
                        )
                    )

                except Exception:

                    comments = 0

                views_per_hour = None

                if age_hours:

                    views_per_hour = (
                        views
                        / age_hours
                    )

                engagement = 0.0

                if views > 0:

                    engagement = (
                        likes
                        + comments
                    ) / views

                enriched = dict(
                    item
                )

                enriched["_radar"] = {
                    "language": language,
                    "query": query,
                    "age_hours": age_hours,
                    "views": views,
                    "views_per_hour": (
                        views_per_hour
                    ),
                    "engagement": engagement,
                }

                results.append(
                    enriched
                )

    results.sort(
        key=lambda item: (
            item.get(
                "_radar",
                {},
            ).get(
                "views_per_hour"
            )
            or 0
        ),
        reverse=True,
    )

    return {
        "items": results,
        "quota_exceeded": False,
        "_quota": {
            "search_calls": search_calls_used,
            "other_units": other_units_used,
        },
    }
 
# ---------------------------------------------------------
# Run MCP server
# ---------------------------------------------------------

if __name__ == "__main__":
    logger.info(
        "Starting YouTube MCP server on port %s",
        PORT,
    )

    mcp.run(
        transport="streamable-http",
    )
