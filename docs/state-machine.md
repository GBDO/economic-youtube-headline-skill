# State Machine

Terminal status:

- `complete`
- `partial`
- `ended_live`
- `unavailable`
- `error`

Precedence:

1. Transcript empty + `was_live=true` -> `ended_live`
2. Transcript empty + `was_live=false` -> `unavailable`
3. Transcript length `< EYT_HEADLINE_MIN_TRANSCRIPT_CHARS` -> `partial`
4. Otherwise -> `complete`

`error` is reserved for unexpected internal exceptions.
