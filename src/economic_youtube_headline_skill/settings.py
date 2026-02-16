import os
from dataclasses import dataclass


def _bool_from_env(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(slots=True)
class Settings:
    min_transcript_chars: int = 700
    max_headlines: int = 5
    allow_partial: bool = True
    transcript_languages: str = "ko,en"
    mock_transcript_text: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            min_transcript_chars=max(
                100, int(os.getenv("EYT_HEADLINE_MIN_TRANSCRIPT_CHARS", "700"))
            ),
            max_headlines=min(20, max(1, int(os.getenv("EYT_HEADLINE_MAX_HEADLINES", "5")))),
            allow_partial=_bool_from_env(os.getenv("EYT_HEADLINE_ALLOW_PARTIAL"), True),
            transcript_languages=os.getenv("EYT_HEADLINE_TRANSCRIPT_LANGUAGES", "ko,en"),
            mock_transcript_text=os.getenv("EYT_HEADLINE_MOCK_TRANSCRIPT_TEXT") or None,
        )

    def languages(self) -> list[str]:
        return [item.strip() for item in self.transcript_languages.split(",") if item.strip()]
