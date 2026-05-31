# Homelab Architecture Notes

## Initial Topology

The starting assumption is Ubuntu Server 26.04 hosts with three K3s server nodes using embedded etcd.

If four machines are available, do not make all four etcd/control-plane members. Use three K3s servers and one agent. An even-sized etcd cluster adds failure modes without improving quorum for this homelab shape.

| Host | Role | Notes |
| --- | --- | --- |
| `lab-node-1` | K3s server and worker | MAC `58:47:ca:7b:8a:5d`; pending IP/current hostname confirmation. |
| `lab-node-2` | K3s server and worker | MAC `e8:ff:1e:d4:26:8b`; pending IP/current hostname confirmation. |
| `lab-node-3` | K3s server and worker | MAC `1c:69:7a:c7:6f:f3`; pending IP/current hostname confirmation. |
| `lab-node-4` | K3s agent | MAC `84:47:09:2f:48:9a`; pending IP/current hostname confirmation. |

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
