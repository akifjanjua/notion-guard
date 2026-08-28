# Troubleshooting

**Saved a token in Integrations, but Notion Guard still says "not configured"** — Search Integrations for "notion"; you'll see two cards. The plain `notion` card is Station's own built-in integration, not this module's. Because this module's provider collides with it, RailCall auto-namespaces the real credential slot to `muhammad-akif-janjua-notion-guard::notion` — save `NOTION_API_KEY` on that card instead.

**"Notion credential is not configured"** — Save your integration secret as `NOTION_API_KEY` on the `muhammad-akif-janjua-notion-guard::notion` card in RailCall Studio → Integrations (see above — not the plain `notion` card), then reload Modules.

**A page/database doesn't show up in `notion.search`** — Notion integrations only see content a workspace admin has explicitly shared with them. Open the page or database in Notion, click "..." → "Connections", and add the integration.

**`notion.create_page` or `notion.update_page_properties` fails with a property-name error** — Run `notion.get_data_source_schema` on the target data source first and use the exact property names and option values it returns; Notion property names and select/status values are case-sensitive.

**`blocked_by_policy`** — For the four write commands, this is expected: open Studio → Sends, inspect the exact previewed payload, and approve it. For the six read commands, this can *also* happen: Station's `a2d3bf` policy upgrades every command on a network-capable module (like this one) to `write_requires_approval` by default, because a manifest cannot prove a command is really read-only. Until an operator explicitly allowlists a read command's exact id in Settings → Live Execution, reads need the same manual preview → approve → execute as writes.

**Approved action does not execute, or the approval seems to disappear** — Approval is bound to the exact previewed payload's hash. Changing any input — even whitespace — after previewing creates a different payload and needs a new approval. An approval is also single-use: re-running an already-executed approval is refused; preview and approve again.

**"the write outcome is unknown"** — The request either timed out, the connection failed, or Notion returned a server error (5xx) after the request was sent. Check the target page/database directly in Notion before retrying; the write may or may not have applied.

**"Notion API rate limit reached"** — Wait before retrying. Notion Guard never automatically retries a request. Narrow searches/queries and reuse IDs you've already discovered instead of re-querying broadly.

**`children_json` or `properties_json` errors about invalid JSON** — These fields must be a JSON-encoded string containing Notion's exact documented shape (e.g. `{"Name":{"title":[{"text":{"content":"..."}}]}}`), not a plain string or a Python dict literal.

**`page_id` vs `data_source_id`** — A database in Notion's current API is a container for one or more data sources; pages are created under a `data_source_id`, not a `database_id`. Use `notion.search` with `object_type: "data_source"`, or pass a `database_id` directly to `notion.get_data_source_schema` to resolve it.

**`No module named certifi`** — Install certifi with the same Python RailCall uses:

```bash
python -m pip install certifi
python -c "import certifi; print(certifi.where())"
```

**`CERTIFICATE_VERIFY_FAILED`** — Confirm certifi is installed and current, then check the computer's date and time. Notion Guard never disables certificate or hostname verification and never falls back to curl.
