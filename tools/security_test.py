#!/usr/bin/env python3
"""Focused offline security tests for Notion Guard."""

from __future__ import annotations

import importlib.util
import io
import urllib.error
from pathlib import Path

# Synthetic fixture assembled in pieces to avoid secret-scanner false positives.
TEST_NOTION_TOKEN = "".join(("ntn", "_", "testfixture1234567890"))


ROOT = Path(__file__).resolve().parents[1]
HANDLER = ROOT / "handlers" / "handler.py"


def load_handler():
    spec = importlib.util.spec_from_file_location("notion_guard_handler", HANDLER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def expect_runtime_error(callable_, contains: str) -> None:
    try:
        callable_()
    except RuntimeError as exc:
        if contains.lower() not in str(exc).lower():
            raise AssertionError(f"expected {contains!r} in {exc!r}") from exc
    else:
        raise AssertionError("expected RuntimeError")


def main() -> int:
    source = HANDLER.read_text(encoding="utf-8")
    forbidden = [
        "credentials.local.json",
        "subprocess",
        "shutil",
        "os.environ",
        "os.getenv",
    ]
    for text in forbidden:
        assert text not in source, f"forbidden source text remains: {text}"
    print("PASS: no credential-file, environment, or subprocess fallback")

    h = load_handler()

    h.__rc_helpers__ = {"vault_get": lambda provider: TEST_NOTION_TOKEN}
    assert h._load_api_key() == TEST_NOTION_TOKEN
    assert h._extract_api_key({"fields": {"NOTION_API_KEY": " key "}}) == "key"
    # RailCall Station's credential_resolver.resolve() returns the bare
    # fields dict directly for named credentials saved through Studio
    # Integrations (no "fields" wrapper) - this must also resolve.
    assert h._extract_api_key({"NOTION_API_KEY": " key2 "}) == "key2"
    print("PASS: vault_get supplies string, wrapped-fields, and bare-fields shapes")

    h.__rc_helpers__ = {"vault_get": lambda provider: None}
    expect_runtime_error(h._load_api_key, "not configured")
    h.__rc_helpers__ = {}
    expect_runtime_error(h._load_api_key, "vault_get")
    print("PASS: missing vault configuration fails clearly")

    secret = TEST_NOTION_TOKEN
    redacted = h._redact(f"Authorization: Bearer {secret}", secret)
    assert secret not in redacted
    assert "[REDACTED]" in redacted
    print("PASS: active secret redaction")

    # Pattern-based redaction must catch a credential-shaped string even when
    # it is NOT the exact `secret` argument passed in (defense in depth,
    # matching Linear Guard's regex-based _redact design) - not just literal
    # substring replacement of a known value.
    leaked_token = "ntn_" + "a1b2c3d4e5f6g7h8i9j0k1l2m3"
    assert leaked_token not in h._redact(f"leak: {leaked_token}", "unrelated")
    assert "some-header-value" not in h._redact(
        "Authorization: some-header-value", "unrelated"
    )
    assert "field-value-here" not in h._redact(
        "NOTION_API_KEY=field-value-here", "unrelated"
    )
    # A leading \b word-boundary requirement let a token glued directly onto a
    # preceding word character (no separator) through unredacted - e.g. an
    # exception message that happens to read "...mysecret_<token>..." rather
    # than "...my secret_<token>..." or "...my=secret_<token>...".
    glued_token = "a1b2c3d4e5f6g7h8i9j0k1l2m3"
    assert glued_token not in h._redact(f"prefixntn_{glued_token}", "unrelated")
    assert glued_token not in h._redact(f"wordsecret_{glued_token}", "unrelated")
    print("PASS: pattern-based redaction (token shape, Authorization header, field name, glued-on tokens)")

    calls = {"count": 0}
    original_urlopen = h.urllib.request.urlopen

    def failing_urlopen(*args, **kwargs):
        calls["count"] += 1
        raise urllib.error.URLError("timed out")

    h.urllib.request.urlopen = failing_urlopen
    try:
        try:
            h._request("POST", "/pages", secret, body={}, is_write=True)
        except RuntimeError as exc:
            assert "outcome is unknown" in str(exc)
            assert exc.__cause__ is None
        else:
            raise AssertionError("expected unknown write outcome")
        assert calls["count"] == 1, "write transport was retried"
    finally:
        h.urllib.request.urlopen = original_urlopen
    print("PASS: mutation transport makes one attempt and hides low-level cause")

    class _FakeHTTPError(urllib.error.HTTPError):
        def __init__(self, code, body, headers=None):
            super().__init__("http://x", code, "msg", headers or {}, io.BytesIO(body))

    def rate_limited_urlopen(*args, **kwargs):
        raise _FakeHTTPError(429, b'{"message": "rate limited"}')

    h.urllib.request.urlopen = rate_limited_urlopen
    try:
        expect_runtime_error(
            lambda: h._request("GET", "/search", secret), "rate limit"
        )
    finally:
        h.urllib.request.urlopen = original_urlopen
    print("PASS: HTTP 429 gets a clear rate-limit message, not a generic HTTP-error one")

    def rate_limited_with_retry_after(*args, **kwargs):
        raise _FakeHTTPError(
            429, b'{"message": "rate limited"}', headers={"Retry-After": "30"}
        )

    h.urllib.request.urlopen = rate_limited_with_retry_after
    try:
        expect_runtime_error(
            lambda: h._request("GET", "/search", secret), "30 seconds"
        )
    finally:
        h.urllib.request.urlopen = original_urlopen
    print("PASS: HTTP 429 with a Retry-After header surfaces the actual wait time")

    expect_runtime_error(
        lambda: h.notion_create_page(
            {"parent_type": "bogus", "parent_id": "x", "properties_json": "{}"},
            None,
        ),
        "parent_type",
    )
    expect_runtime_error(
        lambda: h.notion_update_page_properties({"page_id": "p"}, None),
        "at least one",
    )
    expect_runtime_error(
        lambda: h.notion_append_blocks(
            {"block_id": "b", "children_json": "[" + ",".join(["{}"] * 101) + "]"},
            None,
        ),
        "100",
    )
    print("PASS: important write inputs fail before network access")

    context = h._build_tls_context()
    assert context.verify_mode != 0 and context.check_hostname is True
    print("PASS: certifi-backed TLS verification is enabled")

    print("SECURITY TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
