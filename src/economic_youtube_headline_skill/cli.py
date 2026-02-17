import argparse
import sys
from pathlib import Path
from uuid import uuid4

from economic_youtube_headline_skill.pipeline import run_pipeline
from economic_youtube_headline_skill.render import render_json, render_markdown
from economic_youtube_headline_skill.result_store import append_daily_result
from economic_youtube_headline_skill.session_logger import SessionLogger
from economic_youtube_headline_skill.settings import Settings
from economic_youtube_headline_skill.youtube import collect_video_urls_from_channels


def _collect_urls(settings: Settings, video_urls: list[str], input_file: str | None) -> tuple[list[str], list[str]]:
    collected: list[str] = []
    collected.extend(video_urls)
    if input_file:
        lines = [line.strip() for line in Path(input_file).read_text(encoding="utf-8").splitlines()]
        collected.extend([line for line in lines if line and not line.startswith("#")])

    if not collected and settings.channels():
        channel_urls, warnings = collect_video_urls_from_channels(
            settings.channels(),
            settings.channel_video_limit,
        )
        collected.extend(channel_urls)
    else:
        warnings = []

    deduped = list(dict.fromkeys(collected))
    if not deduped:
        raise ValueError(
            "No input videos found. Provide --video-url/--input-file or set EYT_HEADLINE_TARGET_CHANNELS."
        )
    return deduped, warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="eyt-headline", description="Economic YouTube headline CLI")
    sub = parser.add_subparsers(dest="command")

    generate = sub.add_parser("generate", help="Generate per-video headlines")
    generate.add_argument("--video-url", action="append", default=[], help="Repeatable YouTube URL")
    generate.add_argument("--input-file", type=str, default=None, help="File with one URL per line")
    generate.add_argument("--output-format", choices=["markdown", "json"], default="markdown")
    generate.add_argument("--out", type=str, default=None, help="Output file path")
    return parser


def run_generate(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    run_id = uuid4().hex[:10]
    date_key = settings.date_key()
    log_path = Path(settings.log_dir) / f"headline-{date_key}.log"
    logger = SessionLogger(
        repo="economic-youtube-headline-skill",
        run_id=run_id,
        session_id=date_key,
        log_path=log_path,
    )

    logger.info(
        "run_start",
        {
            "input_video_urls": len(args.video_url),
            "used_input_file": bool(args.input_file),
            "configured_channels": settings.channels(),
        },
    )

    urls, warnings = _collect_urls(settings, args.video_url, args.input_file)
    logger.info("videos_collected", {"count": len(urls)})

    batch = run_pipeline(
        urls,
        settings,
        log_event=logger.info,
        run_id=run_id,
    )
    result_path = append_daily_result(
        result_dir=settings.result_dir,
        date_key=date_key,
        skill_slug="headline",
        payload=batch.to_dict(),
    )
    for warning in warnings:
        print(f"[warn] {warning}", file=sys.stderr)
        logger.warn("channel_warning", {"message": warning})

    rendered = render_markdown(batch) if args.output_format == "markdown" else render_json(batch)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
        print(f"Written: {out}")
        logger.info("run_complete", {"output_format": args.output_format, "output_file": str(out)})
        print(f"[log] {log_path}", file=sys.stderr)
        print(f"[result] {result_path}", file=sys.stderr)
        return 0
    print(rendered)
    logger.info("run_complete", {"output_format": args.output_format, "output_file": None})
    print(f"[log] {log_path}", file=sys.stderr)
    print(f"[result] {result_path}", file=sys.stderr)
    return 0


def app() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "generate":
        raise SystemExit(run_generate(args))
    parser.print_help()
    raise SystemExit(0)


if __name__ == "__main__":
    app()
