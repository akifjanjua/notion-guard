# Security

## Vault-only credentials

Notion Guard resolves `NOTION_API_KEY` exclusively through RailCall's injected `vault_get("notion")` helper. It does not inspect `credentials.local.json`, other RailCall files, process environment variables, command-line arguments, or command inputs for secrets.

Never publish API keys, approval codes, local receipt archives, `.env` files, or RailCall credential files.

## HTTPS transport

All Notion requests use Python `urllib.request` with certificate and hostname verification enabled through a certifi-backed `SSLContext`. The module does not invoke curl, a shell, or another subprocess and never disables TLS verification.

## Model-provider egress contract

`module.json` declares `"allowed_destinations": []`. The signed declaration means the module permits no LLM/model-provider calls. Notion's REST API is the module's business integration endpoint and is not routed through any model-completion primitive. A dedicated CI test rejects imports, hostnames, or source references associated with supported model providers and rejects any use of `station_llm`.

## Governance

All four writes — `notion.create_page`, `notion.update_page_properties`, `notion.append_blocks`, and `notion.create_comment` — are `write_requires_approval`. RailCall binds approval to the exact previewed payload. Without matching approval, the external write is blocked.

Complex payloads (property values, block arrays, filters, sorts) are passed as JSON-string fields so a write expresses Notion's exact documented shape rather than a lossy intermediate format, and can be inspected in full during approval.

## Retry and unknown-outcome policy

The handler performs one HTTP attempt per command. Mutations are never automatically retried. If a timeout, connection failure, unreadable response, or HTTP 5xx response prevents confirmation of a write, the handler reports that the write outcome is unknown and instructs the user to check Notion before retrying.

## Error handling and redaction

HTTP status is checked on every response; Notion's own error payloads are surfaced with a clear message. The active API key is redacted from any error text before it is raised, so a network error or Notion error response cannot leak the credential.

## Responsible disclosure

Report security issues with a redacted reproduction. Do not include credentials, private page contents, personal email addresses, approval codes, signatures, or full sensitive identifiers.
