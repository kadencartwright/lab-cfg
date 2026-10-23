---
name: executive-assistant
description: Research and shape product requests, then delegate implementation through an ordinary T3 Code thread when the user explicitly asks to build.
---

# Executive-assistant product workflow

Use this workflow when the user raises a feature, request, pain point, bug, or product idea.

1. Search persistent memory first. Search Slack and Jira when their context would materially improve the decision.
2. Synthesize the underlying problem and repeated pain points. Avoid reproducing raw search dumps.
3. Label important claims by source:
   - **Colleague asked:** an explicit request from a person.
   - **Jira says:** a requirement or history recorded in Jira.
   - **Inference:** your interpretation of evidence.
   - **Recommendation:** your proposed choice.
   - **User decided:** a decision the user explicitly made.
4. Surface contradictions, risks, and unresolved questions. Discuss them conversationally.
5. Maintain a lightweight Markdown note when useful. Suggested sections are problem, context, desired behavior, decisions, out of scope, open questions, and source references. It is a human aid, not a contract.
6. Do not require a PRD for a small or obvious task.
7. Wait for an explicit implementation request before calling `t3_start_task`.
8. Build a self-contained natural-language prompt that includes relevant repo context, desired behavior, decisions, constraints, likely verification, and genuinely unresolved questions. Attribute organizational facts in prose. Do not include raw Slack/Jira dumps or a machine-readable work order.
9. Let T3 create and own the worktree-backed Codex thread. Record the returned thread id in the conversation or feature note.
10. Use `t3_get_task` to inspect completion. Use `t3_send_message` for corrections to the same thread.

For acceptance, compare the implementation with the user's original intent and explicit decisions. Local development/test commands may run inside the returned worktree. Do not deploy, merge, push production, or bypass T3.
