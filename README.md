# lab-cfg

Homelab infrastructure management code.

This repo starts with an Ansible control setup intended to run from a Raspberry Pi and bootstrap three Ubuntu Server 26.04 nodes into a K3s cluster.

## Current Shape

- Ansible host preparation role for Ubuntu/Debian-family nodes.
- Upstream `k3s-io/k3s-ansible` collection for K3s installation and upgrades.
- Three-node K3s server/control-plane inventory template using embedded etcd.
- Exact K3s version pin: `v1.35.5+k3s1`.
- ServiceLB disabled so MetalLB or kube-vip services can be added later through GitOps.
- Secrets referenced through Ansible Vault, not stored in plaintext.

## Pushback On The Prior Recommendation

- `v1.35.x` is not a real operational pin. This repo uses an exact version and expects deliberate upgrades.
- A Kubernetes API VIP cannot be treated as "GitOps later" if clients and joining nodes need it before Kubernetes exists. Start without a VIP, use an external load balancer, or bootstrap kube-vip as a static manifest before depending on it.
- Do not run the Ansible control Raspberry Pi from an unreliable SD card if it becomes your main operations box. Use SSD boot or keep the repo cloned somewhere else as well.
- Keep Longhorn out of the first pass. Get host prep, K3s, backups, and node labels stable first.
- A three-node etcd cluster is reasonable only if all three nodes have SSD-backed storage, wired networking, and stable power. You said to assume the weakest node has resilient disk, so the template uses all three as servers.

## Quickstart

Install dependencies on the Raspberry Pi control node:

```bash
sudo apt-get update
sudo apt-get install -y ansible git make openssl
make collections
```

Create the local vault file:

```bash
cp inventories/lab/group_vars/k3s_cluster/vault.yml.example inventories/lab/group_vars/k3s_cluster/vault.yml
openssl rand -base64 64
ansible-vault encrypt inventories/lab/group_vars/k3s_cluster/vault.yml
```

Edit:

- `inventories/lab/hosts.yml`
- `inventories/lab/group_vars/k3s_cluster/main.yml`
- `inventories/lab/group_vars/k3s_cluster/vault.yml`

Then run:

```bash
make ping
make sudo-check
make prep
make site
```

`make ping` checks SSH as the `lab` user. `make sudo-check` verifies passwordless sudo, which is required for unattended host prep and K3s installation. If passwordless sudo is not enabled, either add a sudoers rule for `lab` or run playbooks with become password prompting:

```bash
ANSIBLE_PLAYBOOK="ansible-playbook --ask-become-pass" make prep
ANSIBLE_PLAYBOOK="ansible-playbook --ask-become-pass" make site
```

If `make ping` reports host key verification failures, refresh the local SSH host keys before running Ansible:

```bash
ssh-keygen -R 192.168.32.41
ssh-keygen -R 192.168.32.69
ssh-keygen -R 192.168.32.169
ssh-keyscan -H 192.168.32.41 192.168.32.69 192.168.32.169 >> ~/.ssh/known_hosts
```

For upgrades, change `k3s_version` in `inventories/lab/group_vars/k3s_cluster/main.yml`, then run:

```bash
make upgrade
```

## Questions To Fill In

- Desired Kubernetes API endpoint: first server IP initially, kube-vip static manifest, or an external load balancer.
- MetalLB service IP range on your LAN.
- Tailscale auth method for hosts and Kubernetes operator.
- Backup target for etcd snapshots and future persistent volumes.
