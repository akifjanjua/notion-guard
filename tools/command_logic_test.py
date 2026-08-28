#!/usr/bin/env python3
"""Command-logic tests for Notion Guard.

Mocks the transport layer (_request) with realistic Notion API response
shapes, then calls the real command functions and the data-transformation
helpers directly, asserting on actual computed output. Offline only - no
network access, no credentials. Mirrors the pattern in Linear Guard's
tools/v15_read_test.py (mock the transport, exercise the real handler
functions, assert on real output) rather than only testing input
validation and low-level transport mechanics.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDLER = ROOT / "handlers" / "handler.py"


def load_handler():
    spec = importlib.util.spec_from_file_location("notion_guard_handler", HANDLER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    module.__rc_helpers__ = {"vault_get": lambda provider: "sk-test-token"}
    return module


def rich_text(content: str) -> list[dict]:
    return [{"type": "text", "text": {"content": content}, "plain_text": content}]


def test_simplify_helpers(h) -> None:
    assert h._simplify_rich_text(rich_text("Hello ") + rich_text("World")) == "Hello World"
    assert h._simplify_rich_text(None) == ""
    assert h._simplify_rich_text("not-a-list") == ""

    assert h._simplify_property({"type": "title", "title": rich_text("Task one")}) == "Task one"
    assert h._simplify_property({"type": "rich_text", "rich_text": rich_text("notes")}) == "notes"
    assert h._simplify_property({"type": "select", "select": {"name": "Done"}}) == "Done"
    assert h._simplify_property({"type": "select", "select": None}) is None
    assert h._simplify_property({"type": "status", "status": {"name": "In progress"}}) == "In progress"
    assert h._simplify_property(
        {"type": "multi_select", "multi_select": [{"name": "Bug"}, {"name": "Urgent"}]}
    ) == ["Bug", "Urgent"]
    assert h._simplify_property({"type": "date", "date": {"start": "2026-01-01", "end": None}}) == {
        "start": "2026-01-01",
        "end": None,
    }
    assert h._simplify_property({"type": "checkbox", "checkbox": True}) is True
    assert h._simplify_property({"type": "number", "number": 42}) == 42
    assert h._simplify_property(
        {"type": "people", "people": [{"name": "Akif", "id": "u1"}, {"name": None, "id": "u2"}]}
    ) == ["Akif", "u2"]
    assert h._simplify_property({"type": "relation", "relation": [{"id": "r1"}, {"id": "r2"}]}) == [
        "r1",
        "r2",
    ]
    assert h._simplify_property({"type": "url", "url": "https://example.com"}) == "https://example.com"
    assert h._simplify_property({"type": "email", "email": "a@example.com"}) == "a@example.com"
    assert h._simplify_property({"type": "formula", "formula": {"string": "x"}}) is None
    assert h._simplify_property("not-a-dict") is None

    props = {
        "Status": {"type": "select", "select": {"name": "Done"}},
        "Name": {"type": "title", "title": rich_text("My Task")},
    }
    assert h._simplify_properties(props) == {"Status": "Done", "Name": "My Task"}
    assert h._simplify_properties(None) == {}
    assert h._title_from_properties(props) == "My Task"
    assert h._title_from_properties({}) == ""

    block = {
        "id": "b1",
        "type": "paragraph",
        "has_children": False,
        "paragraph": {"rich_text": rich_text("hello block")},
    }
    assert h._simplify_block(block) == {
        "id": "b1",
        "type": "paragraph",
        "text": "hello block",
        "has_children": False,
    }
    assert h._simplify_block({"id": "b2", "type": "divider", "divider": {}}) == {
        "id": "b2",
        "type": "divider",
        "text": "",
        "has_children": False,
    }
    assert h._simplify_block("not-a-dict") == {}
    print("PASS: data-transformation helpers (_simplify_rich_text, _simplify_property "
          "for all 15 property types, _simplify_properties, _title_from_properties, "
          "_simplify_block)")


def test_extract_error_message(h) -> None:
    assert h._extract_error_message(
        '{"message": "bad request", "code": "validation_error"}'
    ) == "bad request [validation_error]"
    assert h._extract_error_message('{"message": "bad request"}') == "bad request"
    long_message = "x" * 500
    capped = h._extract_error_message(
        json.dumps({"message": long_message, "code": "validation_error"})
    )
    assert len(capped) == 300
    print("PASS: _extract_error_message (code surfaced alongside message, still capped at 300)")


def test_notion_search(h) -> None:
    def fake_request(method, path, api_key, body=None, query=None, is_write=False):
        assert method == "POST" and path == "/search"
        assert body["query"] == "Test Tasks"
        assert body["filter"] == {"value": "data_source", "property": "object"}
        return 200, {
            "results": [
                {
                    "object": "data_source",
                    "id": "ds-1",
                    "title": rich_text("Test Tasks"),
                    "url": "https://notion.so/ds-1",
                },
                {
                    "object": "page",
                    "id": "pg-1",
                    "url": "https://notion.so/pg-1",
                    "properties": {"Name": {"type": "title", "title": rich_text("Ship it")}},
                },
            ],
            "next_cursor": "cursor-1",
            "has_more": True,
        }

    h._request = fake_request
    out, _ = h.notion_search(
        {"query": "Test Tasks", "object_type": "data_source", "page_size": 10}, None
    )
    results = json.loads(out["results_json"])
    assert out["returned_count"] == 2
    assert results[0] == {"id": "ds-1", "object": "data_source", "title": "Test Tasks", "url": "https://notion.so/ds-1"}
    assert results[1] == {"id": "pg-1", "object": "page", "title": "Ship it", "url": "https://notion.so/pg-1"}
    assert out["next_cursor"] == "cursor-1"
    assert out["has_more"] is True

    try:
        h.notion_search({"object_type": "bogus"}, None)
        raise AssertionError("expected object_type rejection")
    except RuntimeError as exc:
        assert "object_type" in str(exc)
    print("PASS: notion_search (title extraction for page + data_source, filter, pagination)")


def test_get_data_source_schema(h) -> None:
    def fake_request_direct(method, path, api_key, body=None, query=None, is_write=False):
        assert method == "GET" and path == "/data_sources/ds-1"
        return 200, {
            "id": "ds-1",
            "title": rich_text("Test Tasks"),
            "properties": {
                "Name": {"id": "title", "type": "title"},
                "Status": {
                    "id": "st1",
                    "type": "status",
                    "status": {"options": [{"name": "Not started"}, {"name": "Done"}]},
                },
                "Tags": {
                    "id": "ms1",
                    "type": "multi_select",
                    "multi_select": {"options": [{"name": "Bug"}, {"name": "Urgent"}]},
                },
                "Related": {"id": "rel1", "type": "relation"},
            },
        }

    h._request = fake_request_direct
    out, _ = h.notion_get_data_source_schema({"data_source_id": "ds-1"}, None)
    props = json.loads(out["properties_json"])
    assert out["title"] == "Test Tasks"
    assert out["property_count"] == 4
    assert props["Status"]["type"] == "status" and props["Status"]["options"] == ["Not started", "Done"]
    assert props["Tags"]["options"] == ["Bug", "Urgent"]
    assert "options" not in props["Related"]
    print("PASS: notion_get_data_source_schema direct data_source_id path (options extraction)")

    calls = []

    def fake_request_resolve(method, path, api_key, body=None, query=None, is_write=False):
        calls.append(path)
        if path == "/databases/db-1":
            return 200, {"data_sources": [{"id": "ds-resolved"}]}
        assert path == "/data_sources/ds-resolved"
        return 200, {"id": "ds-resolved", "title": [], "properties": {}}

    h._request = fake_request_resolve
    out, _ = h.notion_get_data_source_schema({"database_id": "db-1"}, None)
    assert calls == ["/databases/db-1", "/data_sources/ds-resolved"]
    assert out["data_source_id"] == "ds-resolved"
    print("PASS: notion_get_data_source_schema database_id -> data_source_id resolution")

    def fake_request_multi(method, path, api_key, body=None, query=None, is_write=False):
        return 200, {"data_sources": [{"id": "ds-a"}, {"id": "ds-b"}]}

    h._request = fake_request_multi
    try:
        h.notion_get_data_source_schema({"database_id": "db-multi"}, None)
        raise AssertionError("expected multi-data-source rejection")
    except RuntimeError as exc:
        assert "ds-a" in str(exc) and "ds-b" in str(exc)
    print("PASS: notion_get_data_source_schema multi-data-source database rejected with ids listed")


def test_query_data_source(h) -> None:
    def fake_request(method, path, api_key, body=None, query=None, is_write=False):
        assert method == "POST" and path == "/data_sources/ds-1/query"
        assert body["filter"] == {"property": "Status", "select": {"equals": "Done"}}
        return 200, {
            "results": [
                {
                    "id": "row-1",
                    "url": "https://notion.so/row-1",
                    "in_trash": False,
                    "properties": {
                        "Name": {"type": "title", "title": rich_text("Task A")},
                        "Status": {"type": "status", "status": {"name": "Done"}},
                    },
                }
            ],
            "next_cursor": None,
            "has_more": False,
        }

    h._request = fake_request
    out, _ = h.notion_query_data_source(
        {
            "data_source_id": "ds-1",
            "filter_json": json.dumps({"property": "Status", "select": {"equals": "Done"}}),
        },
        None,
    )
    results = json.loads(out["results_json"])
    assert results[0]["properties"] == {"Name": "Task A", "Status": "Done"}
    assert out["has_more"] is False
    print("PASS: notion_query_data_source (filter passthrough, simplified row properties)")


def test_get_page(h) -> None:
    def fake_request(method, path, api_key, body=None, query=None, is_write=False):
        assert method == "GET" and path == "/pages/pg-1"
        return 200, {
            "id": "pg-1",
            "url": "https://notion.so/pg-1",
            "in_trash": False,
            "parent": {"type": "data_source_id", "data_source_id": "ds-1"},
            "properties": {"Name": {"type": "title", "title": rich_text("My Page")}},
            "created_time": "2026-01-01T00:00:00.000Z",
            "last_edited_time": "2026-01-02T00:00:00.000Z",
        }

    h._request = fake_request
    out, _ = h.notion_get_page({"page_id": "pg-1"}, None)
    assert json.loads(out["properties_json"]) == {"Name": "My Page"}
    assert json.loads(out["parent_json"]) == {"type": "data_source_id", "data_source_id": "ds-1"}
    print("PASS: notion_get_page (properties + parent simplification)")


def test_get_page_content(h) -> None:
    def fake_request(method, path, api_key, body=None, query=None, is_write=False):
        assert method == "GET"
        return 200, {
            "results": [
                {"id": "b1", "type": "paragraph", "has_children": False,
                 "paragraph": {"rich_text": rich_text("hi")}},
            ],
            "next_cursor": None,
            "has_more": False,
        }

    h._request = fake_request
    out, _ = h.notion_get_page_content({"page_id": "pg-1"}, None)
    assert out["block_id"] == "pg-1"
    assert json.loads(out["blocks_json"])[0]["text"] == "hi"

    out, _ = h.notion_get_page_content({"block_id": "blk-9"}, None)
    assert out["block_id"] == "blk-9"

    try:
        h.notion_get_page_content({}, None)
        raise AssertionError("expected missing page_id/block_id rejection")
    except RuntimeError as exc:
        assert "page_id or block_id" in str(exc)
    print("PASS: notion_get_page_content (page_id path, block_id path, missing-both rejection)")


def test_list_users(h) -> None:
    def fake_request(method, path, api_key, body=None, query=None, is_write=False):
        assert method == "GET" and path == "/users"
        return 200, {
            "results": [
                {"id": "u1", "name": "Akif", "type": "person", "person": {"email": "a@example.com"}},
                {"id": "u2", "name": "Notion Guard Bot", "type": "bot", "bot": {}},
            ],
            "next_cursor": None,
            "has_more": False,
        }

    h._request = fake_request
    out, _ = h.notion_list_users({}, None)
    users = json.loads(out["users_json"])
    assert users[0]["email"] == "a@example.com"
    assert "email" not in users[1]
    print("PASS: notion_list_users (email surfaced for person, omitted for bot)")


def test_create_page(h) -> None:
    def fake_request(method, path, api_key, body=None, query=None, is_write=False):
        assert method == "POST" and path == "/pages" and is_write is True
        assert body["parent"] == {"type": "data_source_id", "data_source_id": "ds-1"}
        assert body["properties"]["Name"]["title"][0]["text"]["content"] == "New task"
        # Notion's real response echoes properties back fully typed (the
        # request body itself omits "type" - only the response includes it),
        # so the fixture must not just echo body["properties"] verbatim.
        return 200, {
            "id": "pg-new",
            "url": "https://notion.so/pg-new",
            "parent": body["parent"],
            "properties": {"Name": {"type": "title", "title": rich_text("New task")}},
            "created_time": "2026-01-01T00:00:00.000Z",
        }

    h._request = fake_request
    out, _ = h.notion_create_page(
        {
            "parent_type": "data_source_id",
            "parent_id": "ds-1",
            "properties_json": json.dumps(
                {"Name": {"title": [{"text": {"content": "New task"}}]}}
            ),
        },
        None,
    )
    assert out["page_id"] == "pg-new"
    assert json.loads(out["properties_json"]) == {"Name": "New task"}

    try:
        h.notion_create_page({"parent_type": "bogus", "parent_id": "x", "properties_json": "{}"}, None)
        raise AssertionError("expected parent_type rejection")
    except RuntimeError:
        pass
    print("PASS: notion_create_page (body shape, response simplification, parent_type validation)")


def test_update_page_properties(h) -> None:
    def fake_request(method, path, api_key, body=None, query=None, is_write=False):
        assert method == "PATCH" and path == "/pages/pg-1" and is_write is True
        assert body == {"in_trash": True}
        return 200, {
            "id": "pg-1",
            "url": "https://notion.so/pg-1",
            "in_trash": True,
            "properties": {},
            "last_edited_time": "2026-01-03T00:00:00.000Z",
        }

    h._request = fake_request
    out, _ = h.notion_update_page_properties({"page_id": "pg-1", "in_trash": True}, None)
    assert out["in_trash"] is True

    try:
        h.notion_update_page_properties({"page_id": "pg-1"}, None)
        raise AssertionError("expected at-least-one-field rejection")
    except RuntimeError as exc:
        assert "at least one" in str(exc)
    print("PASS: notion_update_page_properties (in_trash archive path, at-least-one-field validation)")


def test_append_blocks(h) -> None:
    def fake_request(method, path, api_key, body=None, query=None, is_write=False):
        assert method == "PATCH" and path == "/blocks/blk-1/children" and is_write is True
        assert body["position"] == {"type": "end"}
        return 200, {
            "results": [
                {"id": "b-new", "type": "paragraph", "has_children": False,
                 "paragraph": {"rich_text": rich_text("added")}},
            ]
        }

    h._request = fake_request
    out, _ = h.notion_append_blocks(
        {
            "block_id": "blk-1",
            "children_json": json.dumps(
                [{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "added"}}]}}]
            ),
        },
        None,
    )
    assert out["appended_count"] == 1
    assert json.loads(out["blocks_json"])[0]["text"] == "added"

    try:
        h.notion_append_blocks({"block_id": "b", "children_json": "[" + ",".join(["{}"] * 101) + "]"}, None)
        raise AssertionError("expected 100-block cap rejection")
    except RuntimeError as exc:
        assert "100" in str(exc)
    print("PASS: notion_append_blocks (default position, response simplification, 100-block cap)")


def test_require_id_validation(h) -> None:
    def must_reject(value, expected_fragment):
        try:
            h._require_id(value, "page_id")
            raise AssertionError(f"expected rejection for {value!r}")
        except RuntimeError as exc:
            assert expected_fragment in str(exc), f"{value!r} -> {exc}"

    for bad in ("abc\r\nX-Injected: evil", "abc def", "abc\x00def", "abc\tdef"):
        must_reject(bad, "control character or space")
    for bad in ("../../v1/users", "abc/def", "abc\\def", "/etc/passwd"):
        must_reject(bad, "path separator")
    assert h._require_id("1f2e3d4c-5b6a-7980-9c8d-0e1f2a3b4c5d", "page_id") == (
        "1f2e3d4c-5b6a-7980-9c8d-0e1f2a3b4c5d"
    )

    def poisoned_request(*args, **kwargs):
        raise AssertionError("must not reach the network for an invalid id")

    h._request = poisoned_request
    for field, bad_inputs in (
        ("page_id", {"page_id": "abc\r\nX-Injected: evil"}),
        ("block_id", {"block_id": "../../v1/users"}),
    ):
        try:
            h.notion_get_page(bad_inputs, None) if field == "page_id" else h.notion_append_blocks(
                {**bad_inputs, "children_json": "[{}]"}, None
            )
            raise AssertionError(f"expected {field} rejection before any network call")
        except RuntimeError:
            pass
    print("PASS: _require_id (control characters, path separators rejected; valid ids pass; "
          "commands reject bad ids before any network attempt)")


def test_create_comment(h) -> None:
    def fake_request(method, path, api_key, body=None, query=None, is_write=False):
        assert method == "POST" and path == "/comments" and is_write is True
        assert body["parent"] == {"page_id": "pg-1"}
        return 200, {
            "id": "cm-1",
            "discussion_id": "disc-1",
            "parent": body["parent"],
            "created_time": "2026-01-01T00:00:00.000Z",
        }

    h._request = fake_request
    out, _ = h.notion_create_comment({"parent_type": "page_id", "parent_id": "pg-1", "text": "hello"}, None)
    assert out["comment_id"] == "cm-1"
    assert out["discussion_id"] == "disc-1"

    try:
        h.notion_create_comment({"parent_type": "page_id", "parent_id": "pg-1", "text": "x" * 2001}, None)
        raise AssertionError("expected 2000-char cap rejection")
    except RuntimeError as exc:
        assert "2000" in str(exc)
    print("PASS: notion_create_comment (parent shape, 2000-char cap)")


def main() -> int:
    h = load_handler()
    test_simplify_helpers(h)
    test_extract_error_message(h)
    test_notion_search(h)
    test_get_data_source_schema(h)
    test_query_data_source(h)
    test_get_page(h)
    test_get_page_content(h)
    test_require_id_validation(h)
    test_list_users(h)
    test_create_page(h)
    test_update_page_properties(h)
    test_append_blocks(h)
    test_create_comment(h)
    print("COMMAND LOGIC TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
