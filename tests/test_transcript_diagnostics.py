import ssl
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from economic_youtube_headline_skill import pipeline, youtube
from economic_youtube_headline_skill.settings import Settings


class TranscriptDiagnosticsTest(unittest.TestCase):
    def test_fetch_transcript_uses_insecure_fallback_for_ssl_error(self) -> None:
        original_default = youtube._fetch_transcript_default
        original_insecure = youtube._fetch_transcript_insecure

        def fail_ssl(_video_id: str, _languages: list[str]) -> str | None:
            raise ssl.SSLError("[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed")

        try:
            youtube._fetch_transcript_default = fail_ssl
            youtube._fetch_transcript_insecure = lambda _video_id, _languages: "fallback transcript"
            transcript, warnings = youtube.fetch_transcript(
                "dQw4w9WgXcQ",
                ["en"],
                allow_insecure_ssl_fallback=True,
            )
        finally:
            youtube._fetch_transcript_default = original_default
            youtube._fetch_transcript_insecure = original_insecure

        self.assertEqual(transcript, "fallback transcript")
        self.assertTrue(any("insecure SSL fallback" in item for item in warnings))

    def test_fetch_transcript_reports_ssl_error_when_fallback_disabled(self) -> None:
        original_default = youtube._fetch_transcript_default

        def fail_ssl(_video_id: str, _languages: list[str]) -> str | None:
            raise ssl.SSLError("[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed")

        try:
            youtube._fetch_transcript_default = fail_ssl
            transcript, warnings = youtube.fetch_transcript(
                "dQw4w9WgXcQ",
                ["en"],
                allow_insecure_ssl_fallback=False,
            )
        finally:
            youtube._fetch_transcript_default = original_default

        self.assertIsNone(transcript)
        self.assertEqual(len(warnings), 1)
        self.assertIn("fallback disabled", warnings[0])
        self.assertIn("SSLError", warnings[0])

    def test_fetch_transcript_reports_non_ssl_exception_with_diagnostic(self) -> None:
        original_default = youtube._fetch_transcript_default

        def fail_runtime(_video_id: str, _languages: list[str]) -> str | None:
            raise RuntimeError("boom happened")

        try:
            youtube._fetch_transcript_default = fail_runtime
            transcript, warnings = youtube.fetch_transcript(
                "dQw4w9WgXcQ",
                ["en"],
                allow_insecure_ssl_fallback=True,
            )
        finally:
            youtube._fetch_transcript_default = original_default

        self.assertIsNone(transcript)
        self.assertEqual(len(warnings), 1)
        self.assertIn("RuntimeError: boom happened", warnings[0])

    def test_pipeline_includes_transcript_fetch_warnings(self) -> None:
        original_fetch = pipeline.fetch_transcript
        try:
            pipeline.fetch_transcript = (
                lambda _video_id, _languages, allow_insecure_ssl_fallback=True: (
                    None,
                    ["Transcript fetch failed: SSLError: certificate verify failed"],
                )
            )
            batch = pipeline.run_pipeline(
                ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
                Settings(),
                run_id="testrun",
            )
        finally:
            pipeline.fetch_transcript = original_fetch

        result = batch.results[0]
        self.assertEqual(result.status.value, "unavailable")
        self.assertTrue(any("Transcript fetch failed" in item for item in result.warnings))
        self.assertTrue(any("Transcript is unavailable." in item for item in result.warnings))


if __name__ == "__main__":
    unittest.main()
