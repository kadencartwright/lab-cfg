# K3s Restore Drill

This document records the first non-destructive Borg restore drill and the
runbook for restoring the embedded-etcd K3s cluster from BorgBase.

## Drill Result

Date: 2026-06-06

Pretend-dead node: `lab-um890`

Borg archive restored locally:

```text
k3s-etcd-lab-um890-20260606T193412Z
```

Temporary restore directory:

```text
/tmp/lab-borg-restore-drill.CdLEF5Zx
```

Verified contents:

```text
etc/rancher/k3s/config.yaml
etc/rancher/k3s/k3s.yaml
var/lib/rancher/k3s/server/token
var/lib/rancher/k3s/server/db/snapshots/
```

The archive contained 18 etcd snapshots. The newest restored snapshot was:

```text
var/lib/rancher/k3s/server/db/snapshots/etcd-snapshot-lab-um890-1780768800
mtime: 2026-06-06 13:00:00 UTC
size: 5,599,264 bytes
```

The server token was present. `node-token` was not present in this archive, but
the server token is the critical recovery secret for decrypting confidential
data in K3s etcd snapshots.

## Source Semantics

K3s documents that the server token must be backed up with the datastore. The
token is used to encrypt confidential data in the datastore, so restoring with a
different token makes the snapshot unusable:

```text
https://docs.k3s.io/datastore/backup-restore
```

For multi-server embedded etcd restore, K3s documents this shape:

1. Stop K3s on all servers.
2. On one server, run `k3s server --cluster-reset` with
   `--cluster-reset-restore-path`.
3. Restart K3s on the restored server.
4. Delete `/var/lib/rancher/k3s/server/db/` on peer etcd servers.
5. Start K3s on peer servers so they rejoin the restored cluster.

Reference:

```text
https://docs.k3s.io/cli/etcd-snapshot
```

## Non-Destructive Local Drill

List available Borg archives:

```bash
BORG_RSH='ssh -i .secrets/borgbase_admin_ed25519 -o IdentitiesOnly=yes' \
BORG_PASSPHRASE="$(cat .secrets/borgbase_passphrase)" \
borg list --short ssh://w2z0usc7@w2z0usc7.repo.borgbase.com/./repo
```

Extract one archive to a temporary directory:

```bash
restore_dir="$(mktemp -d -t lab-borg-restore-drill.XXXXXXXX)"
cd "$restore_dir"

BORG_RSH='ssh -i /home/k/.codex/worktrees/9fb2/lab-cfg/.secrets/borgbase_admin_ed25519 -o IdentitiesOnly=yes' \
BORG_PASSPHRASE="$(cat /home/k/.codex/worktrees/9fb2/lab-cfg/.secrets/borgbase_passphrase)" \
borg extract \
  ssh://w2z0usc7@w2z0usc7.repo.borgbase.com/./repo::k3s-etcd-lab-um890-20260606T193412Z
```

Inspect restored material without printing token contents:

```bash
find var/lib/rancher/k3s/server/db/snapshots -maxdepth 1 -type f \
  -printf '%f\t%s bytes\t%TY-%Tm-%Td %TH:%TM:%TS\n' | sort

test -s var/lib/rancher/k3s/server/token && echo token-present
```

Clean up the temporary drill directory after inspection because it contains the
K3s server token:

```bash
cd /
rm -rf "$restore_dir"
```

## Real Multi-Server Restore Runbook

Use this only during an actual recovery window. These steps intentionally stop
the cluster and delete peer etcd databases.

Assumptions:

- Restore target: `lab-um890`
- Peer servers: `lab-bosgame`, `lab-beelink-mini-s`
- Restored Borg archive contains a valid server token and etcd snapshot.
- The replacement host has K3s installed at the intended version, or the K3s
  binary is available. K3s allows restoring with the same or a higher minor
  version than the version that created the snapshot.

On the restore target, extract the Borg archive:

```bash
sudo install -d -m 0700 /root/k3s-restore
cd /root/k3s-restore

sudo BORG_RSH='ssh -i /etc/borg/borgbase_lab_ed25519 -o IdentitiesOnly=yes -o UserKnownHostsFile=/etc/borg/known_hosts -o StrictHostKeyChecking=yes' \
  BORG_PASSCOMMAND='cat /etc/borg/passphrase' \
  borg extract \
  ssh://w2z0usc7@w2z0usc7.repo.borgbase.com/./repo::ARCHIVE_NAME \
  var/lib/rancher/k3s/server/token \
  var/lib/rancher/k3s/server/db/snapshots/SNAPSHOT_NAME
```

Set variables:

```bash
RESTORED_TOKEN="$(sudo cat /root/k3s-restore/var/lib/rancher/k3s/server/token)"
RESTORED_SNAPSHOT="/root/k3s-restore/var/lib/rancher/k3s/server/db/snapshots/SNAPSHOT_NAME"
```

Stop K3s on every server:

```bash
ansible server -i inventories/lab/hosts.yml -u lab -b \
  -m systemd -a 'name=k3s state=stopped'
```

On the restore target, run the K3s cluster reset restore:

```bash
sudo k3s server \
  --cluster-reset \
  --cluster-reset-restore-path="$RESTORED_SNAPSHOT" \
  --token="$RESTORED_TOKEN"
```

Wait for K3s to print:

```text
Managed etcd cluster membership has been reset, restart without --cluster-reset flag now.
```

Start K3s on the restored server:

```bash
sudo systemctl start k3s
```

On each peer server, move the old database out of the way instead of deleting it
immediately:

```bash
sudo mv /var/lib/rancher/k3s/server/db \
  "/var/lib/rancher/k3s/server/db.pre-restore.$(date -u +%Y%m%dT%H%M%SZ)"
```

Start K3s on each peer server:

```bash
ansible lab-bosgame,lab-beelink-mini-s -i inventories/lab/hosts.yml -u lab -b \
  -m systemd -a 'name=k3s state=started'
```

Validate the cluster:

```bash
kubectl get nodes -o wide
kubectl get pods -A
flux get all -A
```

If the restore target is a new physical host, remove any stale Kubernetes Node
objects that represent machines that will not return:

```bash
kubectl delete node OLD_NODE_NAME
```

## Open Follow-Up

The current Borg role backs up `/var/lib/rancher/k3s/server/node-token` when it
exists, but the first `lab-um890` archive did not contain that file. Keep the
server token in the backup set either way; it is the required restore secret.
