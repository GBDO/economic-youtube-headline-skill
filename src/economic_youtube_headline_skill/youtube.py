import re
import ssl
from typing import Callable
from urllib.parse import parse_qs, quote_plus, urlparse
from urllib.request import Request, urlopen


_YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_CHANNEL_ID_RE = re.compile(r"^UC[A-Za-z0-9_-]{22}$")
_HANDLE_RE = re.compile(r"^@[A-Za-z0-9._-]{3,30}$")
_CHANNEL_ID_IN_HTML_RE = re.compile(r'"channelId":"(UC[A-Za-z0-9_-]{22})"')
_VIDEO_ID_IN_FEED_RE = re.compile(r"<yt:videoId>([A-Za-z0-9_-]{11})</yt:videoId>")


def parse_video_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname in {"youtu.be"}:
        video_id = parsed.path.lstrip("/")
        if _YOUTUBE_ID_RE.match(video_id):
            return video_id

    query_id = parse_qs(parsed.query).get("v", [None])[0]
    if query_id and _YOUTUBE_ID_RE.match(query_id):
        return query_id

    path_parts = [part for part in parsed.path.split("/") if part]
    for part in path_parts:
        if _YOUTUBE_ID_RE.match(part):
            return part

    raise ValueError(f"Unable to parse YouTube video id from URL: {url}")


def infer_was_live(url: str) -> bool:
    lowered = url.lower()
    return "/live/" in lowered or "live_stream" in lowered


def _fetch_text(url: str, timeout: int = 15) -> str | None:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310
            return response.read().decode("utf-8", errors="ignore")
    except Exception:
        try:
            insecure_context = ssl._create_unverified_context()
            with urlopen(request, timeout=timeout, context=insecure_context) as response:  # noqa: S310
                return response.read().decode("utf-8", errors="ignore")
        except Exception:
            return None


def _extract_channel_id_from_html(html: str | None) -> str | None:
    if not html:
        return None
    match = _CHANNEL_ID_IN_HTML_RE.search(html)
    return match.group(1) if match else None


def resolve_channel_id(
    channel_token: str,
    fetch_text: Callable[[str], str | None] = _fetch_text,
) -> str | None:
    token = channel_token.strip()
    if not token:
        return None
    if _CHANNEL_ID_RE.match(token):
        return token

    if token.startswith("@"):
        html = fetch_text(f"https://www.youtube.com/{token}")
        return _extract_channel_id_from_html(html)

    if token.startswith("http://") or token.startswith("https://"):
        parsed = urlparse(token)
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2 and parts[0] == "channel" and _CHANNEL_ID_RE.match(parts[1]):
            return parts[1]
        html = fetch_text(token)
        return _extract_channel_id_from_html(html)

    # Best effort for channel name or short code:
    candidate_handle = token.replace(" ", "")
    html = fetch_text(f"https://www.youtube.com/@{candidate_handle}")
    channel_id = _extract_channel_id_from_html(html)
    if channel_id:
        return channel_id

    search_html = fetch_text(f"https://www.youtube.com/results?search_query={quote_plus(token)}")
    return _extract_channel_id_from_html(search_html)


def _resolve_channel_id_with_reason(
    channel_token: str,
    fetch_text: Callable[[str], str | None] = _fetch_text,
) -> tuple[str | None, str | None]:
    token = channel_token.strip()
    if not token:
        return None, "empty channel token"
    if token.startswith("@") and not _HANDLE_RE.match(token):
        return None, "invalid handle format"

    channel_id = resolve_channel_id(token, fetch_text=fetch_text)
    if channel_id:
        return channel_id, None
    return None, "could not resolve channel id"


def _list_upload_video_urls_with_reason(
    channel_id: str,
    limit_per_channel: int,
    fetch_text: Callable[[str], str | None] = _fetch_text,
) -> tuple[list[str], str | None]:
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    xml = fetch_text(feed_url)
    if not xml:
        return [], "no uploads feed"

    urls: list[str] = []
    seen: set[str] = set()
    for video_id in _VIDEO_ID_IN_FEED_RE.findall(xml):
        if video_id in seen:
            continue
        seen.add(video_id)
        urls.append(f"https://www.youtube.com/watch?v={video_id}")
        if len(urls) >= limit_per_channel:
            break
    if not urls:
        return [], "no videos in uploads feed"
    return urls, None


