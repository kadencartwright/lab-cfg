"""Hermes native tools for T3 Code's ordinary orchestration lifecycle."""

from __future__ import annotations

import json
from typing import Any, Callable

from .client import T3BridgeError, get_task, list_projects, send_message, start_task
from .schemas import (
    T3_GET_TASK_SCHEMA,
    T3_LIST_PROJECTS_SCHEMA,
    T3_SEND_MESSAGE_SCHEMA,
    T3_START_TASK_SCHEMA,
)


def _json_handler(fn: Callable[..., dict[str, Any]], **values: Any) -> str:
    try:
        return json.dumps({"ok": True, **fn(**values)}, ensure_ascii=False)
    except T3BridgeError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    except Exception as exc:  # Fail closed without leaking a traceback or bearer token.
        return json.dumps({"ok": False, "error": f"Unexpected T3 bridge error: {exc}"}, ensure_ascii=False)


def _handle_list_projects(args: dict[str, Any], **_: Any) -> str:
    return _json_handler(list_projects)


def _handle_start_task(args: dict[str, Any], **_: Any) -> str:
    return _json_handler(
        start_task,
        project_name=args.get("project", ""),
        prompt=args.get("prompt", ""),
        base_branch=args.get("base_branch"),
        title=args.get("title"),
    )


def _handle_get_task(args: dict[str, Any], **_: Any) -> str:
    return _json_handler(get_task, thread_id=args.get("thread_id", ""))


def _handle_send_message(args: dict[str, Any], **_: Any) -> str:
    return _json_handler(
        send_message,
        thread_id=args.get("thread_id", ""),
        message=args.get("message", ""),
    )


def register(ctx) -> None:
    for name, schema, handler, emoji in (
        ("t3_list_projects", T3_LIST_PROJECTS_SCHEMA, _handle_list_projects, "📁"),
        ("t3_start_task", T3_START_TASK_SCHEMA, _handle_start_task, "🚀"),
        ("t3_get_task", T3_GET_TASK_SCHEMA, _handle_get_task, "🔎"),
        ("t3_send_message", T3_SEND_MESSAGE_SCHEMA, _handle_send_message, "↩️"),
    ):
        ctx.register_tool(
            name=name,
            toolset="t3_code",
            schema=schema,
            handler=handler,
            emoji=emoji,
        )
