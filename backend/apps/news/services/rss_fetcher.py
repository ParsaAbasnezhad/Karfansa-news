import calendar
import ipaddress
import logging
import re
import secrets
import socket
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from types import SimpleNamespace
from typing import Protocol, cast
from urllib.parse import urldefrag, urljoin, urlparse

import feedparser
import requests
import urllib3
from django.core.cache import cache, caches
from django.core.cache.backends.locmem import LocMemCache
from django.db import DatabaseError, connection, transaction
from django.utils import timezone
from redis.exceptions import RedisError

from apps.news.models import News, NewsFetchRun, NewsIntake, NewsSource, NewsTopic
from apps.news.services.news_scorer import classify_content_with_reason
from apps.news.services.retention import NEWS_RETENTION_DAYS, retention_cutoff

USER_AGENT = "KarfansaNewsBot/1.0"
REQUEST_TIMEOUT = 15
MAX_RESPONSE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_REDIRECTS = 3
MAX_NETWORK_ATTEMPTS = 3
RETRYABLE_HTTP_STATUSES = {429, 500, 502, 503, 504}
RSS_LOCK_TIMEOUT_SECONDS = 600
RSS_POSTGRES_LOCK_ID = 740216001
logger = logging.getLogger(__name__)


class _CacheLock(Protocol):
    def acquire(self, blocking: bool = True) -> bool: ...

    def release(self) -> None: ...


def _try_postgres_rss_lock() -> bool:
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [RSS_POSTGRES_LOCK_ID])
        return bool(cursor.fetchone()[0])


def _release_postgres_rss_lock() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_unlock(%s)", [RSS_POSTGRES_LOCK_ID])
        if not cursor.fetchone()[0]:
            logger.error("RSS PostgreSQL advisory lock was no longer owned by this connection")


def _acquire_cache_rss_lock(lock_key: str, token: str) -> tuple[bool, _CacheLock | None]:
    lock_factory = getattr(cache, "lock", None)
    if callable(lock_factory):
        lock = cast(
            _CacheLock,
            lock_factory(lock_key, timeout=RSS_LOCK_TIMEOUT_SECONDS, blocking_timeout=0),
        )
        return lock.acquire(blocking=False), lock
    if not isinstance(caches["default"], LocMemCache):
        raise RuntimeError("RSS lock backend must support ownership-aware distributed locks.")
    return cache.add(lock_key, token, timeout=RSS_LOCK_TIMEOUT_SECONDS), None


def _release_cache_rss_lock(
    lock_key: str,
    token: str,
    lock: _CacheLock | None,
) -> None:
    if lock is not None:
        try:
            lock.release()
        except RedisError as exc:
            logger.error(
                "Failed to release Redis RSS lock",
                extra={"error_type": type(exc).__name__},
            )
    elif cache.get(lock_key) == token:
        cache.delete(lock_key)


class _SummaryTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())

    def get_text(self):
        return " ".join(self.parts)


def extract_summary(entry):
    """استخراج خلاصه متنی از فیلدهای مختلف RSS."""
    summary = entry.get("summary", "") or entry.get("description", "")
    if not isinstance(summary, str):
        summary = str(summary)

    parser = _SummaryTextParser()
    parser.feed(summary)
    return parser.get_text()


def extract_tags(entry):
    """Extract RSS category and tag values as text."""
    values = []
    for field in ("tags", "category", "categories"):
        field_values = entry.get(field, [])
        if isinstance(field_values, (str, dict)):
            field_values = [field_values]

        for value in field_values or []:
            if isinstance(value, dict):
                values.extend((value.get("term", ""), value.get("label", "")))
            elif isinstance(value, str):
                values.append(value)

    tags = []
    seen = set()
    for value in values:
        if not isinstance(value, str):
            continue
        normalized = value.strip()
        if normalized and normalized.casefold() not in seen:
            seen.add(normalized.casefold())
            tags.append(normalized)
    return tags


