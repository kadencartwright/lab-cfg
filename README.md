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
make openai-codex-cli
make claude-code
make opencode
make chatgpt-desktop
make virtualization
make tts-pipeline
make riffgraph
```

The remote agent development role creates an `agent` user with passwordless
sudo, seeds its SSH authorized keys from the `lab` user, syncs new public keys
from `github.com/kadencartwright.keys` every five minutes, then installs Fast
Node Manager (FNM), Codex CLI, Tailscale, GitHub CLI, a password-protected Paseo
daemon. FNM manages the interactive Node
versions for `agent`, keeps Node 22 and Node 24 installed, defaults to Node 24,
and automatically follows `.node-version` and `.nvmrc` files. The system Node
installation remains the stable runtime for systemd services. Paseo listens on
the host's Tailscale address and runs as a systemd service under the `agent` account.

The focused OpenAI playbooks install the pinned Codex CLI standalone release
for the `agent` user and the native ChatGPT desktop app on `lab-um890`. The
desktop bootstrap package configures OpenAI's signed APT repository, and later
Ansible runs upgrade the `chatgpt` package from that repository.

`make claude-code` installs Claude Code for the existing `agent` user on
`remote_agent_dev_hosts` using the [official native installer](https://code.claude.com/docs/en/setup).
The launcher is `/home/agent/.local/bin/claude`; native installs update automatically.
Reruns skip installation when the launcher exists and verify `claude --version`.
Run `claude` as `agent` to complete interactive sign-in. To apply directly from
`lab-um890`, use `make claude-code ANSIBLE_PLAYBOOK='ansible-playbook --connection=local --limit lab-um890'`.

The virtualization role equips `lab-um890` with hardware-accelerated QEMU/KVM,
libvirt, UEFI and virtual TPM support, and Virtual Machine Manager. It enables
the default NAT network and grants the `agent` account access to the system
libvirt connection. A new login session is required before an already logged-in
shell sees the new `libvirt` and `kvm` group memberships.

The text-to-speech role configures `lab-um890` with a pinned Kokoro-ONNX CPU
environment under `/opt/patristic-tts`. Its `patristic-tts` command accepts a
text file or inline text, caches deterministic WAV chunks for resumable work,
and assembles a final narration without holding the complete work in memory.
The `patristic-tts-render` production wrapper retains master WAV files under
`masters/` and creates 48 kbps mono Opus delivery files under `delivery/`.
It uses the `bm_george` voice by default for the library's production queue.

The RiffGraph role configures `lab-um890` as a CPU-first music workbench with
MuScriptor, local musical analysis, MIDI export, and FluidSynth rendering.
Model authentication is copied from the controller at deploy time and is never
stored in Git. See [the RiffGraph runbook](docs/riffgraph.md).

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
- [Hermes Agent EA and T3 delegation](docs/hermes-agent.md)
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

### Update agent tools

`make agent-tools` applies the pinned Pi, Codex CLI, Hermes T3 CLI, and OpenCode v2
updates and upgrades native Claude Code to `remote_agent_dev_hosts`.
It expects the existing T3 system service.
The Hermes CLI and T3 server share the same version pin, with a systemd override
pointing the server at the installed CLI. Version changes restart T3 and check
its HTTP endpoint. OpenCode is pinned to native release 2.2.0 using the official
v2 installer, with `/usr/local/bin/opencode` pointing to the agent-owned binary.
The older snap remains installed, but the native command takes precedence.
`make opencode` applies only the OpenCode update and restarts T3 when it changes.

`playbooks/retire-agent-bridges.yml` removes the retired OpenBridge user services and Orca system
service, installed runtimes, configuration, and Orca status plugin. It preserves source checkouts and Android
emulator images.

To apply on the managed host itself, use `-c local --limit lab-um890` with the
playbook. Existing Codex processes keep their loaded version until restarted;
new processes use the updated binary.
