# Demo Video Script

1. Show Notion Guard loaded in RailCall Studio: v1.0.0, signature verified, 10 commands.
2. Run `notion.search` to find a test database; run `notion.get_data_source_schema` on it and point out the real property names/options it returns.
3. Preview `notion.create_page` using those exact property names — show the full payload RailCall is about to send.
4. Approve the write. Show the new page appear in the real Notion workspace.
5. Open the signed receipt and verify it independently.
6. Briefly show one blocked-before-approval example (a preview that was never approved) to demonstrate the gate.
7. Close on the governance summary: every write previewed, approved, and receipted; zero model-provider egress declared in the signed manifest.

Never show the API key, the approval code, or full page UUIDs on screen.
