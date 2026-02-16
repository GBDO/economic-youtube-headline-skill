import argparse
from pathlib import Path

from economic_youtube_headline_skill.pipeline import run_pipeline
from economic_youtube_headline_skill.render import render_json, render_markdown
from economic_youtube_headline_skill.settings import Settings


def _collect_urls(video_urls: list[str], input_file: str | None) -> list[str]:
    collected: list[str] = []
    collected.extend(video_urls)
    if input_file:
        lines = [line.strip() for line in Path(input_file).read_text(encoding="utf-8").splitlines()]
        collected.extend([line for line in lines if line and not line.startswith("#")])
    deduped = list(dict.fromkeys(collected))
    if not deduped:
        raise ValueError("At least one --video-url or --input-file is required.")
    return deduped


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
    urls = _collect_urls(args.video_url, args.input_file)
    batch = run_pipeline(urls, settings)

    rendered = render_markdown(batch) if args.output_format == "markdown" else render_json(batch)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
        print(f"Written: {out}")
        return 0
    print(rendered)
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
