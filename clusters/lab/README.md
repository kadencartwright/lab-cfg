# lab Flux Cluster

Flux watches this directory and reconciles the Kubernetes cluster from Git.

## Layout

- `flux-system/`: generated Flux installation and sync configuration.
- `infrastructure/`: cluster add-ons such as operators, storage, ingress, monitoring, and policy.
- `apps/`: application workloads.

## Secrets

SOPS-encrypted Kubernetes secrets use the age public key configured in `.sops.yaml`.

The matching private key is stored locally at `.secrets/age.key` and must also exist in the cluster as the `flux-system/sops-age` Secret for Flux to decrypt committed secrets.
