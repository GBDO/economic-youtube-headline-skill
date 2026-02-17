import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class SessionLogger:
    repo: str
    run_id: str
    session_id: str
    log_path: Path

    def _write(self, level: str, event: str, payload: dict[str, Any]) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "repo": self.repo,
            "run_id": self.run_id,
            "session_id": self.session_id,
            "event": event,
            "payload": payload,
        }
        with self.log_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")

    def info(self, event: str, payload: dict[str, Any] | None = None) -> None:
        self._write("INFO", event, payload or {})

    def warn(self, event: str, payload: dict[str, Any] | None = None) -> None:
        self._write("WARN", event, payload or {})

    def error(self, event: str, payload: dict[str, Any] | None = None) -> None:
        self._write("ERROR", event, payload or {})
