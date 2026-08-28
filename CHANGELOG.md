# Changelog

## 1.0.0

Initial release. Ten commands against the real Notion REST API (`Notion-Version: 2026-03-11`, the data-source architecture introduced 2025-09-03):

- Reads: `notion.search`, `notion.get_data_source_schema`, `notion.query_data_source`, `notion.get_page`, `notion.get_page_content`, `notion.list_users`.
- Writes (`write_requires_approval`): `notion.create_page`, `notion.update_page_properties`, `notion.append_blocks`, `notion.create_comment`.

Vault-only credentials, certifi-backed TLS, one HTTP attempt per write with unknown-outcome reporting on timeout/5xx, and a signed manifest declaring `allowed_destinations: []`.
