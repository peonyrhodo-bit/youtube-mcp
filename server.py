import json
import logging
import os
import re
from typing import Any

import requests
from fastmcp import FastMCP


# ============================================================
# CONFIG
# ============================================================

PORT = int(os.environ.get("PORT", "8000"))
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger("youtube-mcp")


# ============================================================
# MCP
# ============================================================

mcp = FastMCP(
    "YouTube Statistics",
    host="0.0.0.0",
    port=PORT,
)


# ============================================================
# ERRORS
# ============================================================

class YouTubeQuotaError(Exception):
    """YouTube quota or rate-limit error."""


# ============================================================
# HELPERS
# ============================================================

def sanitize_text(text: str) -> str:
    """
    Never allow the YouTube API key to appear in logs/errors.
    """
    if not text:
        return ""

    if YOUTUBE_API_KEY:
        text = text.replace(YOUTUBE_API_KEY, "***REDACTED***")

    return text


def parse_youtube_error(response: requests.Response) -> dict[str, Any]:
    """
    Extract a safe subset of the YouTube API error.
    Never returns the API key.
    """
    try:
        data = response.json()
    except Exception:
        return {
            "status": response.status_code,
            "reason": "",
            "message": sanitize_text(response.text[:500]),
        }

    error = data.get("error", {})
    reasons = []

    for item in error.get("errors", []):
        reason = item.get("reason")
        if reason:
            reasons.append(str(reason))

    return {
        "status": response.status_code,
        "reason": reasons[0] if reasons else "",
        "message": sanitize_text(
            str(error.get("message", ""))[:500]
        ),
    }


def is_quota_error(error_info: dict[str, Any]) -> bool:
    """
    Detect quota/rate-limit conditions.
    """
    status = error_info.get("status")
    reason = str(error_info.get("reason", ""))

    if status == 429:
        return True

    if status == 403 and reason in {
        "quotaExceeded",
        "dailyLimitExceeded",
        "rateLimitExceeded",
        "userRateLimitExceeded",
    }:
        return True

    return False


# ============================================================
# YOUTUBE HTTP
# ============================================================

