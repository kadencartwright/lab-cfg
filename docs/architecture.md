# Homelab Architecture Notes

## Initial Topology

The starting assumption is three K3s server nodes with embedded etcd:

| Host | Role | Notes |
| --- | --- | --- |
| `um890` | K3s server and worker | Heavy workloads and fast storage. |
| `ryzen5600` | K3s server and worker | General workload capacity. |
| `n100` | K3s server and light worker | Control plane, small services, and replica capacity. |

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
