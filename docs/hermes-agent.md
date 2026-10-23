# Hermes Agent on lab-um890

Hermes Agent is the high-context EA/product layer on `lab-um890`. It can use
memory, web research, browser automation, and (after OAuth) read-oriented Slack
and Jira tools. A small native Hermes plugin delegates implementation into
ordinary T3 Code threads. T3 remains the owner of projects, Git worktrees,
Codex sessions, turns, checkpoints, and diffs; Codex receives only its normal
repository context and Hermes's natural-language prompt.

```text
Hermes context and product reasoning
                |
                | natural-language prompt
                v
       normal T3 thread/worktree <---- human uses the T3 UI
                |
                v
              Codex
                |
                +---- completion/follow-up in the same T3 thread
```

## Managed installation

Ansible installs the supported upstream Hermes checkout for the existing
`agent` user. The release and Git commit are pinned in
`roles/hermes_agent/defaults/main.yml`; the upstream installer is also pinned
by SHA-256. T3's bridge CLI is pinned to the version of the running server.

Important paths on `lab-um890`:

- Hermes checkout and virtual environment: `~agent/.hermes/hermes-agent`
- Hermes configuration: `~agent/.hermes/config.yaml`
- secrets (never overwritten by Ansible): `~agent/.hermes/.env`
- persistent memory: `~agent/.hermes/memories/`
- editable identity/instructions: `~agent/.hermes/SOUL.md`
- EA workflow skill: `~agent/.hermes/skills/executive-assistant/SKILL.md`
- native T3 plugin: `~agent/.hermes/plugins/t3_code/`
- T3 project aliases: `~agent/.hermes/t3-projects.json`
- harmless integration-test repository: `~agent/code/hermes-t3-smoke`

The managed sources for the identity, skill, plugin, config, and mappings live
in `roles/hermes_agent/`. Edit those files rather than their deployed copies.
Memory and `.env` are deliberately seeded only when absent so provisioning does
not erase learned state or credentials.

Provision or reconcile the host from this repository:

```bash
make hermes-agent
```

The gateway is the upstream systemd user service. Ansible enables lingering for
`agent`, so it starts at boot and survives logout. It does not add a public
listener; T3 is still bound to `127.0.0.1:3773`.

```bash
ssh agent@lab-um890
systemctl --user status hermes-gateway.service
systemctl --user restart hermes-gateway.service
systemctl --user stop hermes-gateway.service
systemctl --user start hermes-gateway.service
journalctl --user -u hermes-gateway.service -f
hermes doctor
hermes                         # interactive session
```

## One-time model authentication

The configured provider is `openai-codex` and the model is configurable through
the role defaults. No API key or OAuth token is stored in this repository.
Authenticate interactively as `agent`:

```bash
ssh -t agent@lab-um890 'hermes auth add openai-codex --no-browser'
```

Follow the printed device-login instructions, then validate a real inference:

```bash
ssh agent@lab-um890 "hermes -z 'Reply with exactly HERMES_READY.'"
```

This is separate from Codex CLI authentication. Hermes correctly refuses to
silently import an expired Codex access token.

## Slack and Jira foundation

Both official remote MCP servers are present but disabled until OAuth is
completed. Slack exposes only search/read/history/reply-context patterns. Jira
exposes only identity, resource discovery, search, issue reads, links, and
project discovery. Resources, prompts, sampling, elicitation, and mutating/admin
tools are disabled.

For Slack, create the OAuth app/client required by Slack's official MCP server,
then put only the secrets in `~agent/.hermes/.env`:

```dotenv
SLACK_MCP_CLIENT_ID=...
SLACK_MCP_CLIENT_SECRET=...
```

Set the corresponding Ansible variables for `lab-um890` and rerun provisioning:

```yaml
hermes_slack_mcp_enabled: true
hermes_jira_mcp_enabled: true
```

Then complete OAuth as `agent` and test each connection:

```bash
hermes mcp login slack
hermes mcp test slack
hermes mcp login jira
hermes mcp test jira
systemctl --user restart hermes-gateway.service
```

Keep tool filtering declarative in
`roles/hermes_agent/templates/config.yaml.j2`; direct edits to the deployed
`config.yaml` are replaced by Ansible. Do not put OAuth tokens in inventory or
normal role variables.

## T3 bridge

The model-visible interface is intentionally four tools:

- `t3_list_projects`
- `t3_start_task(project, prompt, base_branch?, title?)`
- `t3_get_task(thread_id)`
- `t3_send_message(thread_id, message)`

