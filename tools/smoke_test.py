#!/usr/bin/env python3
"""
Safe local smoke test for Notion Guard.

Executes read commands and previews writes. It never approves or executes a
write command.
"""

from __future__ import annotations

import argparse
import functools
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_ENDPOINT = "http://127.0.0.1:8799"
DEFAULT_WORKSPACE = Path.home() / ".railcall" / "station" / ".railcall_workspace"


class SmokeFailure(RuntimeError):
    pass


def _discover_session_token(workspace: Path) -> str:
    """Same discovery order RailCall's own MCP server uses in
    mcp_server.py's _station_execute_command: try the CLI-specific token
    first, then the main per-startup session token. Both are same-user,
    0600 local files under the workspace directory Studio was started with."""
    for name in ("cli_session_token", "session_token"):
        path = workspace / name
        try:
            token = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if token:
            return token
    raise SmokeFailure(
        f"No session token found under {workspace}. Is RailCall Studio running? "
        "Pass --session-token or --workspace to point at the right instance."
    )


def call(
    endpoint: str, route: str, payload: dict[str, Any], session_token: str
) -> dict[str, Any]:
    request = urllib.request.Request(
        endpoint.rstrip("/") + route,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Origin": endpoint.rstrip("/"),
            "X-RailCall-Session": session_token,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SmokeFailure(f"HTTP {exc.code} from {route}: {body[:400]}") from exc
    except urllib.error.URLError as exc:
        raise SmokeFailure(f"Could not reach RailCall Studio: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise SmokeFailure(f"RailCall returned invalid JSON from {route}") from exc


def execute(
    endpoint: str, command_id: str, inputs: dict[str, Any], session_token: str
) -> dict[str, Any]:
    return call(
        endpoint,
        "/api/commands/execute",
        {
            "command_id": command_id,
            "inputs": inputs,
            "intent": f"Notion Guard smoke test: {command_id}",
        },
        session_token,
    )


def preview(
    endpoint: str, command_id: str, inputs: dict[str, Any], session_token: str
) -> dict[str, Any]:
    return call(
        endpoint,
        "/api/commands/preview",
        {
            "command_id": command_id,
            "inputs": inputs,
            "intent": f"Notion Guard safe preview: {command_id}",
        },
        session_token,
    )


def receipt_output(result: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    receipt = result.get("receipt")
    if not isinstance(receipt, dict):
        raise SmokeFailure("response contains no receipt object")
    output = receipt.get("output")
    if output is None:
        output = {}
    if not isinstance(output, dict):
        raise SmokeFailure("receipt output is not an object")
    return receipt, output


def require_executed(name: str, result: dict[str, Any]) -> dict[str, Any]:
    receipt, output = receipt_output(result)
    status = receipt.get("result_status")
    if status not in {"executed", "ok"}:
        raise SmokeFailure(f"{name} did not execute successfully: {status!r}")
    if output.get("http_status") != 200:
        raise SmokeFailure(f"{name} returned HTTP {output.get('http_status')!r}")
    print(f"PASS read: {name}")
    return output


def load_list(output: dict[str, Any], field: str) -> list[dict[str, Any]]:
    raw = output.get(field) or "[]"
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SmokeFailure(f"{field} is not complete JSON") from exc
    if not isinstance(value, list):
        raise SmokeFailure(f"{field} is not a list")
    return [item for item in value if isinstance(item, dict)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--search", default="")
    parser.add_argument(
        "--workspace",
        default=str(DEFAULT_WORKSPACE),
        help="RailCall Studio workspace dir (.railcall_workspace) to read the session token from.",
    )
    parser.add_argument(
        "--session-token",
        default=None,
        help="Session token to send as X-RailCall-Session. Auto-discovered from --workspace if omitted.",
    )
    parser.add_argument(
        "--report",
        default="notion-guard-smoke-report.json",
        help="Path for the redacted JSON report.",
    )
    args = parser.parse_args()

    session_token = args.session_token or _discover_session_token(Path(args.workspace))
    execute = functools.partial(globals()["execute"], session_token=session_token)
    preview = functools.partial(globals()["preview"], session_token=session_token)

    report: dict[str, Any] = {
        "endpoint": args.endpoint,
        "reads": {},
        "write_previews": {},
    }

    search_output = require_executed(
        "notion.search",
        execute(args.endpoint, "notion.search", {"query": args.search, "page_size": 10}),
    )
    search_results = load_list(search_output, "results_json")
    report["reads"]["search"] = {"returned": len(search_results)}

    data_sources = [r for r in search_results if r.get("object") == "data_source"]
    pages = [r for r in search_results if r.get("object") == "page"]

    if data_sources:
        data_source_id = data_sources[0]["id"]

        schema_output = require_executed(
            "notion.get_data_source_schema",
            execute(
                args.endpoint,
                "notion.get_data_source_schema",
                {"data_source_id": data_source_id},
            ),
        )
        report["reads"]["data_source_schema"] = {
            "property_count": schema_output.get("property_count"),
        }

        query_output = require_executed(
            "notion.query_data_source",
            execute(
                args.endpoint,
                "notion.query_data_source",
                {"data_source_id": data_source_id, "page_size": 10},
            ),
        )
        queried = load_list(query_output, "results_json")
        report["reads"]["query_data_source"] = {"returned": len(queried)}
        if not pages and queried:
            pages = [{"id": row["id"]} for row in queried]
    else:
        print("INFO: no data source visible to this connection; skipping schema/query checks")

    if pages:
        page_id = pages[0]["id"]

        page_output = require_executed(
            "notion.get_page",
            execute(args.endpoint, "notion.get_page", {"page_id": page_id}),
        )
        report["reads"]["get_page"] = {"url_present": bool(page_output.get("url"))}

        content_output = require_executed(
            "notion.get_page_content",
            execute(args.endpoint, "notion.get_page_content", {"page_id": page_id}),
        )
        report["reads"]["get_page_content"] = {
            "returned": content_output.get("returned_count"),
        }
    else:
        page_id = None
        print("INFO: no page visible to this connection; skipping page/content checks")

    users_output = require_executed(
        "notion.list_users",
        execute(args.endpoint, "notion.list_users", {"page_size": 10}),
    )
    users = load_list(users_output, "users_json")
    report["reads"]["list_users"] = {"returned": len(users)}

    write_payloads: dict[str, dict[str, Any]] = {
        "notion.create_page": {
            "parent_type": "data_source_id" if data_sources else "page_id",
            "parent_id": (data_sources[0]["id"] if data_sources else (page_id or "preview-only-id")),
            "properties_json": json.dumps(
                {"Name": {"title": [{"text": {"content": "Notion Guard safe preview"}}]}}
            ),
        },
        "notion.update_page_properties": {
            "page_id": page_id or "preview-only-id",
            "properties_json": json.dumps(
                {"Name": {"title": [{"text": {"content": "Preview only, not executed"}}]}}
            ),
        },
        "notion.append_blocks": {
            "block_id": page_id or "preview-only-id",
            "children_json": json.dumps(
                [{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "Preview only."}}]}}]
            ),
        },
        "notion.create_comment": {
            "parent_type": "page_id",
            "parent_id": page_id or "preview-only-id",
            "text": "Notion Guard safe smoke-test preview. This is not executed.",
        },
    }

    for command_id, inputs in write_payloads.items():
        result = preview(args.endpoint, command_id, inputs)
        if not isinstance(result, dict):
            raise SmokeFailure(f"{command_id} preview returned no object")
        report["write_previews"][command_id] = {"response_received": True}
        print(f"PASS preview only: {command_id}")

    report_path = Path(args.report)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print()
    print("SAFE SMOKE TEST PASSED")
    print("No write command was approved or executed.")
    print(f"Redacted report: {report_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeFailure as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
