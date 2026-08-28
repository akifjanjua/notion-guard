# Notion Guard

[![Notion Guard Tests](https://github.com/akifjanjua/notion-guard/actions/workflows/notion-guard-tests.yml/badge.svg)](https://github.com/akifjanjua/notion-guard/actions/workflows/notion-guard-tests.yml)

Notion Guard is a governance-first RailCall module for small teams running their work through Notion. It provides 10 focused commands for discovery, database schema/query, page and block reads, and approval-controlled writes through the real Notion REST API.

## Commands

Reads: `notion.search`, `notion.get_data_source_schema`, `notion.query_data_source`, `notion.get_page`, `notion.get_page_content`, and `notion.list_users`. By default these execute immediately since they cannot alter workspace state — but a Station-wide policy (`a2d3bf`) can upgrade every command from a module declaring network access to require approval, reads included. If a read shows `blocked_by_policy`, see [Troubleshooting](docs/TROUBLESHOOTING.md).

Writes: `notion.create_page`, `notion.update_page_properties`, `notion.append_blocks`, and `notion.create_comment`. Every write uses `write_requires_approval`, binding human approval to the exact payload with a signed receipt. `notion.update_page_properties` also archives/restores a page via its `in_trash` field — same command, not a separate delete.

`notion.get_data_source_schema` and `notion.list_users` exist for usability: confirm real property names/options before writing, and address teammates by name instead of raw UUIDs. All 10 commands act on one item at a time by design, matching this round's focused command-set scope rather than adding batch variants.

## Egress contract

The signed manifest declares `allowed_destinations: [{"provider":"notion","hosts":["api.notion.com"]}]` — the Notion API host only, zero LLM/model-provider destinations. A `requires` block has Station enforce this at handler-load time, not just document it. See [SECURITY.md](SECURITY.md) for the full posture.

## Install

Pre-publish (current state):

```bash
python -m pip install certifi
git clone https://github.com/akifjanjua/notion-guard.git
```

Copy the cloned folder's contents into `~/.railcall/station/modules/muhammad-akif-janjua-notion-guard/` (the folder name is the module slug). Open RailCall Studio, reload **Modules**, and confirm **Notion Guard v1.0.1**, **signature verified**, **10 commands**.

Post-publish, this will work instead:

```bash
railcall market install muhammad-akif-janjua/notion-guard
```

## Configure credentials

Create an internal integration at `https://www.notion.so/my-integrations`, then share each page/database you want Notion Guard to see: open it, click **···** top right, **Connections**, add the integration.

In Studio → **Integrations**, search "notion" — you'll see two cards. Use `muhammad-akif-janjua-notion-guard::notion` (Station auto-namespaces this module's slot because its declared provider collides with Station's built-in `notion` card), not the plain one. Save the secret as `NOTION_API_KEY`.

## Run a command

Open Studio's **Sends** tab (`#/sends?module=notion`), pick a Notion Guard command, click **Fire**, fill its inputs, then **1. Preview → 2. Approve → 3. Execute**. Reads and writes both produce a signed receipt; writes additionally pause for your approval click before Notion is touched.

## Governed write example

Preview `notion.create_page` with a `data_source_id` (from `notion.search`; confirm field names with `notion.get_data_source_schema` first) and:

```json
{"properties_json": "{\"Name\":{\"title\":[{\"text\":{\"content\":\"Ship the RailCall demo\"}}]},\"Status\":{\"select\":{\"name\":\"In Progress\"}}}"}
```

## Writing less obvious property types

`get_data_source_schema` reports a property's type and, for select/status/multi_select, its option names — but not every type's write shape. Common ones: `people`: `{"people":[{"id":"<id from notion.list_users>"}]}`; `relation`: `{"relation":[{"id":"<related page id>"}]}`; `date`: `{"date":{"start":"2026-01-01","end":null}}`.

## Limitations

The integration token acts with whatever pages/databases a workspace admin has explicitly shared with it — Notion Guard cannot see anything that has not been shared. Search, query, and content results are bounded to remain readable in RailCall receipts. Retrying `create_page`/`append_blocks`/`create_comment` after an unknown-outcome error can duplicate them; concurrent same-property writes race — see [Troubleshooting](docs/TROUBLESHOOTING.md).

`contest:2026Q3`
