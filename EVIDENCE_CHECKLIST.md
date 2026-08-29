# Evidence and Screenshot Checklist

## Strongest evidence set

1. **Real Notion result** — show a harmless approved page update or comment on a test page.
2. **Module loaded** — Studio's Modules tab or boot log showing Notion Guard `v1.0.3`, signature verified, 10 commands, `loaded=1 rejected=0`.
3. **Blocked before approval** — a receipt showing `"result_status": "blocked_by_policy"`, `"execution_class": "blocked"`, and `"external_api_touched": false`.
4. **Approved execution** — a receipt showing `"result_status": "executed"`, `"http_status": 200`, and a non-null `signature.sig`.
5. **Independent receipt verification** — `tools/verify_module_tree.py` and/or `railcall market module verify` reporting `✓ signature valid` for the executed write's receipt.
6. **Safe smoke test** — all six reads and all four write previews pass; no write approved or executed.
7. **Public marketplace listing** — creator, version, 10 commands, governance posture.
8. **Review acknowledgement/approval** — RailCall message or dashboard status.

## Redact

Hide API keys, approval codes, personal email addresses, full UUIDs, raw signatures, unrelated browser notifications, and local credential paths. Keep command names, status labels, HTTP status, page titles used only for the demo, governance result, and verification success visible.

## Video evidence

The video should show: module loaded → schema check → exact payload preview → one human approval → real Notion result → signed receipt verification. Never show the API key or terminal approval code.
