# Homelab Architecture Notes

## Initial Topology

The starting assumption is Ubuntu Server 26.04 hosts with three K3s server nodes using embedded etcd.

| Host | Role | Notes |
| --- | --- | --- |
| `lab-um890` | K3s server and worker | `192.168.32.41`, MAC `3c:c5:dd:02:d5:a2`; strongest node. |
| `lab-bosgame` | K3s server and worker | `192.168.32.69`, MAC `4c:50:dd:3d:8f:14`; general workload capacity. |
| `lab-beelink-mini-s` | K3s server and light worker | `192.168.32.169`, MAC `f4:3b:d8:71:47:92`; keep heavier workloads elsewhere. |

This is intentionally simple: no separate agents until there is a reason to add them.

## Control Plane Endpoint

The inventory currently uses the first server as `api_endpoint`. That is the least magical bootstrap path.

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
