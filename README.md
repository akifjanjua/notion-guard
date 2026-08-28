# Notion Guard

[![Notion Guard Tests](https://github.com/akifjanjua/notion-guard/actions/workflows/notion-guard-tests.yml/badge.svg)](https://github.com/akifjanjua/notion-guard/actions/workflows/notion-guard-tests.yml)

Notion Guard is a governance-first RailCall module for small teams running their work through Notion. It provides 10 focused commands for discovery, database schema/query, page and block reads, and approval-controlled writes through the real Notion REST API.

## Commands

Reads: `notion.search`, `notion.get_data_source_schema`, `notion.query_data_source`, `notion.get_page`, `notion.get_page_content`, and `notion.list_users`. These execute immediately — they cannot alter workspace state, so gating them would only add friction.

Writes: `notion.create_page`, `notion.update_page_properties`, `notion.append_blocks`, and `notion.create_comment`. Every write uses `write_requires_approval`, so RailCall binds human approval to the exact payload and produces a signed receipt.

`notion.get_data_source_schema` and `notion.list_users` exist for usability, not coverage: the schema command lets a caller confirm real property names and select/status option values before writing, instead of guessing whether a field is "Status" or "Task Status"; `list_users` lets people be addressed by name instead of raw UUIDs when setting an assignee.

## Egress contract

The signed manifest declares `"allowed_destinations": []`. Notion Guard permits **zero LLM/model-provider destinations**. It does not call Anthropic, OpenAI, Groq, Gemini, xAI, or Ollama, and does not invoke RailCall's model-completion primitive. Its HTTPS traffic is limited to the declared business integration at `api.notion.com`, using the credential obtained from RailCall Vault. CI fails if model-provider SDKs, provider hosts, or `station_llm` usage are introduced.

## Install

```bash
python -m pip install certifi
railcall market install muhammad-akif-janjua/notion-guard
```

Open RailCall Studio, reload **Modules**, and confirm **Notion Guard v1.0.0**, **signature verified**, and **10 commands**.

The release archive is built from immutable Git `HEAD` bytes, reproduces byte-for-byte across checkouts, includes an external per-file SHA-256 manifest, and must pass independent plus official RailCall signature verification after extraction.

## Configure credentials

Create an internal integration at `https://www.notion.so/my-integrations` and share the pages/databases you want Notion Guard to see with it. In **RailCall Studio → Integrations → Notion**, save the integration secret as `NOTION_API_KEY`. Credentials are resolved only through `vault_get("notion")`.

## Governed write example

Preview `notion.create_page` with a `data_source_id` (found via `notion.search`, confirm field names with `notion.get_data_source_schema` first) and:

```json
{
  "properties_json": "{\"Name\":{\"title\":[{\"text\":{\"content\":\"Ship the RailCall demo\"}}]},\"Status\":{\"select\":{\"name\":\"In Progress\"}}}"
}
```

## Limitations

The integration token acts with whatever pages/databases a workspace admin has explicitly shared with it — Notion Guard cannot see anything that has not been shared. Search, query, and content results are bounded to remain readable in RailCall receipts.

`contest:2026Q3`
