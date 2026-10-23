"""Small client for the authenticated HTTP/WebSocket contract in T3 Code 0.0.42.

T3 remains the sole state owner. The bridge neither reads SQLite nor creates Git
worktrees. Each invocation mints a short-lived T3 bearer session with T3's own
headless auth CLI and revokes it in a finally block, so no long-lived T3 secret
is stored in Hermes configuration.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import subprocess
from typing import Any, Iterator
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
import uuid

from websockets.sync.client import connect as websocket_connect


class T3BridgeError(RuntimeError):
    """A sanitized, model-readable bridge failure."""


def _home() -> Path:
    return Path.home()


def _t3_url() -> str:
    return os.getenv("HERMES_T3_URL", "http://127.0.0.1:3773").rstrip("/")


def _t3_home() -> Path:
    return Path(os.getenv("HERMES_T3_HOME", str(_home() / ".t3"))).expanduser()


def _t3_cli() -> Path:
    default = _home() / ".local/share/hermes-t3-bridge/node_modules/.bin/t3"
    return Path(os.getenv("HERMES_T3_CLI", str(default))).expanduser()


def _projects_path() -> Path:
    default = _home() / ".hermes/t3-projects.json"
    return Path(os.getenv("HERMES_T3_PROJECTS", str(default))).expanduser()


def _run_cli(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    cli = _t3_cli()
    if not cli.is_file():
        raise T3BridgeError(f"T3 CLI not found at {cli}")
    env = os.environ.copy()
    env["HOME"] = str(_home())
    env["T3CODE_HOME"] = str(_t3_home())
    try:
        return subprocess.run(
            [str(cli), *args],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise T3BridgeError("T3 auth CLI timed out") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "T3 CLI failed").strip()
        raise T3BridgeError(detail[-1200:]) from exc


@contextmanager
def _temporary_token() -> Iterator[str]:
    issued = _run_cli(
        [
            "auth",
            "session",
            "issue",
            "--base-dir",
            str(_t3_home()),
            "--ttl",
            "5m",
            "--label",
            "Hermes T3 bridge",
            "--subject",
            "hermes-t3-bridge",
            "--json",
        ]
    )
    try:
        payload = json.loads(issued.stdout)
        token = payload["token"]
        session_id = payload["sessionId"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise T3BridgeError("T3 returned an invalid auth-session response") from exc
    try:
        yield token
    finally:
        try:
            _run_cli(
                [
                    "auth",
                    "session",
                    "revoke",
                    "--base-dir",
                    str(_t3_home()),
                    session_id,
                ]
            )
        except Exception:
            # The token is short-lived even if revocation loses a race with shutdown.
            pass


def _request(token: str, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(
        f"{_t3_url()}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
            detail = parsed.get("message") or parsed.get("error") or raw
        except json.JSONDecodeError:
            detail = raw
        raise T3BridgeError(f"T3 HTTP {exc.code}: {str(detail)[:1200]}") from exc
    except URLError as exc:
        raise T3BridgeError(f"Cannot reach T3 at {_t3_url()}: {exc.reason}") from exc


def _ws_dispatch(token: str, command: dict[str, Any]) -> Any:
    """Dispatch through T3's Effect RPC WebSocket path.

    T3 0.0.32's HTTP dispatch endpoint accepts the command schema but does not
    run the WebSocket layer's bootstrap orchestration. Worktree-backed thread
    creation therefore must use the canonical ``orchestration.dispatchCommand``
    RPC, which is the same path the T3 UI uses.
    """
    ticket = _request(token, "POST", "/api/auth/websocket-ticket")
    try:
        ws_ticket = ticket["ticket"]
    except (KeyError, TypeError) as exc:
        raise T3BridgeError("T3 returned an invalid WebSocket ticket") from exc
    base = _t3_url()
    if base.startswith("https://"):
        ws_base = "wss://" + base.removeprefix("https://")
    elif base.startswith("http://"):
        ws_base = "ws://" + base.removeprefix("http://")
    else:
        raise T3BridgeError(f"Unsupported T3 URL scheme: {base}")
    request_id = str(uuid.uuid4())
    request = {
        "_tag": "Request",
        "id": request_id,
        "tag": "orchestration.dispatchCommand",
        "payload": command,
        "headers": [],
    }
    try:
        with websocket_connect(
            f"{ws_base}/ws?wsTicket={quote(str(ws_ticket), safe='')}",
            open_timeout=15,
            close_timeout=5,
            max_size=16 * 1024 * 1024,
        ) as socket:
            socket.send(json.dumps(request))
            while True:
                raw = socket.recv(timeout=60)
                response = json.loads(raw)
                if response.get("_tag") == "Ping":
                    socket.send(json.dumps({"_tag": "Pong"}))
                    continue
                if response.get("_tag") != "Exit" or response.get("requestId") != request_id:
                    continue
                exit_value = response.get("exit") or {}
                if exit_value.get("_tag") == "Success":
                    return exit_value.get("value")
                failure = exit_value.get("cause") or exit_value.get("error") or exit_value
                raise T3BridgeError(f"T3 RPC dispatch failed: {str(failure)[:1200]}")
    except T3BridgeError:
        raise
    except Exception as exc:
        raise T3BridgeError(f"T3 WebSocket dispatch failed: {exc}") from exc


def _load_mappings() -> dict[str, dict[str, Any]]:
    path = _projects_path()
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise T3BridgeError(f"Invalid project mapping at {path}: {exc}") from exc
    projects = payload.get("projects", {})
    if not isinstance(projects, dict):
        raise T3BridgeError(f"Project mapping at {path} must contain a projects object")
    return {str(key): value for key, value in projects.items() if isinstance(value, dict)}


def _resolve_project(
    requested: str, projects: list[dict[str, Any]], mappings: dict[str, dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, Any], str | None]:
    requested = requested.strip()
    mapping = mappings.get(requested, {})
    target = str(mapping.get("t3Project") or requested).strip()
    matches = [
        project
        for project in projects
        if target in {project.get("id"), project.get("title"), project.get("workspaceRoot")}
    ]
    if len(matches) != 1:
        known = ", ".join(sorted(str(p.get("title")) for p in projects))
        aliases = ", ".join(sorted(mappings)) or "none"
        if not matches:
            raise T3BridgeError(
                f"No T3 project matches {target!r}. Aliases: {aliases}. T3 projects: {known}"
            )
        raise T3BridgeError(f"T3 project selector {target!r} is ambiguous")
    alias = requested if requested in mappings else None
    return matches[0], mapping, alias


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _title_from_prompt(prompt: str) -> str:
    first = next((line.strip() for line in prompt.splitlines() if line.strip()), "Codex task")
    return first[:96]


def _thread_state(thread: dict[str, Any], shell_thread: dict[str, Any] | None = None) -> str:
    latest = thread.get("latestTurn") or {}
    session = thread.get("session") or {}
    if shell_thread and shell_thread.get("hasPendingUserInput"):
        return "waiting_for_input"
    if shell_thread and shell_thread.get("hasPendingApprovals"):
        return "waiting_for_approval"
    if latest.get("state") == "error" or session.get("status") == "error":
        return "failed"
    if latest.get("state") == "interrupted" or session.get("status") in {"interrupted", "stopped"}:
        return "stopped"
    if latest.get("state") == "running" or session.get("status") in {"starting", "running"}:
        return "codex_working"
    if latest.get("state") == "completed":
        return "turn_complete"
    return "queued_preparing" if thread.get("worktreePath") is None else "idle"


def _task_summary(
    thread: dict[str, Any], project: dict[str, Any] | None, shell_thread: dict[str, Any] | None = None
) -> dict[str, Any]:
    assistants = [m for m in thread.get("messages", []) if m.get("role") == "assistant"]
    latest_message = assistants[-1].get("text") if assistants else None
    if isinstance(latest_message, str) and len(latest_message) > 12000:
        latest_message = latest_message[-12000:]
    activities = thread.get("activities", [])
    latest_activity = activities[-1] if activities else None
    latest_turn = thread.get("latestTurn")
    session = thread.get("session") or {}
    return {
        "threadId": thread.get("id"),
        "project": None if project is None else project.get("title"),
        "projectId": thread.get("projectId"),
        "title": thread.get("title"),
        "state": _thread_state(thread, shell_thread),
        "branch": thread.get("branch"),
        "worktreePath": thread.get("worktreePath"),
        "latestTurn": latest_turn,
        "sessionStatus": session.get("status"),
        "lastError": session.get("lastError"),
        "latestAssistantMessage": latest_message,
        "latestActivity": latest_activity,
    }


def list_projects() -> dict[str, Any]:
    mappings = _load_mappings()
    with _temporary_token() as token:
        shell = _request(token, "GET", "/api/orchestration/shell")
    rows = []
    for project in shell.get("projects", []):
        aliases = [
            alias
            for alias, mapping in mappings.items()
            if str(mapping.get("t3Project") or alias)
            in {project.get("id"), project.get("title"), project.get("workspaceRoot")}
        ]
        rows.append(
            {
                "id": project.get("id"),
                "title": project.get("title"),
                "workspaceRoot": project.get("workspaceRoot"),
                "defaultModelSelection": project.get("defaultModelSelection"),
                "aliases": aliases,
                "mappedBaseBranches": {
                    alias: mappings[alias].get("baseBranch") for alias in aliases
                },
            }
        )
    return {"projects": rows}


def start_task(project_name: str, prompt: str, base_branch: str | None, title: str | None) -> dict[str, Any]:
    project_name = (project_name or "").strip()
    prompt = (prompt or "").strip()
    if not project_name or not prompt:
        raise T3BridgeError("project and prompt must be non-empty")
    mappings = _load_mappings()
    with _temporary_token() as token:
        shell = _request(token, "GET", "/api/orchestration/shell")
        project, mapping, alias = _resolve_project(project_name, shell.get("projects", []), mappings)
        selected_branch = (base_branch or mapping.get("baseBranch") or "").strip()
        if not selected_branch:
            raise T3BridgeError(
                f"No base branch mapped for {project_name!r}; pass base_branch or edit {_projects_path()}"
            )
        model_selection = project.get("defaultModelSelection") or mapping.get("modelSelection")
        if not isinstance(model_selection, dict) or not model_selection.get("instanceId"):
            raise T3BridgeError(
                f"T3 project {project.get('title')!r} has no default provider/model selection; "
                "set it in T3 or add modelSelection to the Hermes project mapping"
            )
        thread_id = str(uuid.uuid4())
        now = _now()
        resolved_title = (title or _title_from_prompt(prompt)).strip()[:120]
        command = {
            "type": "thread.turn.start",
            "commandId": str(uuid.uuid4()),
            "threadId": thread_id,
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "text": prompt,
                "attachments": [],
            },
            "modelSelection": model_selection,
            "titleSeed": resolved_title,
            "runtimeMode": "full-access",
            "interactionMode": "default",
            "bootstrap": {
                "createThread": {
                    "projectId": project["id"],
                    "title": resolved_title,
                    "modelSelection": model_selection,
                    "runtimeMode": "full-access",
                    "interactionMode": "default",
                    "branch": None,
                    "worktreePath": None,
                    "createdAt": now,
                },
                "prepareWorktree": {
                    "projectCwd": project["workspaceRoot"],
                    "baseBranch": selected_branch,
                    "branch": f"t3code/{secrets.token_hex(4)}",
                },
                "runSetupScript": True,
            },
            "createdAt": now,
        }
        dispatch = _ws_dispatch(token, command)
    return {
        "threadId": thread_id,
        "project": project.get("title"),
        "projectId": project.get("id"),
        "projectAlias": alias,
        "baseBranch": selected_branch,
        "requestedBranch": command["bootstrap"]["prepareWorktree"]["branch"],
        "state": "queued_preparing",
        "dispatch": dispatch,
    }


def get_task(thread_id: str) -> dict[str, Any]:
    thread_id = (thread_id or "").strip()
    try:
        uuid.UUID(thread_id)
    except (ValueError, AttributeError) as exc:
        raise T3BridgeError("thread_id must be a UUID") from exc
    with _temporary_token() as token:
        shell = _request(token, "GET", "/api/orchestration/shell")
        detail = _request(
            token, "GET", f"/api/orchestration/threads/{quote(thread_id, safe='')}"
        )
    thread = detail["thread"]
    project = next((p for p in shell.get("projects", []) if p.get("id") == thread.get("projectId")), None)
    shell_thread = next((t for t in shell.get("threads", []) if t.get("id") == thread_id), None)
    return _task_summary(thread, project, shell_thread)


def send_message(thread_id: str, message: str) -> dict[str, Any]:
    thread_id = (thread_id or "").strip()
    message = (message or "").strip()
    if not message:
        raise T3BridgeError("message must be non-empty")
    try:
        uuid.UUID(thread_id)
    except (ValueError, AttributeError) as exc:
        raise T3BridgeError("thread_id must be a UUID") from exc
    with _temporary_token() as token:
        detail = _request(
            token, "GET", f"/api/orchestration/threads/{quote(thread_id, safe='')}"
        )
        thread = detail["thread"]
        if (thread.get("latestTurn") or {}).get("state") == "running":
            raise T3BridgeError("The current T3 turn is still running; wait before sending a follow-up")
        command = {
            "type": "thread.turn.start",
            "commandId": str(uuid.uuid4()),
            "threadId": thread_id,
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "text": message,
                "attachments": [],
            },
            "modelSelection": thread.get("modelSelection"),
            "titleSeed": thread.get("title"),
            "runtimeMode": thread.get("runtimeMode", "full-access"),
            "interactionMode": thread.get("interactionMode", "default"),
            "createdAt": _now(),
        }
        dispatch = _ws_dispatch(token, command)
    return {"threadId": thread_id, "state": "codex_working", "dispatch": dispatch}