def validate_rss_url(url):
    """بررسی اولیه URL و جلوگیری از دسترسی به آدرس‌های خصوصی."""

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS URLs are allowed.")

    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Invalid RSS URL.")

    try:
        addresses = socket.getaddrinfo(
            parsed.hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise requests.ConnectionError("RSS host could not be resolved.") from exc

    vetted_addresses = []
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])

        if not ip.is_global:
            raise ValueError("Private or non-public IP addresses are not allowed.")
        normalized = str(ip)
        if normalized not in vetted_addresses:
            vetted_addresses.append(normalized)

    if not vetted_addresses:
        raise requests.ConnectionError("RSS host has no usable address.")
    return vetted_addresses[:2]


def _request_pinned_url(url, address):
    """Connect to a vetted address, but verify TLS against the original hostname."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    ascii_hostname = hostname.encode("idna").decode("ascii")
    host_header = f"[{ascii_hostname}]" if ":" in ascii_hostname else ascii_hostname
    if port != (443 if parsed.scheme == "https" else 80):
        host_header = f"{host_header}:{port}"

    pool_options = {"retries": False}
    if parsed.scheme == "https":
        pool_options.update(
            cert_reqs="CERT_REQUIRED",
            assert_hostname=ascii_hostname,
            server_hostname=ascii_hostname,
        )
        pool = urllib3.HTTPSConnectionPool(address, port, **pool_options)
    else:
        pool = urllib3.HTTPConnectionPool(address, port, **pool_options)

    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    try:
        return pool, pool.urlopen(
            "GET",
            path,
            headers={"Host": host_header, "User-Agent": USER_AGENT},
            timeout=urllib3.Timeout(connect=5, read=REQUEST_TIMEOUT),
            preload_content=False,
            redirect=False,
            retries=False,
        )
    except urllib3.exceptions.NewConnectionError as exc:
        pool.close()
        raise requests.ConnectionError("RSS network request failed") from exc
    except urllib3.exceptions.TimeoutError as exc:
        pool.close()
        raise requests.Timeout("RSS request timed out") from exc
    except urllib3.exceptions.SSLError as exc:
        pool.close()
        raise ValueError("RSS TLS verification failed.") from exc
    except urllib3.exceptions.HTTPError as exc:
        pool.close()
        raise requests.ConnectionError("RSS network request failed") from exc


def download_feed(url):
    """دریافت RSS با محدودیت حجم، زمان و تعداد Redirect."""

    current_url = url

    for _ in range(MAX_REDIRECTS + 1):
        addresses = validate_rss_url(current_url)
        last_connection_error = None
        for address in addresses:
            try:
                pool, response = _request_pinned_url(current_url, address)
                break
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_connection_error = exc
        else:
            raise last_connection_error
        try:
            if response.status in {301, 302, 303, 307, 308}:
                location = response.headers.get("Location")
                if not location:
                    raise ValueError("Invalid redirect response.")
                current_url = urljoin(current_url, location)
                continue

            if response.status >= 400:
                raise requests.HTTPError(
                    f"HTTP {response.status}",
                    response=SimpleNamespace(status_code=response.status),
                )
            content = bytearray()
            try:
                for chunk in response.stream(8192):
                    content.extend(chunk)
                    if len(content) > MAX_RESPONSE_SIZE:
                        raise ValueError("RSS response exceeds the size limit.")
            except urllib3.exceptions.TimeoutError as exc:
                raise requests.Timeout("RSS request timed out") from exc
            except urllib3.exceptions.HTTPError as exc:
                raise requests.ConnectionError("RSS network request failed") from exc
            return bytes(content)
        finally:
            response.close()
            pool.close()

    raise ValueError("Too many redirects.")


def download_feed_with_retry(url):
    """Retry transient network and server errors with capped exponential backoff."""
    host = urlparse(url).hostname or "unknown"
    for attempt in range(1, MAX_NETWORK_ATTEMPTS + 1):
        try:
            return download_feed(url)
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status not in RETRYABLE_HTTP_STATUSES or attempt == MAX_NETWORK_ATTEMPTS:
                raise
            error_name = f"HTTP {status}"
        except (requests.Timeout, requests.ConnectionError, socket.gaierror, TimeoutError) as exc:
            if attempt == MAX_NETWORK_ATTEMPTS:
                raise
            error_name = type(exc).__name__

        delay = min(2 ** (attempt - 1), 8)
        logger.warning(
            "Retrying transient RSS request",
            extra={
                "host": host,
                "attempt": attempt,
                "next_attempt_in_seconds": delay,
                "error": error_name,
            },
        )
        time.sleep(delay)

    raise RuntimeError("RSS request retry loop exited unexpectedly")


def _safe_error_message(exc):
    """Build log/admin text without echoing request URLs, query strings, or credentials."""
    if isinstance(exc, requests.HTTPError):
        status = exc.response.status_code if exc.response is not None else "unknown"
        return f"HTTP {status}"
    if isinstance(exc, requests.Timeout):
        return "RSS request timed out"
    if isinstance(exc, requests.RequestException):
        return "RSS network request failed"
    if isinstance(exc, DatabaseError):
        return "Database operation failed"
    if isinstance(exc, ValueError):
        return "Invalid RSS feed or URL"
    return f"{type(exc).__name__} while processing feed"


def _public_image_url(raw, base):
    if not isinstance(raw, str):
        return ""
    absolute = urljoin(base, raw.strip()) if raw.strip() else ""
    parsed = urlparse(absolute)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return absolute[:1000]
    return ""


def extract_image(entry, base_url=""):
    """استخراج تصویر خبر از اطلاعات RSS."""

    base = base_url or entry.get("link") or ""
    candidates = []

    for item in entry.get("media_content", []) or []:
        if isinstance(item, dict):
            candidates.append(item.get("url", ""))

    for item in entry.get("media_thumbnail", []) or []:
        if isinstance(item, dict):
            candidates.append(item.get("url", ""))

    for enclosure in entry.get("enclosures", []) or []:
        if not isinstance(enclosure, dict):
            continue
        if str(enclosure.get("type", "")).startswith("image/"):
            candidates.append(enclosure.get("href", enclosure.get("url", "")))

    for link in entry.get("links", []) or []:
        if isinstance(link, dict) and str(link.get("type", "")).startswith("image/"):
            candidates.append(link.get("href", ""))

    html_chunks = [entry.get("summary") or "", entry.get("description") or ""]
    content = entry.get("content")
    if isinstance(content, list):
        html_chunks.extend(block.get("value") or "" for block in content if isinstance(block, dict))
    elif isinstance(content, str):
        html_chunks.append(content)

    for html in html_chunks:
        if not isinstance(html, str) or "<img" not in html.lower():
            continue
        candidates.extend(re.findall(r"""<img[^>]+src=["']([^"']+)["']""", html, flags=re.I))

    for raw in candidates:
        image = _public_image_url(raw, base)
        if image:
            return image
    return ""


def extract_available_text(entry):
    """متن در دسترس RSS؛ خلاصه یا بدنه، بدون HTML و با سقف طول."""
    summary = extract_summary(entry)
    extra = ""
    content = entry.get("content")
    html = ""
    if isinstance(content, list) and content and isinstance(content[0], dict):
        html = content[0].get("value") or ""
    elif isinstance(content, str):
        html = content
    if html:
        parser = _SummaryTextParser()
        parser.feed(html)
        extra = parser.get_text()
    text = extra if len(extra) > len(summary) else summary
    return text[:4000]


def extract_published_date(entry):
    """تبدیل تاریخ انتشار RSS به datetime آگاه از منطقه زمانی."""

    parsed_date = entry.get("published_parsed") or entry.get("updated_parsed")

    if parsed_date:
        timestamp = calendar.timegm(parsed_date)
        return datetime.fromtimestamp(timestamp, tz=UTC)

    raw_date = entry.get("published") or entry.get("updated")

    if raw_date:
        try:
            result = parsedate_to_datetime(raw_date)

            if result.tzinfo is None:
                result = result.replace(tzinfo=UTC)

            return result
        except (TypeError, ValueError):
            pass

    return None


def _guid(entry):
    raw = entry.get("id") or entry.get("guid") or ""
    if not isinstance(raw, str):
        raw = str(raw)
    return raw.strip()[:1000]


def _entry_link(raw_link, feed_url):
    """Resolve feed-relative links and discard fragments before deduplication."""
    if not isinstance(raw_link, str) or not raw_link.strip():
        return ""
    link = urldefrag(urljoin(feed_url, raw_link.strip())).url
    parsed = urlparse(link)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""
    return link


def _already_reviewed(source, link, guid):
    if News.objects.filter(original_url=link).exists():
        return True
    if NewsIntake.objects.filter(original_url=link).exists():
        return True
    if not guid:
        return False
    if News.objects.filter(source=source, guid=guid).exists():
        return True
    return NewsIntake.objects.filter(source=source, guid=guid).exists()


def _remember_decision(source, link, guid, title, status, score, topic_name, reason):
    NewsIntake.objects.update_or_create(
        original_url=link[:1000],
        defaults={
            "source": source,
            "guid": guid,
            "title": title[:300],
            "status": status,
            "score": score,
            "topic_name": topic_name[:100],
            "decision_reason": reason,
        },
    )


def fetch_source(source):
    """دریافت، فیلتر و ذخیره خبرهای مرتبط یک منبع RSS."""

    source.last_attempt_at = timezone.now()
    source.save(update_fields=["last_attempt_at"])

    content = download_feed_with_retry(source.rss_url)
    parsed_feed = feedparser.parse(content)

    if not parsed_feed.get("version") or (parsed_feed.bozo and not parsed_feed.entries):
        raise ValueError("RSS feed could not be parsed.")

    created_count = 0
    rejected_count = 0
    skipped_count = 0
    error_count = 0
    last_error = ""

    topics = list(NewsTopic.objects.filter(is_active=True))

    for entry_index, entry in enumerate(parsed_feed.entries, start=1):
        try:
            link = _entry_link(entry.get("link", ""), source.rss_url)
            title = entry.get("title", "").strip()
            if not link or not title or len(link) > 1000:
                error_count += 1
                last_error = "RSS item is missing a valid HTTP(S) link or title"
                continue

            guid = _guid(entry)
            if _already_reviewed(source, link, guid):
                skipped_count += 1
                continue

            published_at = extract_published_date(entry)
            if published_at is not None and published_at < retention_cutoff():
                _remember_decision(
                    source,
                    link,
                    guid,
                    title,
                    NewsIntake.Status.REJECTED,
                    0,
                    "",
                    f"خبر قدیمی‌تر از بازهٔ نگهداری {NEWS_RETENTION_DAYS} روزه است.",
                )
                rejected_count += 1
                continue

            summary = extract_available_text(entry)
            tags = extract_tags(entry)
            topic, score, decision_reason = classify_content_with_reason(
                title=title,
                summary=summary,
                topics=topics,
                tags=tags,
            )

            if topic is None:
                _remember_decision(
                    source,
                    link,
                    guid,
                    title,
                    NewsIntake.Status.REJECTED,
                    score,
                    "",
                    decision_reason,
                )
                rejected_count += 1
                continue

            with transaction.atomic():
                _, created = News.objects.get_or_create(
                    original_url=link,
                    defaults={
                        "source": source,
                        "topic": topic,
                        "title": title[:300],
                        "summary": summary,
                        "image_url": extract_image(entry, link),
                        "guid": guid,
                        "published_at": published_at,
                        "score": score,
                        "is_published": True,
                    },
                )
                _remember_decision(
                    source,
                    link,
                    guid,
                    title,
                    NewsIntake.Status.APPROVED,
                    score,
                    topic.name,
                    decision_reason,
                )
            if created:
                created_count += 1
            else:
                skipped_count += 1
        except DatabaseError:
            raise
        except Exception as exc:
            last_error = _safe_error_message(exc)
            logger.error(
                "Failed to process RSS entry",
                extra={
                    "source_id": source.pk,
                    "entry_index": entry_index,
                    "error_type": type(exc).__name__,
                    "error": last_error,
                },
            )
            error_count += 1

    now = timezone.now()
    source.last_fetched_at = now
    source.last_fetch_status = "success" if not error_count else "partial"
    source.last_fetch_error = (
        f"{error_count} item errors; latest: {last_error}" if error_count else ""
    )[:300]
    source.last_fetched_count = len(parsed_feed.entries)
    source.last_accepted_count = created_count
    source.last_rejected_count = rejected_count
    source.last_duplicate_count = skipped_count
    source.last_error_count = error_count
    source.health_status = (
        NewsSource.Health.HEALTHY if not error_count else NewsSource.Health.DEGRADED
    )
    source.save(
        update_fields=[
            "last_fetched_at",
            "last_attempt_at",
            "last_fetch_status",
            "last_fetch_error",
            "last_fetched_count",
            "last_accepted_count",
            "last_rejected_count",
            "last_duplicate_count",
            "last_error_count",
            "health_status",
        ]
    )

    return {
        "fetched": len(parsed_feed.entries),
        "accepted": created_count,
        "created": created_count,
        "saved": created_count,
        "rejected": rejected_count,
        "skipped": skipped_count,
        "duplicates": skipped_count,
        "errors": error_count,
    }


def fetch_all_sources():
    """دریافت خبر از تمام منابع فعال. خطای یک منبع بقیه را متوقف نمی‌کند."""

    run = NewsFetchRun.objects.create()
    lock_key = "news:rss-fetch-lock"
    lock_token = secrets.token_urlsafe(32)
    cache_lock = None
    postgres_lock = connection.vendor == "postgresql"
    try:
        if postgres_lock:
            acquired = _try_postgres_rss_lock()
        else:
            acquired, cache_lock = _acquire_cache_rss_lock(lock_key, lock_token)
    except Exception as exc:
        run.status = NewsFetchRun.Status.FAILED
        run.finished_at = timezone.now()
        run.error_count = 1
        run.error_summary = _safe_error_message(exc)
        run.save(update_fields=["status", "finished_at", "error_count", "error_summary"])
        logger.error(
            "RSS ingestion lock acquisition failed",
            extra={"run_id": run.pk, "error": run.error_summary},
        )
        raise
    if not acquired:
        run.status = NewsFetchRun.Status.SKIPPED
        run.finished_at = timezone.now()
        run.error_summary = "Another RSS run already holds the ingestion lock."
        run.save(update_fields=["status", "finished_at", "error_summary"])
        logger.info(
            "RSS run skipped because another run is active",
            extra={"run_id": run.pk, "status": run.status},
        )
        return [
            {
                "status": "skipped",
                "reason": "RSS fetch is already running",
                "run_id": run.pk,
            }
        ]

    results = []
    try:
        sources = list(NewsSource.objects.filter(is_active=True).order_by("pk"))
        run.sources_checked = len(sources)
        run.save(update_fields=["sources_checked"])

        for source in sources:
            try:
                count = fetch_source(source)
            except DatabaseError:
                logger.error(
                    "Database error interrupted RSS source processing",
                    extra={"run_id": run.pk, "source_id": source.pk},
                )
                raise
            except Exception as exc:
                message = _safe_error_message(exc)
                now = timezone.now()
                source.last_attempt_at = source.last_attempt_at or now
                source.last_fetch_status = "failed"
                source.last_fetch_error = message
                source.last_fetched_count = 0
                source.last_accepted_count = 0
                source.last_rejected_count = 0
                source.last_duplicate_count = 0
                source.last_error_count = 1
                source.health_status = NewsSource.Health.UNHEALTHY
                source.save(
                    update_fields=[
                        "last_attempt_at",
                        "last_fetch_status",
                        "last_fetch_error",
                        "last_fetched_count",
                        "last_accepted_count",
                        "last_rejected_count",
                        "last_duplicate_count",
                        "last_error_count",
                        "health_status",
                    ]
                )
                count = {
                    "fetched": 0,
                    "accepted": 0,
                    "created": 0,
                    "saved": 0,
                    "rejected": 0,
                    "skipped": 0,
                    "duplicates": 0,
                    "errors": 1,
                }
                result = {
                    "source": source.name,
                    "source_id": source.pk,
                    "status": "failed",
                    "error": message,
                }
            else:
                result = {
                    "source": source.name,
                    "source_id": source.pk,
                    "status": source.last_fetch_status,
                }
            result.update(
                {
                    "fetched": count["fetched"],
                    "accepted": count["accepted"],
                    "created": count["created"],
                    "saved": count["saved"],
                    "rejected": count["rejected"],
                    "skipped": count["skipped"],
                    "duplicates": count["duplicates"],
                    "errors": count["errors"],
                }
            )
            results.append(result)
            logger.info(
                "RSS source fetch completed",
                extra={
                    "run_id": run.pk,
                    "source_id": source.pk,
                    "source_name": source.name,
                    "status": result["status"],
                    "fetched": count["fetched"],
                    "accepted": count["accepted"],
                    "rejected": count["rejected"],
                    "duplicates": count["duplicates"],
                    "errors": count["errors"],
                },
            )

        totals = {
            "fetched_count": sum(result.get("fetched", 0) for result in results),
            "new_count": sum(result.get("saved", 0) for result in results),
            "accepted_count": sum(result.get("accepted", 0) for result in results),
            "rejected_count": sum(result.get("rejected", 0) for result in results),
            "duplicate_count": sum(result.get("duplicates", 0) for result in results),
            "error_count": sum(result.get("errors", 0) for result in results),
        }
        failed_sources = sum(result["status"] == "failed" for result in results)
        successful_sources = sum(result["status"] in {"success", "partial"} for result in results)
        run.status = (
            NewsFetchRun.Status.SUCCESS
            if totals["error_count"] == 0
            else NewsFetchRun.Status.PARTIAL
            if successful_sources > 0
            else NewsFetchRun.Status.FAILED
        )
        run.finished_at = timezone.now()
        run.error_summary = (
            f"{failed_sources} source failures; {totals['error_count']} total errors."
            if totals["error_count"]
            else ""
        )
        for field, value in totals.items():
            setattr(run, field, value)
        run.save(
            update_fields=[
                "status",
                "finished_at",
                "error_summary",
                "fetched_count",
                "new_count",
                "accepted_count",
                "rejected_count",
                "duplicate_count",
                "error_count",
            ]
        )
        logger.info(
            "RSS run completed",
            extra={
                "run_id": run.pk,
                "status": run.status,
                "sources_checked": run.sources_checked,
                **totals,
            },
        )
        for result in results:
            result["run_id"] = run.pk
        return results
    except Exception as exc:
        if run.status == NewsFetchRun.Status.RUNNING:
            run.status = NewsFetchRun.Status.FAILED
            run.finished_at = timezone.now()
            run.error_count = max(1, run.error_count)
            run.error_summary = _safe_error_message(exc)
            run.save(update_fields=["status", "finished_at", "error_count", "error_summary"])
        raise
    finally:
        if postgres_lock:
            try:
                _release_postgres_rss_lock()
            except DatabaseError:
                logger.error("Failed to release PostgreSQL RSS advisory lock")
        else:
            _release_cache_rss_lock(lock_key, lock_token, cache_lock)
