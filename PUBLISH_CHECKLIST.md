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
dist/notion-guard-v1.0.0.zip
dist/notion-guard-v1.0.0.files.json
```

**Do not proceed if `release_acceptance_test.py` fails for any reason**, including the official-CLI check being unavailable — investigate and fix, don't skip.

## 5. Push, review, and merge

Push and wait for Python 3.10, 3.12, and 3.13 CI to go green on `.github/workflows/notion-guard-tests.yml`. Merge only after every check passes.

After merging, update local `main` and repeat steps 3–4 against the merged commit before moving on.

## 6. Remaining before an actual `railcall market publish`

- [ ] Flip the GitHub repo from private to public (or grant reviewer access) — `README.md`/CI links won't resolve to reviewers otherwise.
- [ ] Record the demo video per `VIDEO_SCRIPT.md` and fill in the URL in `CONTEST_SUBMISSION.md`.
- [ ] Fill in the marketplace listing URL in `CONTEST_SUBMISSION.md` once step 7 below produces one.

## 7. Publish once

Publish only from a verified, clean `main` where steps 1–5 above all passed on the latest commit:

```bash
railcall market publish . --type=module
```

**Do not repeatedly publish while debugging.** Preserve the marketplace output and the signed receipt evidence. This step requires explicit sign-off — confirm before running it, every time.
