# Object Storage

The lab uses RustFS for S3-compatible object storage.

## Topology

The initial deployment is standalone:

- one RustFS pod
- one `local-path` data PVC
- one `local-path` logs PVC
- no public ingress
- private Tailscale ingress for the S3 API

This is not high availability. The data PVC is node-local, so a node loss means
object storage is unavailable until the volume is recovered or recreated.

RustFS object data is intentionally not included in Borg backups yet. The
current BorgBase plan is the free `10Gi` tier, so Borg should stay focused on
control-plane and configuration recovery rather than object payloads.

## Endpoints

```text
https://rustfs.bleak-banana.ts.net
```

## Credentials

The local plaintext credential file is ignored by Git:

```text
.secrets/rustfs.env
```

The cluster receives the credentials through:

```text
clusters/lab/infrastructure/rustfs/credentials.sops.yaml
```

## Capacity

The first data PVC is `100Gi`; logs use `1Gi`. The current `local-path` storage
class does not advertise volume expansion, so increasing capacity later likely
means provisioning a new PVC and moving or restoring data.
