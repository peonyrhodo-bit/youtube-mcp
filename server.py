import os
import logging
import json
import sqlite3
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse


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


class YouTubeQuotaGuard:
    """Fail-closed preflight at the only HTTP gateway to YouTube Data API."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.search_limit = max(0, int(os.getenv("YOUTUBE_SEARCH_DAILY_LIMIT", "100")))
        self.other_limit = max(0, int(os.getenv("YOUTUBE_OTHER_DAILY_QUOTA_UNITS", "10000")))
        self.timezone = ZoneInfo("America/Los_Angeles")
        self._ensure_schema()

    def _connect(self):
        if self.db_path != ":memory:":
            Path(self.db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 30000")
        return conn

    def _ensure_schema(self):
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS youtube_quota_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    search_calls INTEGER NOT NULL DEFAULT 0,
                    other_units INTEGER NOT NULL DEFAULT 0,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS youtube_quota_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    method TEXT NOT NULL,
                    bucket TEXT NOT NULL,
                    units INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT,
                    remaining_json TEXT NOT NULL DEFAULT '{}',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    finished_at TEXT
                )
            """)
        finally:
            conn.close()

    def _period_start(self, now: datetime | None = None) -> datetime:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        local = current.astimezone(self.timezone)
        midnight = datetime.combine(local.date(), time.min, tzinfo=self.timezone)
        return midnight.astimezone(timezone.utc)

    def authorize(self, endpoint: str, params: dict[str, Any] | None = None) -> int:
        bucket = "search" if endpoint == "search" else "other"
        units = 1
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            start = self._period_start().isoformat()
            row = conn.execute("""
                SELECT COALESCE(SUM(search_calls), 0) AS search_calls,
                       COALESCE(SUM(other_units), 0) AS other_units
                FROM youtube_quota_usage WHERE created_at >= ?
            """, (start,)).fetchone()
            used_search = int(row["search_calls"] or 0)
            used_other = int(row["other_units"] or 0)
            search_remaining = max(self.search_limit - used_search, 0)
            other_remaining = max(self.other_limit - used_other, 0)
            remaining = {
                "search_remaining": search_remaining,
                "other_remaining": other_remaining,
                "search_limit": self.search_limit,
                "other_limit": self.other_limit,
            }
            available = search_remaining if bucket == "search" else other_remaining
            method = "search.list" if bucket == "search" else f"{endpoint}.list"
            conn.execute("""
                INSERT INTO youtube_quota_events
                (created_at, operation, method, bucket, units, status, remaining_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, 'planned', ?, ?)
            """, (
                datetime.now(timezone.utc).isoformat(), "youtube_get", method, bucket, units,
                json.dumps(remaining),
                json.dumps({"endpoint": endpoint, "params": params or {}}, default=str),
            ))
            if available < units:
                conn.execute("""
                    INSERT INTO youtube_quota_events
                    (created_at, operation, method, bucket, units, status, reason, remaining_json, metadata_json)
                    VALUES (?, ?, ?, ?, ?, 'blocked', 'budget_exhausted', ?, ?)
                """, (
                    datetime.now(timezone.utc).isoformat(), "youtube_get", method, bucket, units,
                    json.dumps(remaining), json.dumps({"endpoint": endpoint, "params": params or {}}, default=str),
                ))
                conn.commit()
                raise YouTubeQuotaError(
                    f"YouTube {bucket} budget exhausted before {method}; remaining={available}"
                )
            now = datetime.now(timezone.utc).isoformat()
            conn.execute("""
                INSERT INTO youtube_quota_usage
                (created_at, operation, search_calls, other_units, metadata_json)
                VALUES (?, ?, ?, ?, ?)
            """, (
                now, "youtube_get", units if bucket == "search" else 0,
                units if bucket == "other" else 0,
                json.dumps({"method": method, "endpoint": endpoint}, default=str),
            ))
            remaining["search_remaining"] = max(search_remaining - (units if bucket == "search" else 0), 0)
            remaining["other_remaining"] = max(other_remaining - (units if bucket == "other" else 0), 0)
            event_id = conn.execute("""
                INSERT INTO youtube_quota_events
                (created_at, operation, method, bucket, units, status, remaining_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, 'attempted', ?, ?)
            """, (
                now, "youtube_get", method, bucket, units, json.dumps(remaining),
                json.dumps({"endpoint": endpoint}, default=str),
            )).lastrowid
            conn.commit()
            return int(event_id)
        except YouTubeQuotaError:
            raise
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def finish(self, event_id: int, status: str, reason: str | None = None):
        conn = self._connect()
        try:
            conn.execute("""
                UPDATE youtube_quota_events SET status=?, reason=?, finished_at=?
                WHERE id=?
            """, (status, reason, datetime.now(timezone.utc).isoformat(), event_id))
            conn.commit()
        finally:
            conn.close()


QUOTA_DB_PATH = os.getenv("YOUTUBE_QUOTA_DB_PATH", "/tmp/youtube_quota.sqlite3")
quota_guard = YouTubeQuotaGuard(QUOTA_DB_PATH)


