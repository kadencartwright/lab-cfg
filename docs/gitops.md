# GitOps Notes

Flux runs inside the cluster and reconciles Kubernetes resources from `clusters/lab`.

SOPS encrypts Kubernetes Secret values before they are committed. The public age recipient is committed in `.sops.yaml`; the private age key is recovery-critical and must be stored outside Git.

## Local Tooling

This repo uses ignored local binaries under `.tools/bin` when system packages are not installed:

```bash
.tools/bin/flux
.tools/bin/sops
.tools/bin/age
.tools/bin/age-keygen
```

## Secret Workflow

Create a Secret manifest with a `.sops.yaml` suffix under `clusters/lab`, then encrypt it:

```bash
SOPS_AGE_KEY_FILE=.secrets/age.key .tools/bin/sops --encrypt --in-place clusters/lab/path/to/secret.sops.yaml
```

Decrypt locally when needed:

```bash
SOPS_AGE_KEY_FILE=.secrets/age.key .tools/bin/sops --decrypt clusters/lab/path/to/secret.sops.yaml
```

Flux can decrypt SOPS files after the cluster contains:

```text
namespace: flux-system
secret: sops-age
key: age.agekey
```
