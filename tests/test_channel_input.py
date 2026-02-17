import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from economic_youtube_headline_skill import cli
from economic_youtube_headline_skill.settings import Settings
from economic_youtube_headline_skill.youtube import collect_video_urls_from_channels


class ChannelInputTest(unittest.TestCase):
    def test_collect_video_urls_from_channel_code(self) -> None:
        channel_id = "UC1234567890123456789012"

        def fake_fetch(url: str) -> str | None:
            if "feeds/videos.xml" in url:
                return """
                <feed>
                  <entry><yt:videoId>dQw4w9WgXcQ</yt:videoId></entry>
                  <entry><yt:videoId>aqz-KE-bpKQ</yt:videoId></entry>
                </feed>
                """
            return None

        urls, warnings = collect_video_urls_from_channels(
            [channel_id], limit_per_channel=2, fetch_text=fake_fetch
        )
        self.assertEqual(
            urls,
            [
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "https://www.youtube.com/watch?v=aqz-KE-bpKQ",
            ],
        )
        self.assertEqual(warnings, [])

    def test_cli_uses_target_channels_when_no_direct_urls(self) -> None:
        settings = Settings(target_channels="@sample-channel", channel_video_limit=1)
        original = cli.collect_video_urls_from_channels
        try:
            cli.collect_video_urls_from_channels = (
                lambda channels, limit: (["https://www.youtube.com/watch?v=dQw4w9WgXcQ"], [])
            )
            urls, warnings = cli._collect_urls(settings, video_urls=[], input_file=None)
        finally:
            cli.collect_video_urls_from_channels = original

        self.assertEqual(urls, ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"])
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
