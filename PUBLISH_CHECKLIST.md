# Publish Checklist

Current state: signed with the real registered publisher key, credentials configured, one real end-to-end write executed and verified live in Notion. Steps 1–5 below are done; this document is the exact procedure for re-doing them after any future change, and the remaining steps to an actual `railcall market publish`.

## 1. Prepare and commit every signed source change

Work on `main` (or a release branch). Run the complete offline suite before touching signing:

```bash
python tools/validate_release.py
python tools/security_test.py
python tools/command_logic_test.py
python tools/egress_contract_test.py
```

Commit every change except `module.sig`:

```bash
git add -A
git restore --staged module.sig
git commit -m "Prepare Notion Guard vX.Y.Z signed-tree release"
```

The working tree must be clean before signing.

## 2. Sign with the hand-built signer, not `railcall market module sign`

**Do not run `railcall market module sign`.** It is known to rewrite `module.json` in Windows text mode (CRLF), which corrupts the intentional zero-newline byte format the signed tree hash depends on. Sign with the same Ed25519 signer used throughout this project instead: read `~/.railcall/marketplace_publisher.json`'s `seed_hex`, compute `canonical_manifest(module.json) + b"\n" + tree_manifest` via `tools/verify_module_tree.py`'s own `canonical_manifest`/`signed_tree` functions, sign it, write the 128-hex-char result to `module.sig`. Confirm `module.json`'s `publisher_pubkey` matches the registered key's `pubkey_hex` before signing.

Commit the signature:

```bash
git add module.sig
git commit -m "Sign Notion Guard vX.Y.Z module tree"
```

## 3. Verify the committed tree — both verifiers must pass

```bash
python tools/verify_module_tree.py .
python "$HOME/.railcall/railcall_cli.py" market module verify .
```

Both must report a valid v2 tree signature with 10 commands and `ownership: ✓ signed by your local key`. **Do not proceed if either fails.**

## 4. Build and accept the release

```bash
python tools/build_release.py
python tools/release_acceptance_test.py
```

Expected assets:

```text
dist/notion-guard-v1.0.3.zip
dist/notion-guard-v1.0.3.files.json
```

(The version segment tracks `module.json`'s `version` field — update this if it changes again.)

**Do not proceed if `release_acceptance_test.py` fails for any reason**, including the official-CLI check being unavailable — investigate and fix, don't skip.

## 5. Push, review, and merge

Push and wait for Python 3.10, 3.12, and 3.13 CI to go green on `.github/workflows/notion-guard-tests.yml`. Merge only after every check passes.

After merging, update local `main` and repeat steps 3–4 against the merged commit before moving on.

## 6. Remaining before an actual `railcall market publish`

- [x] Flip the GitHub repo from private to public (or grant reviewer access) — `README.md`/CI links won't resolve to reviewers otherwise. Done: repo is public, `homepage`/`tests_url` verified reachable with real unauthenticated requests.
- [ ] Record the demo video per `VIDEO_SCRIPT.md` and fill in the URL in `CONTEST_SUBMISSION.md`.
- [x] Fill in the marketplace listing URL in `CONTEST_SUBMISSION.md` once step 7 below produces one. Done: `railcall market publish` succeeded, listing confirmed live at https://railcall.ai/marketplace/muhammad-akif-janjua/notion-guard — but `railcall market get`/`market list` had not yet indexed it as of publishing; recheck before relying on `railcall market install` working.

## 7. Publish once

Publish only from a verified, clean `main` where steps 1–5 above all passed on the latest commit:

```bash
railcall market publish . --type=module --price=0
```

**Notion Guard is free (`license_required: false`, `price_cents: 0`).** `--price=0` must still be passed explicitly on every republish, not omitted — `price_cents` has no "preserve current value" fallback the way `category` does; it defaults to `0` either way, but pass it explicitly so a future decision to charge again isn't accidentally reverted by an omitted flag reading as "no change" when it actually means "reset to free." Confirmed directly in `railcall_cli.py`'s `_market_publish_module`.

**The marketplace also requires a strictly-increasing `version` to accept a republish at all** (`HTTP 409: version "X" must be strictly greater than the currently published version`) — bump `module.json`'s `version` (and this checklist's dist filenames above) before every republish, even a metadata-only change.

**Do not repeatedly publish while debugging.** Preserve the marketplace output and the signed receipt evidence. This step requires explicit sign-off — confirm before running it, every time.
