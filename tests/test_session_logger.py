import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from economic_youtube_headline_skill.session_logger import SessionLogger


class SessionLoggerTest(unittest.TestCase):
    def test_same_session_appends_to_one_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "shared-session.log"
            logger_a = SessionLogger(
                repo="economic-youtube-headline-skill",
                run_id="run-a",
                session_id="shared-session",
                log_path=log_path,
            )
            logger_b = SessionLogger(
                repo="economic-youtube-headline-skill",
                run_id="run-b",
                session_id="shared-session",
                log_path=log_path,
            )

            logger_a.info("run_start", {"value": 1})
            logger_b.info("run_start", {"value": 2})

            lines = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(lines), 2)
            self.assertEqual({row["run_id"] for row in lines}, {"run-a", "run-b"})
            self.assertEqual({row["session_id"] for row in lines}, {"shared-session"})


if __name__ == "__main__":
    unittest.main()
