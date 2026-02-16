import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from economic_youtube_headline_skill.models import (
    BatchResult,
    HeadlineResult,
    PartialInfo,
    ProcessingStatus,
    VideoDescriptor,
)
from economic_youtube_headline_skill.render import render_markdown


class RenderTest(unittest.TestCase):
    def test_render_markdown_groups_by_channel_title_link(self) -> None:
        batch = BatchResult(
            run_id="abc",
            generated_at="2026-02-16T00:00:00+00:00",
            results=[
                HeadlineResult(
                    status=ProcessingStatus.COMPLETE,
                    video=VideoDescriptor(
                        video_id="dQw4w9WgXcQ",
                        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                        channel_name="Sample Channel",
                        title="Sample Title",
                        was_live=False,
                    ),
                    transcript_chars=1200,
                    partial=PartialInfo(is_partial=False),
                    headlines=["헤드라인 A", "헤드라인 B"],
                    warnings=[],
                    error=None,
                )
            ],
        )

        markdown = render_markdown(batch)
        self.assertIn("Sample Channel", markdown)
        self.assertIn("Sample Title", markdown)
        self.assertIn("https://www.youtube.com/watch?v=dQw4w9WgXcQ", markdown)
        self.assertIn("- 헤드라인 A", markdown)


if __name__ == "__main__":
    unittest.main()
