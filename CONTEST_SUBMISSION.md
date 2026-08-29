# RailCall Contest Entry — Notion Guard

## Title

Notion Guard — Governed Notion Integration

## Repository

https://github.com/akifjanjua/notion-guard (branch `main`, HEAD `ad930177bce22450d4031e1a4edd21f0f67ccac0` at time of writing — check the branch for later commits)

The repository is **public** — README and CI links resolve for anyone.

## Description

Notion Guard is a governance-first RailCall module for small teams running their work through Notion. It provides 10 focused commands against the real Notion REST API (`Notion-Version: 2026-03-11`, the data-source architecture introduced 2025-09-03): search across pages and data sources, inspect a data source's property schema, query/filter/sort a data source's rows, read a page's properties and block content, list workspace users, create a page, update a page's properties or trash status, append content blocks, and create a comment or discussion reply.

The four write commands (`create_page`, `update_page_properties`, `append_blocks`, `create_comment`) cannot run silently. RailCall previews the exact payload, blocks it until a human approves it, executes only the approved action, and records the result in a signed receipt that can be independently verified. The six read commands execute immediately — they cannot alter workspace state, so gating them would only add friction.

Two of the six read commands — `notion.get_data_source_schema` and `notion.list_users` — were chosen specifically for usability rather than coverage: they let a caller confirm real property names, option values, and teammate identities before a write is attempted, so a first write is far more likely to succeed instead of failing on a guessed field name or a raw UUID.

Notion Guard resolves credentials only through RailCall's vault helper, uses certifi-backed verified HTTPS, never invokes curl or another subprocess, actively redacts credentials from errors, and never automatically retries writes with an uncertain outcome. `module.json` declares a `requires` sandbox block (`network: ["api.notion.com"]`, `subprocess: false`, `filesystem_writes: []`) that RailCall Station enforces at handler-load time, not just documents.

I tested it against the real Notion REST API with no mocks or stubs. The public CI workflow (GitHub Actions) tests Python 3.10, 3.12, and 3.13, runs an offline security suite and a model-provider egress contract test, and verifies the final release archive byte-for-byte against the committed Git tree. Latest green run: https://github.com/akifjanjua/notion-guard/actions/runs/33225704673

Marketplace listing: https://railcall.ai/marketplace/muhammad-akif-janjua/notion-guard — free, matching Linear Guard. Verified independently by loading the live page: `V1.0.3`, `PRICE: Free`, `Provenance: commands 10`, and a full "10 AIRLOCK COMMANDS" breakdown (each command's id, risk, and mode individually listed) — the same layout Linear Guard's listing uses. Notion Guard briefly carried a $69 one-time price with `license_required: true`; while priced, the listing correctly showed `commands —` and a "metadata-only" notice instead of the itemized breakdown, confirmed as universal platform behavior for every paid listing checked (Zernio $160/mo, Salesforce CRM $199/mo) and absent from every free listing checked (Linear Guard, HubSpot CRM) — not a bug, and not something specific to this module.

README URL: https://github.com/akifjanjua/notion-guard/blob/main/README.md

Demo video: **[PASTE UNLISTED YOUTUBE URL — record per `VIDEO_SCRIPT.md`, not yet filmed]**

`contest:2026Q3`

## Verification evidence

- **Signature**: signed with the real registered publisher key (fingerprint `e469d55383447fc6b95cbffb786fee7c…`), independently verified both by this repo's own `tools/verify_module_tree.py` (Ed25519, RailCall v2 tree spec) and by RailCall's own CLI (`railcall market module verify`): `✓ signature valid`, `ownership: ✓ signed by your local key`.
- **Release reproducibility**: `tools/build_release.py` + `tools/release_acceptance_test.py` confirm the packaged archive is byte-for-byte identical to the committed Git tree and rebuilds deterministically.
- **Real end-to-end write, not a mock — re-verified on v1.0.3 (free)**: executed a real `notion.search` (receipt `cmd_20260829T012119Z_notion_search_4398ede7_executed_0003.json`, `http_status: 200`, returned 5 real results including the live "Test Tasks" data source, integrity `sha256:a51684de5b9cfe316f718a9030ad9235c41c25c657c5083ce6fab222acc65e4a`) followed by an approved, executed `notion.create_page` against that data source through RailCall Studio's preview → approve → execute airlock (receipt `cmd_20260829T012240Z_notion_create_page_30a11898_executed_0006.json`, `http_status: 200`, integrity `sha256:0d836d53cce2df9911a36df7036c401eb15946065b91f7caa390cc5aa15b9b6c`, signed with key `ecac7bc46608cb35`). Both commands show `mode: "write_requires_approval"` in the receipt even for the read — Station's `a2d3bf` policy upgrading every command on a network-capable module, exactly as documented in README/Troubleshooting, not a defect. The resulting page, "Notion Guard v1.0.3 free reversion test," was confirmed visible live in the Test Tasks database. (An earlier end-to-end pass exists from the module's brief paid period — receipts `cmd_20260828T165238Z_notion_search_475cc19c_executed_0004.json` and `cmd_20260828T171009Z_notion_create_page_db9b3fa2_executed_0008.json` — superseded by the pair above as the current evidence.)
- **Sandbox enforcement, not just declaration**: Station's own boot log shows the gate actually installed for this module: `network gate armed — allow: ['api.notion.com']`, `subprocess gate CLOSED`, `filesystem-write gate active — allow: (none)`.

## Trust declaration

Notion Guard's signed manifest declares `allowed_destinations` as exactly the Notion API host (`api.notion.com`) and zero LLM/model-provider entries. The module talks only to the Notion REST API and does not send page or database data to a model-provider SDK or RailCall model-completion primitive.
