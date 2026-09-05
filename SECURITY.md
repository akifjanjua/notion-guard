# Security

## Vault-only credentials

Notion Guard resolves `NOTION_API_KEY` exclusively through RailCall's injected `vault_get("notion")` helper. It does not inspect `credentials.local.json`, other RailCall files, process environment variables, command-line arguments, or command inputs for secrets.

Because this module's declared provider (`notion`) collides with Station's own built-in Notion integration, RailCall auto-namespaces the actual vault slot to `muhammad-akif-janjua-notion-guard::notion` (a distinct card from the plain `notion` one in Studio's Integrations page). The handler's `vault_get("notion")` call is unaffected — RailCall's per-module vault shim transparently routes it to the namespaced slot — but an operator saving the credential in Studio must use the namespaced card, not the plain `notion` one, or the module will report the credential as not configured. See `README.md` → Configure credentials.

Never publish API keys, approval codes, local receipt archives, `.env` files, or RailCall credential files.

## HTTPS transport

All Notion requests use Python `urllib.request` with certificate and hostname verification enabled through a certifi-backed `SSLContext`. The module does not invoke curl, a shell, or another subprocess and never disables TLS verification.

## Model-provider egress contract

`module.json` declares `"allowed_destinations": [{"provider":"notion","hosts":["api.notion.com"]}]` — exactly the Notion API host and nothing else. The signed declaration means the module permits no LLM/model-provider calls; Notion's REST API is the module's only business integration endpoint and is not routed through any model-completion primitive. A dedicated CI test rejects imports, hostnames, or source references associated with supported model providers and rejects any use of `station_llm`.

## Sandbox posture

`module.json` also declares a `requires` block that RailCall Station enforces at handler-load time: `network: ["api.notion.com"]` (a contextvar-scoped gate — any request to a host outside this allowlist raises `SandboxViolation`), `subprocess: false` (subprocess/`os.system`/`os.exec*` are blocked in the handler's namespace), and `filesystem_writes: []` (no filesystem writes are permitted at all). This matches Notion Guard's actual behavior — one HTTPS host, no subprocess use, no local file writes — as an enforced guarantee rather than only a documented one.

## Governance

All four writes — `notion.create_page`, `notion.update_page_properties`, `notion.append_blocks`, and `notion.create_comment` — are `write_requires_approval`. RailCall binds approval to the exact previewed payload. Without matching approval, the external write is blocked.

**Approval freshness.** RailCall approvals never platform-expire — single-use consumption is the platform's only built-in protection, so a delayed, queued, or retried execution could otherwise act on a human decision made an arbitrary amount of time earlier. All four writes independently check their own approval's age against RailCall's own `pending_approvals.json` record before doing anything else, and refuse to execute one older than 30 minutes. 30 minutes is generous enough that a normal preview → think → approve → execute pace never trips it, even with a short interruption, while still bounding how long a stale decision can act. If that record isn't reachable or readable for any reason, the check does not block — a missing or unreadable piece of platform bookkeeping is not evidence of staleness, and refusing an otherwise-legitimate, freshly-approved write over an internal lookup failure would be a worse failure mode than the gap this closes.

**Trust surface note:** `notion.update_page_properties` is also the module's delete-adjacent command — setting `in_trash: true` archives a page (Notion's trash, restorable via `in_trash: false`), and `in_trash` can be set in the same call as a `properties_json` edit. It carries no separate command name or higher risk tier than an ordinary property edit, so a reviewer scanning command names for "what can remove content" should know this one covers it. Approval preview always shows the exact `in_trash` value being set, so an operator approving a plain-looking property update can see if it also archives the page.

Complex payloads (property values, block arrays, filters, sorts) are passed as JSON-string fields so a write expresses Notion's exact documented shape rather than a lossy intermediate format, and can be inspected in full during approval.

## Retry and unknown-outcome policy

Every write performs exactly one HTTP attempt and is never automatically retried, since a retry could duplicate an unknown-outcome mutation. If a timeout, connection failure, unreadable response, or HTTP 5xx response prevents confirmation of a write, the handler reports that the write outcome is unknown and instructs the user to check Notion before retrying. Reads have no side effect, so a read may automatically retry up to twice on a transient HTTP 429/502/503/504 (honoring Notion's `Retry-After` value when one is supplied) before raising an error.

## Error handling and redaction

HTTP status is checked on every response; Notion's own error payloads are surfaced with a clear message. The active API key is redacted from any error text before it is raised, so a network error or Notion error response cannot leak the credential.

## Responsible disclosure

Report security issues with a redacted reproduction. Do not include credentials, private page contents, personal email addresses, approval codes, signatures, or full sensitive identifiers.