The plugin uses the exact T3 0.0.32 Effect RPC WebSocket dispatch path used by
the T3 UI and T3's HTTP read model. It asks T3 to bootstrap the thread and
worktree; it never runs `git worktree add`. Each call mints a five-minute T3
administrative session with T3's own CLI and revokes it in a `finally` block.
There is no task database or persistent bridge credential.

Add project aliases in `hermes_t3_projects` in the role defaults or host vars:

```yaml
hermes_t3_projects:
  my-app:
    t3Project: my-app
    baseBranch: dev
    modelSelection:
      instanceId: codex
      model: gpt-5.4
```

`t3Project` may match a T3 project id, title, or workspace root. The alias and
default branch are operational hints only; T3 remains the state owner. Rerun
`make hermes-agent` after changing the mapping.

Once model authentication is complete, a natural test is:

```bash
hermes -z 'List the T3 projects you can delegate to. Do not start a task.'
```

For a model-independent bridge check:

```bash
cd ~/.hermes
PYTHONPATH="$PWD" ~/.hermes/hermes-agent/venv/bin/python - <<'PY'
import json
from plugins.t3_code.client import list_projects
print(json.dumps(list_projects(), indent=2))
PY
```

Ask Hermes to start implementation explicitly (for example, “have Codex build
this in my-app”). The returned `threadId`, project, branch, and worktree identify
the ordinary task. Open the named project in T3 and find that thread normally;
Hermes and the human can both append turns to it.

The real provisioning validation created thread
`e7258d19-d6d0-4bed-93ae-085da284a691` in `hermes-t3-smoke`. T3 created its
worktree, Codex made the requested harmless file, and a second Hermes message
was processed in the same thread.

## Browser, web, and acceptance testing

Key-free DuckDuckGo search is enabled through Hermes's bundled `web-ddgs`
provider. The role also installs a narrow root-owned AppArmor exception for the
exact version-pinned agent-browser Chromium executable, preserving Chromium's
user-namespace sandbox without relaxing Ubuntu's system-wide restriction.

Manual browser smoke test:

```bash
ab=~/.hermes/hermes-agent/node_modules/.bin/agent-browser
"$ab" --session smoke open https://example.com
"$ab" --session smoke get title
"$ab" --session smoke snapshot -c
"$ab" --session smoke close
```

The EA instructions establish the acceptance loop and permit local test/dev
commands in T3 worktrees. V1 proves delegation, completion inspection, and a
same-thread correction. Generalized application startup, `readyUrl` mappings,
and autonomous browser verdict/retry loops are intentionally not yet built.

## Updating

To upgrade Hermes, update all pin-related values in the role defaults:

- `hermes_agent_version`
- `hermes_agent_commit`
- `hermes_agent_installer_sha256`
- `hermes_agent_playwright_chromium_path` if agent-browser Chromium changed

If T3 changes, inspect the locally running version's contracts first, then
update `hermes_t3_version` and the plugin together. Never guess the RPC payload
from an older release. Apply with `make hermes-agent`, run it a second time, and
expect the second recap to report `changed=0`.

The 0.0.42 pin was checked with a temporary local server: CLI startup, bridge
auth-session issue/revoke, HTTP project listing, and WebSocket project creation
passed. The turn-start and worktree-bootstrap payloads remain compatible with
the published 0.0.42 schema. A provider-backed Codex task was not run during
this version check. Upgrade the running T3 server to the same version before
applying the Hermes CLI pin.

## Troubleshooting and current limits

- `hermes doctor` reports provider auth until the one-time device login above.
- Slack and Jira remain unavailable until their explicit OAuth steps are done.
- `journalctl --user -u hermes-gateway.service -n 200` shows gateway failures.
- If browser launch reports “No usable sandbox,” confirm the executable in
  `hermes_agent_playwright_chromium_path`, rerun Ansible, and check the loaded
  profile with `sudo apparmor_status | grep hermes-playwright`.
- If T3 calls fail, confirm `curl http://127.0.0.1:3773` works locally, the T3
  server matches `hermes_t3_version` (currently 0.0.42), and `~agent/.t3` is owned
  by `agent`.
- Hermes doctor currently reports upstream npm audit findings in the pinned
  Hermes/agent-browser checkout. They were not rewritten with an unreviewed
  `npm audit fix`; address them through a reviewed upstream Hermes upgrade.
- V1 does not stop tasks, merge PRs, deploy, push production, or alter base
  branches. It adds no MCP configuration to Codex.
