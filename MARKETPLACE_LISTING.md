# Notion Guard

Governed Notion access for small teams: search, inspect database schemas, query and read pages, look up teammates, and make approval-gated writes — every change previewed, approved, and receipted before it touches your workspace.

## What it does

Ten commands against the real Notion REST API. Six reads execute immediately: search across pages and data sources, inspect a data source's property schema, query/filter/sort a database's rows, read a page's properties and content, and list workspace users. Four writes — create a page, update a page's properties or trash status, append content blocks, and create a comment — require a human to approve the exact payload before anything changes in Notion.

## Why the schema and user-lookup reads matter

Guessing a property name or a select option wrong produces a failed or malformed write. `notion.get_data_source_schema` lets a caller check a database's real field names and valid values once, then write correctly the first time. `notion.list_users` lets an assignee be set by name instead of a raw UUID.

## Governance posture

Every write is `write_requires_approval`. RailCall shows the exact payload before anything executes, and a signed, independently verifiable receipt records what happened. The signed manifest declares `allowed_destinations: [{"provider":"notion","hosts":["api.notion.com"]}]` — exactly the Notion API host, zero LLM/model-provider egress. Credentials are vault-only; there is no environment-variable or credential-file fallback.

## Setup

Create an internal integration at `notion.so/my-integrations`, share the pages/databases you want it to see, and save the integration secret as `NOTION_API_KEY` in RailCall Studio → Integrations. Search "notion" — use the `muhammad-akif-janjua-notion-guard::notion` card, not the plain `notion` one (Station auto-namespaces this module's slot because its declared provider collides with Station's built-in Notion integration).

## Pricing

$69, one-time purchase (`license_required: true`). Notion Guard's `module.json` description explicitly lists all 10 commands with a one-line purpose each — a workaround RailCall's own team confirmed for a real, permanent-fix-pending platform gap where paid listings don't render the structured command breakdown (`WHAT IT DOES`/`Provenance: commands`) that free listings get; this doesn't fix that widget, but it does put the same information back in front of a buyer before purchase.

`contest:2026Q3`
