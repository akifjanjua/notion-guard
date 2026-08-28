# Changelog

## Unreleased

Real changes since the 1.0.0 initial commit (not yet a new tagged version — `module.json` still reads `1.0.0`). Every entry below was committed, offline-tested, re-signed with the real registered publisher key, independently re-verified (both this repo's own `tools/verify_module_tree.py` and RailCall's own `railcall market module verify`), and confirmed green on CI before merging.

### Fixed

- `_extract_api_key` now also recognizes the bare fields-dict shape (`{"NOTION_API_KEY": "..."}`) that RailCall Station's `credential_resolver.resolve()` actually returns for named credentials saved through Studio Integrations, not just the `{"fields": {...}}`-wrapped shape. Without this, a correctly-saved credential still reported "not configured."
- `_bounded_page_size` silently truncated a non-integer float `page_size` (`int(10.9)` → `10`) instead of rejecting it; now raises the same "must be an integer" error a malformed string input already got.
- `_extract_error_message` capped the raw-body fallback at 300 characters but not a `message` field pulled from Notion's own JSON error payload; an unusually long Notion error could land unbounded in a signed receipt. Now capped the same way.
- README.md and SECURITY.md's credential setup instructions pointed installers at the plain `notion` Integrations card. Station auto-namespaces this module's actual vault slot to `muhammad-akif-janjua-notion-guard::notion` because the declared provider (`notion`) collides with Station's own built-in Notion integration — following the old instructions reproduced the exact wrong-card mistake found live while building this module. `docs/TROUBLESHOOTING.md` gained a matching entry.
- `tools/release_acceptance_test.py`'s official-CLI check now invokes `railcall_cli.py` directly with `sys.executable` instead of the `railcall` wrapper script, which on Windows can shell out to a bare `python3` that resolves to the Microsoft Store alias stub even with a working Python on `PATH`.
- Removed a bare `subprocess` mention from `handler.py`'s module docstring that false-positived the security scanner's forbidden-source-text check (reworded to describe the same guarantee without the trigger word).

### Changed

- `module.json` brought up to the current RailCall v2 schema: added `credential_spec`, `category`, `provider_list`, and a `requires` sandbox-gate block (`network: ["api.notion.com"]`, `subprocess: false`, `filesystem_writes: []`) that Station enforces at handler-load time, not just documents. Restructured `allowed_destinations` from an empty list to an explicit `[{"provider":"notion","hosts":["api.notion.com"]}]` declaration, matching the platform's current convention.
- Signed with the real registered publisher key (previously a local throwaway dev key used only to exercise the sign/verify/build/acceptance pipeline end-to-end).
- `tools/smoke_test.py` now authenticates with the `X-RailCall-Session` header (auto-discovered from `cli_session_token`/`session_token` under the Studio workspace directory), matching the same channel RailCall's own MCP server uses. `Origin`/`Referer` alone satisfies Studio's CSRF guard but not session auth, so the smoke test's `/api/commands/execute` and `/api/commands/preview` calls were previously rejected with 403.

### Added

- `notion.get_page_content` now accepts an optional `block_id` input in addition to `page_id` (previously present in the handler but dead — `module.json`'s schema never declared it, so Studio could never pass it). Notion's underlying endpoint reads children from any block, not just a page's top level, so this is real added capability: reading a specific nested block's (e.g. a toggle's) children using an id returned by an earlier call to this same command.

## 1.0.0

Initial release. Ten commands against the real Notion REST API (`Notion-Version: 2026-03-11`, the data-source architecture introduced 2025-09-03):

- Reads: `notion.search`, `notion.get_data_source_schema`, `notion.query_data_source`, `notion.get_page`, `notion.get_page_content`, `notion.list_users`.
- Writes (`write_requires_approval`): `notion.create_page`, `notion.update_page_properties`, `notion.append_blocks`, `notion.create_comment`.

Vault-only credentials, certifi-backed TLS, one HTTP attempt per write with unknown-outcome reporting on timeout/5xx, and a signed manifest declaring `allowed_destinations: []`.
