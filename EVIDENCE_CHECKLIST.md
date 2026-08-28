# Evidence and Screenshot Checklist

## Strongest evidence set

1. **Real Notion result** — show a harmless approved page update or comment on a test page.
2. **Module loaded** — Notion Guard `v1.0.0`, signature verified, 10 commands, 0 rejected.
3. **Blocked before approval** — a write preview that is not yet executed.
4. **Approved execution** — executed card showing HTTP 200 and a signature present.
5. **Independent receipt verification** — successful verification for the executed write.
6. **Safe smoke test** — all six reads and all four write previews pass; no write approved or executed.
7. **Public marketplace listing** — creator, version, 10 commands, governance posture.
8. **Review acknowledgement/approval** — RailCall message or dashboard status.

## Redact

Hide API keys, approval codes, personal email addresses, full UUIDs, raw signatures, unrelated browser notifications, and local credential paths. Keep command names, status labels, HTTP status, page titles used only for the demo, governance result, and verification success visible.

## Video evidence

The video should show: module loaded → schema check → exact payload preview → one human approval → real Notion result → signed receipt verification. Never show the API key or terminal approval code.
