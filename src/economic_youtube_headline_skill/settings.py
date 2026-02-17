import os
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path


def _bool_from_env(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _load_dotenv_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            os.environ.setdefault(key, value)


def _load_dotenv() -> None:
    cwd_dotenv = Path(".env")
    repo_dotenv = Path(__file__).resolve().parents[2] / ".env"
    _load_dotenv_file(repo_dotenv)
    if cwd_dotenv.resolve() != repo_dotenv.resolve():
        _load_dotenv_file(cwd_dotenv)


@dataclass(slots=True)
class Settings:
    min_transcript_chars: int = 700
    max_headlines: int = 5
    allow_partial: bool = True
    transcript_languages: str = "ko,en"
    target_channels: str = ""
    channel_video_limit: int = 5
    log_dir: str = "logs"
    result_dir: str = "results"
    mock_transcript_text: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv()
        common_log_dir = os.getenv("EYT_LOG_DIR")
        specific_log_dir = os.getenv("EYT_HEADLINE_LOG_DIR")
        common_result_dir = os.getenv("EYT_RESULT_DIR")
        specific_result_dir = os.getenv("EYT_HEADLINE_RESULT_DIR")
        return cls(
            min_transcript_chars=max(
                100, int(os.getenv("EYT_HEADLINE_MIN_TRANSCRIPT_CHARS", "700"))
            ),
            max_headlines=min(20, max(1, int(os.getenv("EYT_HEADLINE_MAX_HEADLINES", "5")))),
            allow_partial=_bool_from_env(os.getenv("EYT_HEADLINE_ALLOW_PARTIAL"), True),
            transcript_languages=os.getenv("EYT_HEADLINE_TRANSCRIPT_LANGUAGES", "ko,en"),
            target_channels=os.getenv("EYT_HEADLINE_TARGET_CHANNELS", ""),
            channel_video_limit=min(
                50, max(1, int(os.getenv("EYT_HEADLINE_CHANNEL_VIDEO_LIMIT", "5")))
            ),
            log_dir=common_log_dir or specific_log_dir or "logs",
            result_dir=common_result_dir or specific_result_dir or "results",
            mock_transcript_text=os.getenv("EYT_HEADLINE_MOCK_TRANSCRIPT_TEXT") or None,
        )

    def languages(self) -> list[str]:
        return [item.strip() for item in self.transcript_languages.split(",") if item.strip()]

    def channels(self) -> list[str]:
        return [item.strip() for item in self.target_channels.split(",") if item.strip()]

    def date_key(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%d")