# ---------------------------------------------------------
# MCP
# ---------------------------------------------------------

mcp = FastMCP(
    "YouTube Statistics",
    host="0.0.0.0",
    port=PORT,
)


# ---------------------------------------------------------
# Simple HTTP endpoint for uptime checks
# ---------------------------------------------------------

@mcp.custom_route("/", methods=["GET"])
async def root_health_check(request):
    return JSONResponse({"status": "ok"})



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

    # This is the central enforcement point: every outbound YouTube HTTP request
    # must obtain a quota authorization before the network is touched.
    event_id = quota_guard.authorize(endpoint, params)
    try:
        response = requests.get(url, params=safe_params, timeout=30)
    except requests.RequestException as exc:
        quota_guard.finish(event_id, "error", type(exc).__name__)
        logger.error("YouTube request failed: %s", type(exc).__name__)
        raise RuntimeError("YouTube API request failed") from exc

    if response.status_code in (403, 429):
        try:
            data = response.json()
        except Exception:
            data = {}
        reasons = [
            item.get("reason")
            for item in data.get("error", {}).get("errors", [])
            if item.get("reason")
        ]
        quota_reasons = {
            "quotaExceeded", "dailyLimitExceeded", "rateLimitExceeded",
            "userRateLimitExceeded",
        }
        if response.status_code == 429 or any(reason in quota_reasons for reason in reasons):
            quota_guard.finish(event_id, "error", "youtube_quota_or_rate_limit")
            logger.warning("YouTube quota/rate limit reached for endpoint=%s", endpoint)
            raise YouTubeQuotaError("YouTube API quota or rate limit reached")
        quota_guard.finish(event_id, "error", f"http_{response.status_code}")
        logger.error("YouTube API returned HTTP %s for endpoint=%s", response.status_code, endpoint)
        raise RuntimeError("YouTube API authorization/request error")

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        quota_guard.finish(event_id, "error", f"http_{response.status_code}")
        logger.error("YouTube API returned HTTP %s for endpoint=%s", response.status_code, endpoint)
        raise RuntimeError("YouTube API request failed") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        quota_guard.finish(event_id, "error", "invalid_json")
        raise RuntimeError("YouTube API returned invalid JSON") from exc

    quota_guard.finish(event_id, "succeeded")
    return payload


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

    return youtube_get(
        "videos",
        {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(video_ids),
        },
    )


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

    return youtube_get(
        "channels",
        {
            "part": "snippet,statistics,contentDetails",
            "id": channel_id,
        },
    )


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

    return youtube_get(
        "search",
        {
            "part": "snippet",
            "q": query,
            "type": "channel",
            "maxResults": max_results,
        },
    )


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

    _quota reports observed API method calls, not estimated quota units.
    search.list and videos.list are separate quota buckets in the Director.
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

    # Count attempts before making the request: failed/invalid requests can
    # still consume quota. The response can only report calls made in this
    # invocation; durable daily totals are aggregated by the Director.
    search_list_calls = 1
    videos_list_calls = 0
    try:
        search_result = youtube_get("search", params)
    except Exception as exc:
        logger.warning("YouTube API call accounting: endpoint=search.list attempted=1 succeeded=0 error=%s", type(exc).__name__)
        return {
            "items": [],
            "error": "search.list request failed",
            "_quota": {
                "search_calls": search_list_calls,
                "search_list_calls": search_list_calls,
                "videos_list_calls": videos_list_calls,
                "other_units": 0,
                "accounting": "observed_method_calls",
            },
        }
    items = search_result.get("items", [])

    video_ids = list(dict.fromkeys(
        item.get("id", {}).get("videoId")
        for item in items
        if item.get("id", {}).get("videoId")
    ))

    if not video_ids:
        return {
            "items": items,
            "_quota": {
                "search_calls": search_list_calls,
                "search_list_calls": search_list_calls,
                "videos_list_calls": videos_list_calls,
                "other_units": 0,
                "accounting": "observed_method_calls",
            },
        }

    videos_list_calls += 1
    try:
        stats_result = get_video_stats(video_ids)
    except Exception as exc:
        # Search results are still useful if enrichment fails. Report the
        # attempted videos.list call so the caller can account for it.
        logger.warning("YouTube API call accounting: endpoint=videos.list attempted=1 succeeded=0 error=%s", type(exc).__name__)
        return {
            "items": items,
            "_quota": {
                "search_calls": search_list_calls,
                "search_list_calls": search_list_calls,
                "videos_list_calls": videos_list_calls,
                "other_units": videos_list_calls,
                "accounting": "observed_method_calls",
                "videos_list_error": type(exc).__name__,
            },
        }
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
            "search_calls": search_list_calls,
            "search_list_calls": search_list_calls,
            "videos_list_calls": videos_list_calls,
            "other_units": videos_list_calls,
            "accounting": "observed_method_calls",
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
