---
name: economic-youtube-headline-skill
description: Summarize economic YouTube videos (including ended live videos) into per-video headlines. Use when the user wants channel/title/link grouped headline briefs from one or multiple YouTube URLs while keeping configuration in environment variables.
---

# Economic YouTube Headline Skill

## Workflow

1. Collect YouTube video URLs.
2. Build transcript text for each video (or mark unavailable/ended-live).
3. Generate headline bullets.
4. Render output grouped by channel, title, and link.

## Output Contract

- Each video block includes:
  - Channel name
  - Video title
  - Video link
  - Headline bullets
- Ended-live videos without ready transcript are marked as `ended_live`.

## CLI

```bash
eyt-headline generate \
  --video-url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## Environment Variables

- `EYT_HEADLINE_MIN_TRANSCRIPT_CHARS`
- `EYT_HEADLINE_MAX_HEADLINES`
- `EYT_HEADLINE_ALLOW_PARTIAL`
- `EYT_HEADLINE_TRANSCRIPT_LANGUAGES`
- `EYT_HEADLINE_TARGET_CHANNELS`
- `EYT_HEADLINE_CHANNEL_VIDEO_LIMIT`
- `EYT_HEADLINE_LOG_DIR` / `EYT_LOG_DIR`
- `EYT_HEADLINE_SESSION_ID` / `EYT_SESSION_ID`
- `EYT_HEADLINE_MOCK_TRANSCRIPT_TEXT`
