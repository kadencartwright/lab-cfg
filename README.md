# lab-cfg

Homelab infrastructure as code for a single-node Kubernetes cluster.

This repository manages my homelab from bare Ubuntu hosts through a working
K3s cluster, then uses GitOps to manage cluster add-ons and applications. It is
part real infrastructure, part public reference for how I approach small-scale
platform engineering: explicit bootstrap steps, pinned versions, encrypted
secrets, and repeatable operations.


## Current Architecture

```text
Ansible control node
        |
        | SSH
        v
Ubuntu 26.04 hosts
        |
        | k3s-ansible
        v
single-node K3s cluster
        |
        | Flux reconciles from Git
        v
cluster add-ons + apps
```

The cluster currently runs:

- K3s `v1.35.5+k3s1`
- One K3s server/control-plane node
- Flux CD
- SOPS/age decryption for GitOps-managed secrets
- Tailscale Kubernetes Operator
- A Tailscale-exposed `baby-monitor` application deployed from GHCR

Application services are intentionally exposed through Tailscale
`LoadBalancer` Services, not through LAN-facing MetalLB or public ingress.

## Repository Layout

```text
.
├── clusters/lab/                 # Flux root for the lab cluster
│   ├── apps/                     # Application workloads
│   ├── flux-system/              # Flux install and sync manifests
│   └── infrastructure/           # Cluster add-ons and operators
├── docs/                         # Architecture and operations notes
├── inventories/lab/              # Ansible inventory and group vars
├── playbooks/                    # Host prep, install, and upgrade entrypoints
├── roles/host_prep/              # Local Ansible role for host baseline setup
├── scripts/                      # Secret creation/import helpers
├── Makefile                      # Common operational commands
└── requirements.yml              # Ansible collection requirements
```

## Bootstrap Flow

The intended bootstrap path is:

1. Install Ubuntu Server on each node.
2. Configure SSH access for the `lab` user.
3. Run Ansible host preparation.
4. Install or upgrade K3s through `k3s-io/k3s-ansible`.
5. Bootstrap Flux into the cluster.
6. Let Flux reconcile `clusters/lab`.
7. Add applications and cluster add-ons through Git.

For a fresh control machine:

```bash
sudo apt-get update
sudo apt-get install -y ansible git make openssl
make collections
```

Basic checks:

```bash
make ping
make sudo-check
make check
```

Host prep and cluster install:

```bash
make prep
make site
```

K3s upgrades are deliberate and version-pinned:

```bash
make upgrade
```

Host utility installs:

```bash
make remote-agent-dev
```

## Secret Management

This repository is designed to be public.

Plaintext secrets are not committed. Local-only secret material lives under
`.secrets/`, which is ignored by Git. Kubernetes Secret manifests that need to
exist in Git are encrypted with SOPS using the age recipient in `.sops.yaml`.

Committed encrypted files include examples like:

- `inventories/lab/group_vars/k3s_cluster/vault.yml`
- `clusters/lab/infrastructure/tailscale-operator/operator-oauth.sops.yaml`
- `clusters/lab/apps/baby-monitor/config.sops.yaml`
- `clusters/lab/apps/baby-monitor/ghcr-pull.sops.yaml`

The private age key is intentionally not in this repository. Losing that key
means losing the ability to decrypt the committed SOPS files, so it needs to be
backed up separately.

Gitleaks is configured as a pre-commit hook to catch accidental plaintext
secret commits:

```bash
pre-commit install
make secrets-scan
```

## GitOps

Flux watches `clusters/lab` and reconciles it into the cluster.

The top-level cluster layout separates:

- `infrastructure`: operators and cluster-wide components
- `apps`: application workloads
- `flux-system`: Flux installation and sync configuration

This split keeps host bootstrap in Ansible and in-cluster state in Kubernetes
manifests.

## Networking Model

The cluster uses the normal LAN for node-to-node Kubernetes traffic.

User-facing private services are exposed through Tailscale. That keeps internal
apps reachable from my tailnet without publishing them on the LAN or internet.
MetalLB is intentionally not part of the current path because LAN exposure is
not a goal right now.

## Notable Design Choices

- **K3s over kubeadm/Kubespray**: less operational weight for a small homelab
  while still providing real Kubernetes primitives.
- **Single server node**: the cluster currently runs on `lab-bosgame` to keep
  the UM-890 Pro available for other workloads.
- **Pinned versions**: K3s is pinned exactly rather than tracking `latest`.
- **GitOps after bootstrap**: Ansible handles host state; Flux handles
  Kubernetes state.
- **Longhorn deferred**: distributed storage is useful, but backups and
  recovery come first.

## Operational Docs

- [Architecture notes](docs/architecture.md)
- [GitOps notes](docs/gitops.md)
- [Tailscale operator notes](docs/tailscale-operator.md)
- [Host Tailscale notes](docs/tailscale-hosts.md)
- [Baby monitor deployment notes](docs/baby-monitor.md)
- [Borg backup notes](docs/borg-backups.md)
- [K3s restore drill](docs/k3s-restore-drill.md)
- [Host discovery notes](docs/discovery.md)

## Current Roadmap
- Run a destructive K3s restore rehearsal during a maintenance window.
- Decide on persistent storage policy before adding Longhorn.
- Move image releases from mutable tags toward immutable tags or digests.
