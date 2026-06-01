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
