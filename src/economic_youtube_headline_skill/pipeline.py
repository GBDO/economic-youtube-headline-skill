from datetime import datetime, timezone
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
from economic_youtube_headline_skill.youtube import fetch_transcript, infer_was_live, parse_video_id


def _build_video(url: str) -> VideoDescriptor:
    video_id = parse_video_id(url)
    return VideoDescriptor(
        video_id=video_id,
        url=url,
        channel_name=f"Unknown Channel ({video_id})",
        title=f"Unknown Title ({video_id})",
        was_live=infer_was_live(url),
    )


def _resolve_transcript(video: VideoDescriptor, settings: Settings) -> str | None:
    if settings.mock_transcript_text:
        return settings.mock_transcript_text
    return fetch_transcript(video.video_id, settings.languages())


def run_pipeline(urls: list[str], settings: Settings) -> BatchResult:
    results: list[HeadlineResult] = []
    for url in urls:
        video = _build_video(url)
        transcript = _resolve_transcript(video, settings)

        status, partial, warnings = classify_transcript_state(
            was_live=video.was_live,
            transcript_text=transcript,
            min_transcript_chars=settings.min_transcript_chars,
            allow_partial=settings.allow_partial,
        )

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

    return BatchResult(
        run_id=uuid4().hex[:10],
        generated_at=datetime.now(timezone.utc).isoformat(),
        results=results,
    )
