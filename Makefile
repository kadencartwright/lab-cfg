ANSIBLE_PLAYBOOK ?= ansible-playbook
ANSIBLE_GALAXY ?= ansible-galaxy
INVENTORY ?= inventories/lab/hosts.yml
VAULT_PASSWORD_FILE ?= .secrets/ansible-vault-password
VAULT_ARGS := $(shell test -f $(VAULT_PASSWORD_FILE) && printf -- '--vault-password-file %s' '$(VAULT_PASSWORD_FILE)')
BORG_ANSIBLE_USER ?= lab
HOST_METRICS_ANSIBLE_USER ?= lab
TAILSCALE_ANSIBLE_USER ?= lab

.PHONY: collections ping sudo-check check prep site upgrade borg-backup systemd-exporter remote-agent-dev openai-codex-cli chatgpt-desktop hermes-agent virtualization tts-pipeline riffgraph tailscale-host-authkey tailscale-hosts tailnet-kubeconfig secrets-scan tailscale-secret ghcr-pull-secret baby-monitor-secret

collections:
	$(ANSIBLE_GALAXY) collection install -r requirements.yml -p .ansible/collections

ping:
	ansible k3s_cluster -i $(INVENTORY) -m ping -e ansible_become=false

sudo-check:
	ansible k3s_cluster -i $(INVENTORY) -m command -a 'sudo -n true' -e ansible_become=false

check:
	$(ANSIBLE_PLAYBOOK) $(VAULT_ARGS) -i $(INVENTORY) playbooks/site.yml --syntax-check

prep:
	$(ANSIBLE_PLAYBOOK) $(VAULT_ARGS) -i $(INVENTORY) playbooks/host-prep.yml

site:
	$(ANSIBLE_PLAYBOOK) $(VAULT_ARGS) -i $(INVENTORY) playbooks/site.yml

upgrade:
	$(ANSIBLE_PLAYBOOK) $(VAULT_ARGS) -i $(INVENTORY) playbooks/upgrade.yml

borg-backup:
	ANSIBLE_VARS_ENABLED= $(ANSIBLE_PLAYBOOK) -i $(INVENTORY) -u $(BORG_ANSIBLE_USER) playbooks/borg-backup.yml

systemd-exporter:
	ANSIBLE_VARS_ENABLED= $(ANSIBLE_PLAYBOOK) -i $(INVENTORY) -u $(HOST_METRICS_ANSIBLE_USER) playbooks/systemd-exporter.yml

remote-agent-dev:
	$(ANSIBLE_PLAYBOOK) $(VAULT_ARGS) -i $(INVENTORY) playbooks/remote-agent-dev.yml

openai-codex-cli:
	$(ANSIBLE_PLAYBOOK) -i $(INVENTORY) playbooks/openai-codex-cli.yml

.PHONY: claude-code
claude-code:
	$(ANSIBLE_PLAYBOOK) $(VAULT_ARGS) -i $(INVENTORY) playbooks/claude-code.yml

chatgpt-desktop:
	$(ANSIBLE_PLAYBOOK) -i $(INVENTORY) playbooks/chatgpt-desktop.yml

hermes-agent:
	$(ANSIBLE_PLAYBOOK) $(VAULT_ARGS) -i $(INVENTORY) playbooks/hermes-agent.yml

virtualization:
	$(ANSIBLE_PLAYBOOK) $(VAULT_ARGS) -i $(INVENTORY) playbooks/virtualization.yml

tts-pipeline:
	$(ANSIBLE_PLAYBOOK) $(VAULT_ARGS) -i $(INVENTORY) playbooks/tts-pipeline.yml

riffgraph:
	$(ANSIBLE_PLAYBOOK) $(VAULT_ARGS) -i $(INVENTORY) playbooks/riffgraph.yml

tailscale-host-authkey:
	scripts/create-tailscale-host-authkey

tailscale-hosts:
	ANSIBLE_VARS_ENABLED= $(ANSIBLE_PLAYBOOK) -i $(INVENTORY) -u $(TAILSCALE_ANSIBLE_USER) playbooks/tailscale-hosts.yml

tailnet-kubeconfig:
	scripts/create-tailnet-kubeconfig

secrets-scan:
	pre-commit run gitleaks --all-files

tailscale-secret:
	scripts/create-tailscale-operator-secret

ghcr-pull-secret:
	scripts/create-ghcr-pull-secret

baby-monitor-secret:
	scripts/create-baby-monitor-secret

.PHONY: agent-tools
agent-tools:
	$(ANSIBLE_PLAYBOOK) $(VAULT_ARGS) -i $(INVENTORY) playbooks/agent-tools.yml

.PHONY: opencode
opencode:
	$(ANSIBLE_PLAYBOOK) $(VAULT_ARGS) -i $(INVENTORY) playbooks/opencode.yml
