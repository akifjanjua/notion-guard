# Troubleshooting

**Saved a token in Integrations, but Notion Guard still says "not configured"** — Search Integrations for "notion"; you'll see two cards. The plain `notion` card is Station's own built-in integration, not this module's. Because this module's provider collides with it, RailCall auto-namespaces the real credential slot to `muhammad-akif-janjua-notion-guard::notion` — save `NOTION_API_KEY` on that card instead.

**"Notion credential is not configured"** — Save your integration secret as `NOTION_API_KEY` on the `muhammad-akif-janjua-notion-guard::notion` card in RailCall Studio → Integrations (see above — not the plain `notion` card), then reload Modules.

**A page/database doesn't show up in `notion.search`** — Notion integrations only see content a workspace admin has explicitly shared with them. Open the page or database in Notion, click "..." → "Connections", and add the integration.

**`notion.create_page` or `notion.update_page_properties` fails with a property-name error** — Run `notion.get_data_source_schema` on the target data source first and use the exact property names and option values it returns; Notion property names and select/status values are case-sensitive.

**"the write outcome is unknown"** — The request either timed out, the connection failed, or Notion returned a server error (5xx) after the request was sent. Check the target page/database directly in Notion before retrying; the write may or may not have applied.

**`children_json` or `properties_json` errors about invalid JSON** — These fields must be a JSON-encoded string containing Notion's exact documented shape (e.g. `{"Name":{"title":[{"text":{"content":"..."}}]}}`), not a plain string or a Python dict literal.

**`page_id` vs `data_source_id`** — A database in Notion's current API is a container for one or more data sources; pages are created under a `data_source_id`, not a `database_id`. Use `notion.search` with `object_type: "data_source"` to find the right ID.
