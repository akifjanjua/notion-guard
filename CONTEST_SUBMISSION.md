# RailCall Contest Entry — Notion Guard

## Title

Notion Guard — Governed Notion Integration

## Repository

https://github.com/akifjanjua/notion-guard (branch `main`, HEAD `df9c6700b09c01636b0f45067746dbf27480cdf0` at time of writing — check the branch for later commits)

The repository is **public** — README and CI links resolve for anyone.

## Description

Notion Guard is a governance-first RailCall module for small teams running their work through Notion. It provides 10 focused commands against the real Notion REST API (`Notion-Version: 2026-03-11`, the data-source architecture introduced 2025-09-03): search across pages and data sources, inspect a data source's property schema, query/filter/sort a data source's rows, read a page's properties and block content, list workspace users, create a page, update a page's properties or trash status, append content blocks, and create a comment or discussion reply.

The four write commands (`create_page`, `update_page_properties`, `append_blocks`, `create_comment`) cannot run silently. RailCall previews the exact payload, blocks it until a human approves it, executes only the approved action, and records the result in a signed receipt that can be independently verified. The six read commands execute immediately — they cannot alter workspace state, so gating them would only add friction.

Two of the six read commands — `notion.get_data_source_schema` and `notion.list_users` — were chosen specifically for usability rather than coverage: they let a caller confirm real property names, option values, and teammate identities before a write is attempted, so a first write is far more likely to succeed instead of failing on a guessed field name or a raw UUID.

Notion Guard resolves credentials only through RailCall's vault helper, uses certifi-backed verified HTTPS, never invokes curl or another subprocess, actively redacts credentials from errors, and never automatically retries writes with an uncertain outcome. `module.json` declares a `requires` sandbox block (`network: ["api.notion.com"]`, `subprocess: false`, `filesystem_writes: []`) that RailCall Station enforces at handler-load time, not just documents.

I tested it against the real Notion REST API with no mocks or stubs. The public CI workflow (GitHub Actions) tests Python 3.10, 3.12, and 3.13, runs an offline security suite and a model-provider egress contract test, and verifies the final release archive byte-for-byte against the committed Git tree. Latest green run: https://github.com/akifjanjua/notion-guard/actions/runs/33226988611

Marketplace listing: https://railcall.ai/marketplace/muhammad-akif-janjua/notion-guard — **$69, one-time purchase** (`license_required: true`), v1.0.4. Paid listings on this platform don't render the structured `WHAT IT DOES` command breakdown or `Provenance: commands` count that free listings get — confirmed as universal platform behavior across every paid listing checked (Zernio $160/mo, Salesforce CRM $199/mo, and this module's own brief free period showed the full breakdown, matching Linear Guard/HubSpot CRM). RailCall's team confirmed this is a real gap with a permanent fix pending, and gave a short-term workaround: `module.json`'s `description` field now lists all 10 commands by name with a one-line purpose each. Verified live after publishing v1.0.4: the listing's free-text `OVERVIEW` section does show the full command list; the structured `WHAT IT DOES`/`Provenance` widget still shows `commands —`/"metadata-only" — the workaround restores the information a buyer needs pre-purchase, not the widget itself.

README URL: https://github.com/akifjanjua/notion-guard/blob/main/README.md

Demo video: **[PASTE UNLISTED YOUTUBE URL — record per `VIDEO_SCRIPT.md`, not yet filmed]**

`contest:2026Q3`

## Verification evidence

- **Signature**: signed with the real registered publisher key (fingerprint `e469d55383447fc6b95cbffb786fee7c…`), independently verified both by this repo's own `tools/verify_module_tree.py` (Ed25519, RailCall v2 tree spec) and by RailCall's own CLI (`railcall market module verify`): `✓ signature valid`, `ownership: ✓ signed by your local key`.
- **Release reproducibility**: `tools/build_release.py` + `tools/release_acceptance_test.py` confirm the packaged archive is byte-for-byte identical to the committed Git tree and rebuilds deterministically.
- **Real end-to-end write, not a mock — verified on v1.0.3 (free); still current for v1.0.4 (paid)**: v1.0.4 changed only `module.json`'s `description`, `license_required`, and `version` — `handlers/handler.py` is byte-identical to v1.0.3, so this evidence still reflects the module's real behavior. Executed a real `notion.search` (receipt `cmd_20260829T012119Z_notion_search_4398ede7_executed_0003.json`, `http_status: 200`, returned 5 real results including the live "Test Tasks" data source, integrity `sha256:a51684de5b9cfe316f718a9030ad9235c41c25c657c5083ce6fab222acc65e4a`) followed by an approved, executed `notion.create_page` against that data source through RailCall Studio's preview → approve → execute airlock (receipt `cmd_20260829T012240Z_notion_create_page_30a11898_executed_0006.json`, `http_status: 200`, integrity `sha256:0d836d53cce2df9911a36df7036c401eb15946065b91f7caa390cc5aa15b9b6c`, signed with key `ecac7bc46608cb35`). Both commands show `mode: "write_requires_approval"` in the receipt even for the read — Station's `a2d3bf` policy upgrading every command on a network-capable module, exactly as documented in README/Troubleshooting, not a defect. The resulting page, "Notion Guard v1.0.3 free reversion test," was confirmed visible live in the Test Tasks database. (An earlier end-to-end pass exists from the module's brief paid period — receipts `cmd_20260828T165238Z_notion_search_475cc19c_executed_0004.json` and `cmd_20260828T171009Z_notion_create_page_db9b3fa2_executed_0008.json` — superseded by the pair above as the current evidence.)
- **Sandbox enforcement, not just declaration**: Station's own boot log shows the gate actually installed for this module: `network gate armed — allow: ['api.notion.com']`, `subprocess gate CLOSED`, `filesystem-write gate active — allow: (none)`.

## Trust declaration

Notion Guard's signed manifest declares `allowed_destinations` as exactly the Notion API host (`api.notion.com`) and zero LLM/model-provider entries. The module talks only to the Notion REST API and does not send page or database data to a model-provider SDK or RailCall model-completion primitive.
