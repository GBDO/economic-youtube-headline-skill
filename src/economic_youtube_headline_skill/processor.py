import re


def _normalize(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip(" -•\t\r\n")


def extract_headlines(transcript_text: str, max_headlines: int) -> list[str]:
    fragments = re.split(r"[.!?\n]+", transcript_text)
    normalized: list[str] = []
    seen: set[str] = set()

    for fragment in fragments:
        candidate = _normalize(fragment)
        if len(candidate) < 12:
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)
        if len(normalized) >= max_headlines:
            break

    if normalized:
        return normalized

    fallback = _normalize(transcript_text[:160])
    return [fallback] if fallback else []
