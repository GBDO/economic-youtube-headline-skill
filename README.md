# economic-youtube-headline-skill

경제 유튜브 영상을 영상 단위로 요약해서, 각 영상별로 **채널명 / 영상 제목 / 링크 / 헤드라인**을 출력하는 스킬 레포지토리입니다.

## Features

- 종료된 라이브 영상 포함 처리 (`ended_live` 상태)
- 환경변수 기반 설정 (`EYT_HEADLINE_*`)
- Markdown / JSON 출력
- Contract v1 JSON Schema 포함

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

`.env`는 실행 시 자동 로드됩니다(`source .env` 불필요).

로그/결과 파일은 **날짜 기준으로 자동 통합**됩니다.

- 로그: `headline-YYYYMMDD.log`
- 결과: `headline-YYYYMMDD.jsonl`

공통 디렉터리 예시:

```bash
export EYT_LOG_DIR=/tmp/eyt-logs
export EYT_RESULT_DIR=/tmp/eyt-results
```

```bash
eyt-headline generate \
  --video-url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

입력 파일 사용:

```bash
eyt-headline generate --input-file urls.txt
```

채널 환경변수 기반 실행(채널명/채널코드/핸들):

```bash
export EYT_HEADLINE_TARGET_CHANNELS="UC_x5XG1OV2P6uZZ5FSM9Ttw,@mkbhd,한국경제TV"
export EYT_HEADLINE_CHANNEL_VIDEO_LIMIT=3
eyt-headline generate
```

## Environment Variables

| Variable | Default | Description |
|---|---:|---|
| `EYT_HEADLINE_MIN_TRANSCRIPT_CHARS` | `700` | `partial` vs `complete` 기준 문자 수 |
| `EYT_HEADLINE_MAX_HEADLINES` | `5` | 영상당 최대 헤드라인 개수 |
| `EYT_HEADLINE_ALLOW_PARTIAL` | `true` | 부분 자막 결과 허용 여부 |
| `EYT_HEADLINE_TRANSCRIPT_LANGUAGES` | `ko,en` | 자막 조회 언어 우선순위 |
| `EYT_HEADLINE_TARGET_CHANNELS` | _empty_ | 채널 토큰 목록(쉼표 구분, 채널명/채널코드/핸들) |
| `EYT_HEADLINE_CHANNEL_VIDEO_LIMIT` | `5` | 채널별 수집 영상 수 |
| `EYT_HEADLINE_LOG_DIR` | `logs` | 로그 디렉터리 (`EYT_LOG_DIR` 공통 변수도 지원) |
| `EYT_HEADLINE_RESULT_DIR` | `results` | 결과 파일 디렉터리 (`EYT_RESULT_DIR` 공통 변수도 지원) |
| `EYT_HEADLINE_MOCK_TRANSCRIPT_TEXT` | _empty_ | 테스트용 강제 자막 텍스트 |

## Output Status

- `complete`: 자막 충분
- `partial`: 자막 일부
- `ended_live`: 라이브 종료 추정 + 자막 미준비
- `unavailable`: 자막 없음
- `error`: 처리 예외

상세 룰은 `/docs/state-machine.md`를 참고하세요.

## Test

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT
