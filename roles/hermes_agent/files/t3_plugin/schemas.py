"""Model-visible schemas for the deliberately small T3 Code surface."""

T3_LIST_PROJECTS_SCHEMA = {
    "name": "t3_list_projects",
    "description": (
        "List projects visible in the normal T3 Code environment and show any "
        "Hermes aliases/base-branch mappings. This is read-only."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}
T3_START_TASK_SCHEMA = {
    "name": "t3_start_task",
    "description": (
        "Create a normal, UI-visible, worktree-backed T3 Code thread and send "
        "Codex its first natural-language turn. Call only after the user "
        "explicitly asks for implementation. T3, not Hermes, creates the worktree."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "project": {
                "type": "string",
                "description": "Hermes project alias, T3 project title, id, or workspace path.",
            },
            "prompt": {
                "type": "string",
                "description": "Self-contained natural-language implementation prompt for Codex.",
            },
            "base_branch": {
                "type": "string",
                "description": "Optional base branch override; otherwise use the hand-authored mapping.",
            },
            "title": {
                "type": "string",
                "description": "Optional human-readable T3 thread title.",
            },
        },
        "required": ["project", "prompt"],
        "additionalProperties": False,
    },
}

T3_GET_TASK_SCHEMA = {
    "name": "t3_get_task",
    "description": (
        "Read the current state and latest useful result from an ordinary T3 "
        "thread without polling processes or reading T3's database."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "thread_id": {"type": "string", "description": "T3 thread UUID."},
        },
        "required": ["thread_id"],
        "additionalProperties": False,
    },
}

T3_SEND_MESSAGE_SCHEMA = {
    "name": "t3_send_message",
    "description": (
        "Append a natural-language follow-up turn to the same ordinary T3/Codex "
        "thread. This is equivalent to the user sending a message in T3."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "thread_id": {"type": "string", "description": "Existing T3 thread UUID."},
            "message": {"type": "string", "description": "Natural-language follow-up for Codex."},
        },
        "required": ["thread_id", "message"],
        "additionalProperties": False,
    },
}
