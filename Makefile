ANSIBLE_PLAYBOOK ?= ansible-playbook
ANSIBLE_GALAXY ?= ansible-galaxy
INVENTORY ?= inventories/lab/hosts.yml
VAULT_PASSWORD_FILE ?= .secrets/ansible-vault-password
VAULT_ARGS := $(shell test -f $(VAULT_PASSWORD_FILE) && printf -- '--vault-password-file %s' '$(VAULT_PASSWORD_FILE)')

.PHONY: collections ping sudo-check check prep site upgrade secrets-scan tailscale-secret ghcr-pull-secret baby-monitor-secret

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

secrets-scan:
	pre-commit run gitleaks --all-files

tailscale-secret:
	scripts/create-tailscale-operator-secret

ghcr-pull-secret:
	scripts/create-ghcr-pull-secret

baby-monitor-secret:
	scripts/create-baby-monitor-secret
