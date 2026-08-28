# RailCall Contest Entry Draft

## Title

Notion Guard — Governed Notion Integration

## Description

I built Notion Guard as a signed RailCall module for real Notion workspaces. It provides 10 focused commands covering workspace discovery and search, data-source schema inspection, filtered database queries, page and block content reads, workspace user lookup, and approval-controlled page/block/comment writes.

The four write commands cannot run silently. RailCall previews the exact payload, blocks it until a human approves it, executes only the approved action, and records the result in a signed receipt that can be independently verified.

Two of the six read commands — `notion.get_data_source_schema` and `notion.list_users` — were chosen specifically for usability rather than coverage: they let a caller confirm real property names, option values, and teammate identities before a write is attempted, so a first write is far more likely to succeed instead of failing on a guessed field name or a raw UUID.

Notion Guard resolves credentials only through RailCall's vault helper, uses certifi-backed verified HTTPS, never invokes curl or another subprocess, actively redacts credentials from errors, and never automatically retries writes with an uncertain outcome.

I tested it against the real Notion REST API with no mocks or stubs. The public CI workflow tests Python 3.10, 3.12, and 3.13, runs an offline security suite and a model-provider egress contract test, and verifies the final release archive file by file.

Marketplace listing: [PASTE APPROVED LISTING URL]

README URL: [PASTE PUBLIC README URL]

Demo video: [PASTE UNLISTED YOUTUBE URL]

`contest:2026Q3`

## Trust declaration

Notion Guard's signed manifest declares zero LLM/model-provider destinations. The module talks only to the Notion REST API and does not send page or database data to a model-provider SDK or RailCall model-completion primitive.
