# Host Tailscale

Ansible manages host-level Tailscale on selected lab hosts. This is separate from
the Kubernetes Tailscale operator, which manages pod-level proxies and private
Ingress objects.

## Purpose

Host-level Tailscale lets remote clients reach selected hosts over the tailnet,
including the K3s API server on the active cluster node. The current
kube-apiserver serving certificate already includes the short node hostnames:

```text
lab-um890
lab-bosgame
lab-beelink-mini-s
```

Use a short MagicDNS hostname in kubeconfig, for example:

```text
https://lab-bosgame:6443
```

Using the short hostname matters because the serving certificate does not
include the full `*.ts.net` names or Tailscale IPs.

## Auth Key

The Ansible role reads a local ignored auth key from:

```text
.secrets/tailscale-host-authkey
```

Generate or rotate it from the existing SOPS-managed Tailscale OAuth client:

```bash
make tailscale-host-authkey
```

The generated key is preauthorized, reusable, non-ephemeral, and tagged
`tag:k8s`. It is only needed when authenticating a host that is not already on
the tailnet; existing nodes keep their Tailscale state locally.

## Apply

```bash
make tailscale-hosts
```

The role installs the official Tailscale apt repository, installs the
`tailscale` package, enables `tailscaled`, and authenticates only when the node
is not already running on the tailnet.

## Kubeconfig

Generate a local kubeconfig that points at the API server over MagicDNS:

```bash
make tailnet-kubeconfig
```

The generated file is ignored by Git:

```text
.secrets/kubeconfig-tailnet
```

Verify it with:

```bash
KUBECONFIG=.secrets/kubeconfig-tailnet kubectl get nodes
```
