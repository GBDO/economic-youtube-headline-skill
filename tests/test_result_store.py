import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from economic_youtube_headline_skill.result_store import append_daily_result


class ResultStoreTest(unittest.TestCase):
    def test_append_daily_result_uses_single_daily_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            p1 = append_daily_result(
                result_dir=temp_dir,
                date_key="20260217",
                skill_slug="headline",
                payload={"run_id": "run-a"},
            )
            p2 = append_daily_result(
                result_dir=temp_dir,
                date_key="20260217",
                skill_slug="headline",
                payload={"run_id": "run-b"},
            )
            self.assertEqual(p1, p2)
            rows = [json.loads(line) for line in Path(p1).read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["run_id"] for row in rows], ["run-a", "run-b"])


if __name__ == "__main__":
    unittest.main()
