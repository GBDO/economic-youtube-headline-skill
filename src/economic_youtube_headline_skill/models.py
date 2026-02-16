from enum import Enum
from dataclasses import asdict, dataclass, field


class ProcessingStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    ENDED_LIVE = "ended_live"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass(slots=True)
class PartialInfo:
    is_partial: bool = False
    coverage_ratio: float | None = None
    reason: str | None = None


@dataclass(slots=True)
class VideoDescriptor:
    video_id: str
    url: str
    channel_name: str = "Unknown Channel"
    title: str = "Unknown Title"
    was_live: bool = False


@dataclass(slots=True)
class HeadlineResult:
    status: ProcessingStatus
    video: VideoDescriptor
    transcript_chars: int = 0
    partial: PartialInfo = field(default_factory=PartialInfo)
    headlines: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass(slots=True)
class BatchResult:
    run_id: str
    generated_at: str
    results: list[HeadlineResult]
    repo: str = "economic-youtube-headline-skill"

    def to_dict(self) -> dict:
        payload = asdict(self)
        for item in payload["results"]:
            item["status"] = item["status"].value
        return payload
