# Homelab Architecture Notes

## Current Topology

The cluster currently runs as a single-node K3s cluster on Ubuntu Server 26.04.

| Host | Role | Notes |
| --- | --- | --- |
| `lab-bosgame` | K3s server and worker | `192.168.32.69`, MAC `4c:50:dd:3d:8f:14`; general workload capacity. |

This keeps `lab-um890` free for non-cluster work and avoids placing the whole
cluster on the smaller Beelink Mini S.

## Retired Cluster Hosts

These machines were part of the original three-node embedded-etcd cluster but
are no longer in the active Ansible inventory:

| Host | Previous role | Notes |
| --- | --- | --- |
| `lab-um890` | K3s server and worker | `192.168.32.41`, MAC `3c:c5:dd:02:d5:a2`; strongest node. |
| `lab-beelink-mini-s` | K3s server and light worker | `192.168.32.169`, MAC `f4:3b:d8:71:47:92`; smallest node. |

`lab-um890` remains in the host-prep inventory, outside of the K3s cluster,
because it needs this host-specific kernel command-line override for stable
disk behavior:

```text
nvme_core.default_ps_max_latency_us=0
```

This disables NVMe APST on that host after prior read-only filesystem events
that looked like intermittent NVMe/controller hangs rather than media wear.

## Control Plane Endpoint

The inventory currently uses the first server as `api_endpoint`. With the
single-node inventory, that resolves to `lab-bosgame` at `192.168.32.69`.

For a highly available API endpoint, choose one of these before depending on the cluster for real workloads:

- External load balancer on the LAN.
- kube-vip as a K3s static manifest.
- A small HAProxy/Keepalived setup that does not conflict with K3s binding `:6443`.

The important constraint is boot order: Flux cannot create the first API endpoint because Flux itself needs the API server to exist.

## Cluster Add-Ons

Add these through GitOps after the base cluster works:

- Flux CD and SOPS/age.
- MetalLB L2 with a reserved LAN service range.
- cert-manager.
- Tailscale Kubernetes Operator.
- Longhorn only after backups and node labels are settled.
- kube-prometheus-stack before Loki/Alloy.

## Storage Policy

Use `local-path` for disposable data only.

Prefer an external NAS, NFS target, or S3-compatible target for backups. If Longhorn is added, keep replica count conservative and avoid using the smallest node for heavy replicated volumes unless its disk and network are genuinely reliable.
