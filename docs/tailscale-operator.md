# Tailscale Kubernetes Operator

The operator is installed by Flux from the stable Tailscale Helm chart repository.

## Prerequisites

Update the tailnet policy to include these tags:

```json
"tagOwners": {
  "tag:k8s-operator": [],
  "tag:k8s": ["tag:k8s-operator"]
}
```

If using `ProxyGroup`-backed ingress, add policy that lets `tag:k8s`
devices advertise Tailscale Services and lets tailnet users reach them:

```json
"autoApprovers": {
  "services": {
    "tag:k8s": ["tag:k8s"]
  }
},
"grants": [
  {
    "src": ["autogroup:member"],
    "dst": ["tag:k8s"],
    "ip": ["tcp:80", "tcp:443"]
  },
  {
    "src": ["autogroup:member"],
    "dst": ["tag:k8s:*"],
    "ip": ["icmp:*"]
  }
]
```

The `ProxyGroup` path is required when a Tailscale Ingress needs an HTTP
endpoint on port 80, for example to redirect plain HTTP to HTTPS.

Create a Tailscale OAuth client in the admin console with:

- `Devices Core` write scope
- `Auth Keys` write scope
- `Services` write scope
- tag: `tag:k8s-operator`

Tailscale documents these prerequisites in the Kubernetes operator setup guide:
https://tailscale.com/docs/features/kubernetes-operator

## Create The Encrypted OAuth Secret

Run:

```bash
make tailscale-secret
```

The script writes:

```text
clusters/lab/infrastructure/tailscale-operator/operator-oauth.sops.yaml
```

The plaintext OAuth secret is not written to Git.

## Enable Reconciliation

After the encrypted secret exists, enable the operator by adding `tailscale-operator` to:

```text
clusters/lab/infrastructure/kustomization.yaml
```
