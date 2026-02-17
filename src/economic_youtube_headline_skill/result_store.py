import json
from pathlib import Path
from typing import Any


def append_daily_result(
    *,
    result_dir: str,
    date_key: str,
    skill_slug: str,
    payload: dict[str, Any],
) -> Path:
    target = Path(result_dir) / f"{skill_slug}-{date_key}.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return target