def list_upload_video_urls(
    channel_id: str,
    limit_per_channel: int,
    fetch_text: Callable[[str], str | None] = _fetch_text,
) -> list[str]:
    urls, _ = _list_upload_video_urls_with_reason(channel_id, limit_per_channel, fetch_text=fetch_text)
    return urls


def collect_video_urls_from_channels(
    channel_tokens: list[str],
    limit_per_channel: int,
    fetch_text: Callable[[str], str | None] = _fetch_text,
) -> tuple[list[str], list[str]]:
    collected: list[str] = []
    warnings: list[str] = []

    for token in channel_tokens:
        channel_id, resolve_reason = _resolve_channel_id_with_reason(token, fetch_text=fetch_text)
        if not channel_id:
            warnings.append(f"Channel token '{token}': {resolve_reason or 'could not resolve channel id'}.")
            continue
        urls, uploads_reason = _list_upload_video_urls_with_reason(
            channel_id,
            limit_per_channel,
            fetch_text=fetch_text,
        )
        if not urls:
            warnings.append(
                f"Channel token '{token}' (channel_id={channel_id}): {uploads_reason or 'no uploads feed'}."
            )
            continue
        collected.extend(urls)

    deduped = list(dict.fromkeys(collected))
    return deduped, warnings


def _short_exception_message(exc: Exception, max_len: int = 200) -> str:
    message = " ".join(str(exc).strip().split())
    if not message:
        return ""
    if len(message) <= max_len:
        return message
    return f"{message[: max_len - 3]}..."


def _format_exception(exc: Exception) -> str:
    message = _short_exception_message(exc)
    return f"{exc.__class__.__name__}: {message}" if message else exc.__class__.__name__


def _is_ssl_verification_error(exc: Exception) -> bool:
    current: Exception | None = exc
    seen: set[int] = set()
    while current and id(current) not in seen:
        seen.add(id(current))
        text = f"{current.__class__.__name__} {current}".lower()
        if "certificate verify failed" in text or "cert_verify_failed" in text:
            return True
        if "ssl" in current.__class__.__name__.lower() and "cert" in text:
            return True
        next_exc = current.__cause__ or current.__context__
        current = next_exc if isinstance(next_exc, Exception) else None
    return False


def _transcript_segments_to_text(segments: list[dict]) -> str | None:
    text = " ".join(seg.get("text", "").strip() for seg in segments if seg.get("text"))
    return text.strip() or None


def _fetch_transcript_default(video_id: str, languages: list[str]) -> str | None:
    from youtube_transcript_api import YouTubeTranscriptApi

    segments = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
    return _transcript_segments_to_text(segments)


def _fetch_transcript_insecure(video_id: str, languages: list[str]) -> str | None:
    import requests
    from youtube_transcript_api._transcripts import TranscriptListFetcher

    with requests.Session() as http_client:
        http_client.verify = False
        transcript_list = TranscriptListFetcher(http_client).fetch(video_id)
        segments = transcript_list.find_transcript(languages).fetch()
    return _transcript_segments_to_text(segments)


def fetch_transcript(
    video_id: str,
    languages: list[str],
    allow_insecure_ssl_fallback: bool = True,
) -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    try:
        return _fetch_transcript_default(video_id, languages), warnings
    except Exception as exc:
        if _is_ssl_verification_error(exc):
            diagnostic = _format_exception(exc)
            if not allow_insecure_ssl_fallback:
                warnings.append(
                    f"Transcript fetch failed due to SSL verification error (fallback disabled): {diagnostic}"
                )
                return None, warnings

            warnings.append(
                "Transcript fetch SSL verification failed; retrying with insecure SSL fallback (verify=False)."
            )
            try:
                return _fetch_transcript_insecure(video_id, languages), warnings
            except Exception as fallback_exc:
                warnings.append(
                    f"Transcript fetch failed after insecure SSL fallback: {_format_exception(fallback_exc)}"
                )
                return None, warnings

        warnings.append(f"Transcript fetch failed: {_format_exception(exc)}")
        return None, warnings
