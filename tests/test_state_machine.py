import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from economic_youtube_headline_skill.state_machine import classify_transcript_state


class StateMachineTest(unittest.TestCase):
    def test_ended_live_has_precedence_when_no_transcript(self) -> None:
        status, partial, warnings = classify_transcript_state(
            was_live=True,
            transcript_text="",
            min_transcript_chars=700,
            allow_partial=True,
        )
        self.assertEqual(status.value, "ended_live")
        self.assertTrue(partial.is_partial)
        self.assertIn("Ended live video", warnings[0])

    def test_partial_when_transcript_too_short(self) -> None:
        status, partial, warnings = classify_transcript_state(
            was_live=False,
            transcript_text="short transcript",
            min_transcript_chars=700,
            allow_partial=True,
        )
        self.assertEqual(status.value, "partial")
        self.assertIsNotNone(partial.coverage_ratio)
        self.assertTrue(warnings)

    def test_complete_when_transcript_is_long_enough(self) -> None:
        status, partial, warnings = classify_transcript_state(
            was_live=False,
            transcript_text="a" * 900,
            min_transcript_chars=700,
            allow_partial=True,
        )
        self.assertEqual(status.value, "complete")
        self.assertFalse(partial.is_partial)
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
