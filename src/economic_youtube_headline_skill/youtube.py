import re
from typing import Callable
from urllib.parse import parse_qs, quote_plus, urlparse
from urllib.request import Request, urlopen


_YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_CHANNEL_ID_RE = re.compile(r"^UC[A-Za-z0-9_-]{22}$")
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


def list_upload_video_urls(
    channel_id: str,
    limit_per_channel: int,
    fetch_text: Callable[[str], str | None] = _fetch_text,
) -> list[str]:
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    xml = fetch_text(feed_url)
    if not xml:
        return []

    urls: list[str] = []
    seen: set[str] = set()
    for video_id in _VIDEO_ID_IN_FEED_RE.findall(xml):
        if video_id in seen:
            continue
        seen.add(video_id)
        urls.append(f"https://www.youtube.com/watch?v={video_id}")
        if len(urls) >= limit_per_channel:
            break
    return urls


def collect_video_urls_from_channels(
    channel_tokens: list[str],
    limit_per_channel: int,
    fetch_text: Callable[[str], str | None] = _fetch_text,
) -> tuple[list[str], list[str]]:
    collected: list[str] = []
    warnings: list[str] = []

    for token in channel_tokens:
        channel_id = resolve_channel_id(token, fetch_text=fetch_text)
        if not channel_id:
            warnings.append(f"Failed to resolve channel token: {token}")
            continue
        urls = list_upload_video_urls(channel_id, limit_per_channel, fetch_text=fetch_text)
        if not urls:
            warnings.append(f"No uploaded videos found for channel: {token}")
            continue
        collected.extend(urls)

    deduped = list(dict.fromkeys(collected))
    return deduped, warnings


def fetch_transcript(video_id: str, languages: list[str]) -> str | None:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        segments = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        text = " ".join(seg.get("text", "").strip() for seg in segments if seg.get("text"))
        return text.strip() or None
    except Exception:
        return None
