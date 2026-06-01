ANSIBLE_PLAYBOOK ?= ansible-playbook
ANSIBLE_GALAXY ?= ansible-galaxy
INVENTORY ?= inventories/lab/hosts.yml

.PHONY: collections ping sudo-check check prep site upgrade

collections:
	$(ANSIBLE_GALAXY) collection install -r requirements.yml -p .ansible/collections

ping:
	ansible k3s_cluster -i $(INVENTORY) -m ping -e ansible_become=false

sudo-check:
	ansible k3s_cluster -i $(INVENTORY) -m command -a 'sudo -n true' -e ansible_become=false

check:
	$(ANSIBLE_PLAYBOOK) -i $(INVENTORY) playbooks/site.yml --syntax-check

prep:
	$(ANSIBLE_PLAYBOOK) -i $(INVENTORY) playbooks/host-prep.yml

site:
	$(ANSIBLE_PLAYBOOK) -i $(INVENTORY) playbooks/site.yml

upgrade:
	$(ANSIBLE_PLAYBOOK) -i $(INVENTORY) playbooks/upgrade.yml
