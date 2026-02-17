from datetime import datetime, timezone
import time
from typing import Any, Callable
from uuid import uuid4

from economic_youtube_headline_skill.models import (
    BatchResult,
    HeadlineResult,
    ProcessingStatus,
    VideoDescriptor,
)
from economic_youtube_headline_skill.processor import extract_headlines
from economic_youtube_headline_skill.settings import Settings
from economic_youtube_headline_skill.state_machine import classify_transcript_state
from economic_youtube_headline_skill.youtube import (
    build_proxy_config,
    fetch_transcript,
    infer_was_live,
    parse_video_id,
)


def _build_video(url: str) -> VideoDescriptor:
    video_id = parse_video_id(url)
    return VideoDescriptor(
        video_id=video_id,
        url=url,
        channel_name=f"Unknown Channel ({video_id})",
        title=f"Unknown Title ({video_id})",
        was_live=infer_was_live(url),
    )


def _resolve_transcript(
    video: VideoDescriptor,
    settings: Settings,
    proxy_config: Any | None = None,
) -> tuple[str | None, list[str]]:
    if settings.mock_transcript_text:
        return settings.mock_transcript_text, []
    return fetch_transcript(
        video.video_id,
        settings.languages(),
        allow_insecure_ssl_fallback=settings.insecure_ssl_fallback,
        proxy_config=proxy_config,
    )


def run_pipeline(
    urls: list[str],
    settings: Settings,
    log_event: Callable[[str, dict[str, Any]], None] | None = None,
    run_id: str | None = None,
) -> BatchResult:
    results: list[HeadlineResult] = []
    proxy_config = build_proxy_config(
        proxy_http_url=settings.proxy_http_url,
        proxy_https_url=settings.proxy_https_url,
        webshare_proxy_username=settings.webshare_proxy_username,
        webshare_proxy_password=settings.webshare_proxy_password,
        webshare_proxy_locations=settings.webshare_proxy_locations,
        webshare_retries_when_blocked=settings.webshare_retries_when_blocked,
    )
    for index, url in enumerate(urls):
        if index > 0 and settings.transcript_request_delay_ms > 0:
            time.sleep(settings.transcript_request_delay_ms / 1000)
        if log_event:
            log_event("video_start", {"url": url})
        video = _build_video(url)
        transcript, transcript_warnings = _resolve_transcript(
            video,
            settings,
            proxy_config=proxy_config,
        )

        status, partial, state_warnings = classify_transcript_state(
            was_live=video.was_live,
            transcript_text=transcript,
            min_transcript_chars=settings.min_transcript_chars,
            allow_partial=settings.allow_partial,
        )
        warnings = [*transcript_warnings, *state_warnings]

        headlines: list[str] = []
        error = None

        if transcript and status in {ProcessingStatus.COMPLETE, ProcessingStatus.PARTIAL}:
            headlines = extract_headlines(transcript, settings.max_headlines)

        if status == ProcessingStatus.ERROR:
            error = "processing_error"

        results.append(
            HeadlineResult(
                status=status,
                video=video,
                transcript_chars=len(transcript or ""),
                partial=partial,
                headlines=headlines,
                warnings=warnings,
                error=error,
            )
        )
        if log_event:
            log_event(
                "video_done",
                {
                    "video_id": video.video_id,
                    "status": status.value,
                    "headlines_count": len(headlines),
                    "warnings_count": len(warnings),
                },
            )

    return BatchResult(
        run_id=run_id or uuid4().hex[:10],
        generated_at=datetime.now(timezone.utc).isoformat(),
        results=results,
    )