def youtube_get(
    endpoint: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Perform a YouTube Data API GET request.

    IMPORTANT:
    The API key is added to the outgoing request,
    but is NEVER written to logs.
    """

    if not YOUTUBE_API_KEY:
        raise RuntimeError("YOUTUBE_API_KEY is not configured")

    request_params = dict(params or {})
    request_params["key"] = YOUTUBE_API_KEY

    url = f"{YOUTUBE_API_BASE}/{endpoint}"

    try:
        response = requests.get(
            url,
            params=request_params,
            timeout=30,
        )

    except requests.RequestException as exc:
        safe_error = sanitize_text(str(exc))

        logger.error(
            "YOUTUBE_HTTP_ERROR endpoint=%s error=%s",
            endpoint,
            safe_error,
        )

        raise RuntimeError(
            f"YouTube request failed: {safe_error}"
        ) from exc

    if not response.ok:
        error_info = parse_youtube_error(response)

        if is_quota_error(error_info):
            logger.warning(
                "YOUTUBE_QUOTA_OR_RATE_LIMIT endpoint=%s status=%s reason=%s",
                endpoint,
                error_info.get("status"),
                error_info.get("reason"),
            )

            raise YouTubeQuotaError(
                f"YouTube quota/rate limit: "
                f"{error_info.get('reason') or error_info.get('status')}"
            )

        logger.error(
            "YOUTUBE_API_ERROR endpoint=%s status=%s reason=%s message=%s",
            endpoint,
            error_info.get("status"),
            error_info.get("reason"),
            error_info.get("message"),
        )

        raise RuntimeError(
            f"YouTube API error: "
            f"{error_info.get('reason') or error_info.get('message')}"
        )

    try:
        return response.json()

    except ValueError as exc:
        logger.error(
            "YOUTUBE_INVALID_JSON endpoint=%s status=%s",
            endpoint,
            response.status_code,
        )

        raise RuntimeError(
            "YouTube returned invalid JSON"
        ) from exc


# ============================================================
# VIDEO STATS
# ============================================================

@mcp.tool()
def get_video_stats(video_ids: list[str]) -> dict[str, Any]:
    """
    Get statistics for up to 50 YouTube videos.
    """

    if not video_ids:
        return {
            "items": []
        }

    if len(video_ids) > 50:
        raise ValueError(
            "Maximum 50 video IDs per request"
        )

    clean_ids = [
        str(video_id).strip()
        for video_id in video_ids
        if str(video_id).strip()
    ]

    if not clean_ids:
        return {
            "items": []
        }

    data = youtube_get(
        "videos",
        {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(clean_ids),
        },
    )

    return data


# ============================================================
# CHANNEL STATS
# ============================================================

@mcp.tool()
def get_channel_stats(
    channel_id: str,
) -> dict[str, Any]:
    """
    Get statistics for a YouTube channel.
    """

    channel_id = str(channel_id).strip()

    if not channel_id:
        raise ValueError("channel_id is required")

    return youtube_get(
        "channels",
        {
            "part": "snippet,statistics,contentDetails",
            "id": channel_id,
        },
    )


# ============================================================
# SEARCH CHANNELS
# ============================================================

@mcp.tool()
def search_channels(
    query: str,
    max_results: int = 10,
) -> dict[str, Any]:
    """
    Search YouTube channels.
    """

    query = str(query).strip()

    if not query:
        raise ValueError("query is required")

    max_results = max(
        1,
        min(int(max_results), 50),
    )

    return youtube_get(
        "search",
        {
            "part": "snippet",
            "q": query,
            "type": "channel",
            "maxResults": max_results,
        },
    )


# ============================================================
# SEARCH VIDEOS
# ============================================================

@mcp.tool()
def search_videos(
    query: str,
    max_results: int = 10,
    region_code: str = "US",
    relevance_language: str | None = None,
) -> dict[str, Any]:
    """
    Search YouTube videos and enrich results with statistics.
    """

    query = str(query).strip()

    if not query:
        raise ValueError("query is required")

    max_results = max(
        1,
        min(int(max_results), 50),
    )

    params: dict[str, Any] = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "regionCode": region_code,
    }

    if relevance_language:
        params["relevanceLanguage"] = relevance_language

    search_data = youtube_get(
        "search",
        params,
    )

    items = search_data.get("items", [])

    video_ids = []

    for item in items:
        video_id = (
            item.get("id", {})
            .get("videoId")
        )

        if video_id:
            video_ids.append(video_id)

    if not video_ids:
        return {
            "items": items
        }

    stats_data = get_video_stats(video_ids)

    stats_by_id = {
        item.get("id"): item
        for item in stats_data.get("items", [])
    }

    enriched_items = []

    for item in items:
        video_id = (
            item.get("id", {})
            .get("videoId")
        )

        if video_id in stats_by_id:
            stats_item = stats_by_id[video_id]

            merged = dict(item)

            merged["statistics"] = (
                stats_item.get("statistics", {})
            )

            merged["contentDetails"] = (
                stats_item.get("contentDetails", {})
            )

            enriched_items.append(merged)

        else:
            enriched_items.append(item)

    return {
        "items": enriched_items
    }


# ============================================================
# TRENDING VIDEOS
# ============================================================

@mcp.tool()
def search_trending_videos(
    max_results: int = 50,
    region_code: str = "US",
) -> dict[str, Any]:
    """
    Get currently popular YouTube videos.
    """

    max_results = max(
        1,
        min(int(max_results), 50),
    )

    data = youtube_get(
        "videos",
        {
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": region_code,
            "maxResults": max_results,
        },
    )

    filtered_items = []

    excluded_categories = {
        "25",
    }

    excluded_words = {
        "news",
        "politics",
        "политика",
        "новости",
        "podcast",
        "подкаст",
        "live",
        "стрим",
        "stream",
    }

    for item in data.get("items", []):
        category_id = str(
            item.get("snippet", {})
            .get("categoryId", "")
        )

        title = str(
            item.get("snippet", {})
            .get("title", "")
        ).lower()

        description = str(
            item.get("snippet", {})
            .get("description", "")
        ).lower()

        text = f"{title} {description}"

        if category_id in excluded_categories:
            continue

        if any(
            word in text
            for word in excluded_words
        ):
            continue

        filtered_items.append(item)

    return {
        "items": filtered_items
    }


# ============================================================
# RADAR CONFIG
# ============================================================

LANGUAGE_CONFIG = {
    "ru": [
        "тренды",
        "искусственный интеллект технологии",
        "фильмы истории",
        "образование интересное",
    ],
    "en": [
        "trends",
        "artificial intelligence technology",
        "movies stories",
        "education interesting",
    ],
    "hi": [
        "trending",
        "artificial intelligence technology",
        "movies stories",
        "education",
    ],
    "zh": [
        "热门趋势",
        "人工智能 科技",
        "电影 故事",
        "教育",
    ],
}


RADAR_EXCLUDED_WORDS = {
    "news",
    "politics",
    "политика",
    "новости",
    "podcast",
    "подкаст",
    "live",
    "стрим",
    "stream",
}


RADAR_EXCLUDED_CATEGORY_IDS = {
    "25",
}


# ============================================================
# RADAR
# ============================================================

@mcp.tool()
def search_radar_videos(
    language: str = "ru",
    max_results_per_query: int = 10,
    region_code: str = "US",
) -> list[dict[str, Any]]:
    """
    Broad discovery radar.

    IMPORTANT:
    If YouTube starts returning quota/rate-limit errors,
    stop immediately instead of continuing to spend requests.
    """

    language = (
        str(language).strip().lower()
    )

    queries = LANGUAGE_CONFIG.get(
        language,
        LANGUAGE_CONFIG["ru"],
    )

    max_results_per_query = max(
        1,
        min(int(max_results_per_query), 25),
    )

    all_items: list[dict[str, Any]] = []

    for query in queries:
        try:
            result = search_videos(
                query=query,
                max_results=max_results_per_query,
                region_code=region_code,
                relevance_language=(
                    language
                    if language in {
                        "ru",
                        "en",
                        "hi",
                        "zh",
                    }
                    else None
                ),
            )

        except YouTubeQuotaError:
            logger.warning(
                "RADAR_STOPPED_QUOTA language=%s query=%s",
                language,
                query,
            )
            break

        except Exception as exc:
            logger.warning(
                "RADAR_QUERY_FAILED language=%s query=%s error_type=%s",
                language,
                query,
                type(exc).__name__,
            )
            continue

        for item in result.get("items", []):
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

            text = (
                f"{title} {description}"
            ).lower()

            if (
                category_id
                in RADAR_EXCLUDED_CATEGORY_IDS
            ):
                continue

            if any(
                word in text
                for word in RADAR_EXCLUDED_WORDS
            ):
                continue

            view_count = int(
                statistics.get(
                    "viewCount",
                    0,
                )
                or 0
            )

            like_count = int(
                statistics.get(
                    "likeCount",
                    0,
                )
                or 0
            )

            comment_count = int(
                statistics.get(
                    "commentCount",
                    0,
                )
                or 0
            )

            published_at = snippet.get(
                "publishedAt"
            )

            all_items.append(
                {
                    "video_id": (
                        item.get("id", {})
                        .get("videoId")
                        or item.get("id")
                    ),
                    "title": title,
                    "channel_id": snippet.get(
                        "channelId"
                    ),
                    "channel_title": snippet.get(
                        "channelTitle"
                    ),
                    "published_at": published_at,
                    "description": description,
                    "category_id": category_id,
                    "views": view_count,
                    "likes": like_count,
                    "comments": comment_count,
                    "query": query,
                    "language": language,
                }
            )

    # Remove duplicates
    unique: dict[str, dict[str, Any]] = {}

    for item in all_items:
        video_id = item.get("video_id")

        if video_id:
            unique[str(video_id)] = item

    result_items = list(
        unique.values()
    )

    # Sort primarily by views
    result_items.sort(
        key=lambda x: (
            x.get("views", 0),
            x.get("likes", 0),
            x.get("comments", 0),
        ),
        reverse=True,
    )

    return result_items


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    logger.info(
        "Starting YouTube MCP server on port %s",
        PORT,
    )

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=PORT,
    )
