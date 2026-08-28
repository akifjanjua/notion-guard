# RailCall Contest Entry — Notion Guard

## Title

Notion Guard — Governed Notion Integration

## Repository

https://github.com/akifjanjua/notion-guard (branch `main`, HEAD `28a7e79d3dacbce1d1d3c37bb9bdb6062b596634` at time of writing — check the branch for later commits)

The repository is **public** — README and CI links resolve for anyone.

## Description

Notion Guard is a governance-first RailCall module for small teams running their work through Notion. It provides 10 focused commands against the real Notion REST API (`Notion-Version: 2026-03-11`, the data-source architecture introduced 2025-09-03): search across pages and data sources, inspect a data source's property schema, query/filter/sort a data source's rows, read a page's properties and block content, list workspace users, create a page, update a page's properties or trash status, append content blocks, and create a comment or discussion reply.

The four write commands (`create_page`, `update_page_properties`, `append_blocks`, `create_comment`) cannot run silently. RailCall previews the exact payload, blocks it until a human approves it, executes only the approved action, and records the result in a signed receipt that can be independently verified. The six read commands execute immediately — they cannot alter workspace state, so gating them would only add friction.

Two of the six read commands — `notion.get_data_source_schema` and `notion.list_users` — were chosen specifically for usability rather than coverage: they let a caller confirm real property names, option values, and teammate identities before a write is attempted, so a first write is far more likely to succeed instead of failing on a guessed field name or a raw UUID.

Notion Guard resolves credentials only through RailCall's vault helper, uses certifi-backed verified HTTPS, never invokes curl or another subprocess, actively redacts credentials from errors, and never automatically retries writes with an uncertain outcome. `module.json` declares a `requires` sandbox block (`network: ["api.notion.com"]`, `subprocess: false`, `filesystem_writes: []`) that RailCall Station enforces at handler-load time, not just documents.

I tested it against the real Notion REST API with no mocks or stubs. The public CI workflow (GitHub Actions) tests Python 3.10, 3.12, and 3.13, runs an offline security suite and a model-provider egress contract test, and verifies the final release archive byte-for-byte against the committed Git tree. Latest green run: https://github.com/akifjanjua/notion-guard/actions/runs/33191114813

Marketplace listing: https://railcall.ai/marketplace/muhammad-akif-janjua/notion-guard — `railcall market publish` succeeded and the listing page is live (verified independently: real HTTP 200, correct title, publisher name, and category). Note: as of publishing, `railcall market get`/`market list` (the CLI's install-facing catalog) had not yet indexed the listing — a possible platform indexing lag, not a re-check of our own; the public storefront page itself is confirmed live.

README URL: https://github.com/akifjanjua/notion-guard/blob/main/README.md

Demo video: **[PASTE UNLISTED YOUTUBE URL — record per `VIDEO_SCRIPT.md`, not yet filmed]**

`contest:2026Q3`

## Verification evidence

- **Signature**: signed with the real registered publisher key (fingerprint `e469d55383447fc6b95cbffb786fee7c…`), independently verified both by this repo's own `tools/verify_module_tree.py` (Ed25519, RailCall v2 tree spec) and by RailCall's own CLI (`railcall market module verify`): `✓ signature valid`, `ownership: ✓ signed by your local key`.
- **Release reproducibility**: `tools/build_release.py` + `tools/release_acceptance_test.py` confirm the packaged archive is byte-for-byte identical to the committed Git tree and rebuilds deterministically.
- **Real end-to-end write, not a mock**: executed a real `notion.search` (receipt `cmd/cmd_20260828T165238Z_notion_search_475cc19c_executed_0004.json`, `http_status: 200`, returned the live "Test Tasks" data source) followed by an approved, executed `notion.create_page` against that data source through RailCall Studio's preview → approve → execute airlock (receipt `cmd/cmd_20260828T171009Z_notion_create_page_db9b3fa2_executed_0008.json`, integrity `sha256:6615c2257f7adeb57fb957681145fbb1ceb4d3ab80138d3a3e91a71638726a16f`, signed with key `ecac7bc46608cb35`). The resulting row was confirmed visible live in the Notion workspace.
- **Sandbox enforcement, not just declaration**: Station's own boot log shows the gate actually installed for this module: `network gate armed — allow: ['api.notion.com']`, `subprocess gate CLOSED`, `filesystem-write gate active — allow: (none)`.

## Trust declaration

Notion Guard's signed manifest declares `allowed_destinations` as exactly the Notion API host (`api.notion.com`) and zero LLM/model-provider entries. The module talks only to the Notion REST API and does not send page or database data to a model-provider SDK or RailCall model-completion primitive.
