import re
from urllib.parse import parse_qs, urlparse


_YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


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


def fetch_transcript(video_id: str, languages: list[str]) -> str | None:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        segments = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        text = " ".join(seg.get("text", "").strip() for seg in segments if seg.get("text"))
        return text.strip() or None
    except Exception:
        return None
