import json

from economic_youtube_headline_skill.models import BatchResult


def render_markdown(batch: BatchResult) -> str:
    chunks: list[str] = [f"# Economic YouTube Headline Brief ({batch.run_id})"]
    for idx, item in enumerate(batch.results, start=1):
        chunks.extend(
            [
                "",
                f"## {idx}. {item.video.channel_name}",
                f"### {item.video.title}",
                f"- 링크: {item.video.url}",
                f"- 상태: {item.status.value}",
            ]
        )
        if item.partial.is_partial and item.partial.reason:
            chunks.append(f"- 부분처리 사유: {item.partial.reason}")
        if item.error:
            chunks.append(f"- 오류: {item.error}")

        chunks.append("#### 헤드라인")
        if item.headlines:
            chunks.extend([f"- {line}" for line in item.headlines])
        else:
            chunks.append("- (추출된 헤드라인 없음)")

    return "\n".join(chunks).strip() + "\n"


def render_json(batch: BatchResult) -> str:
    return json.dumps(batch.to_dict(), ensure_ascii=False, indent=2)
