# Publish Checklist

1. Replace the placeholder `publisher_pubkey` in `module.json` (currently 64 zero characters) with your real RailCall-registered publisher public key.
2. Sign the committed tree with RailCall's official signing tool to produce the real `module.sig`. The placeholder signature in this repo was produced by a local development Ed25519 keypair for testing `tools/verify_module_tree.py` only — it is **not** a valid RailCall publisher signature and must be replaced before submission.
3. Run, in order: `python tools/validate_release.py`, `python tools/security_test.py`, `python tools/egress_contract_test.py`, `python tools/verify_module_tree.py .`, `python tools/build_release.py`, `python tools/release_acceptance_test.py`.
4. Configure a real Notion internal integration, share a test page/database with it, and run `python tools/smoke_test.py` against a running RailCall Studio instance.
5. Preview and approve one real write against a disposable test page; verify the signed receipt independently.
6. Fill in the bracketed placeholders in `CONTEST_SUBMISSION.md` (listing URL, README URL, demo video URL).
7. Push, open the marketplace listing using `MARKETPLACE_LISTING.md`, and confirm CI is green on `.github/workflows/notion-guard-tests.yml`.
