# Borg Backups

The lab cluster backs up K3s recovery material to BorgBase.

## Repository

```text
ssh://w2z0usc7@w2z0usc7.repo.borgbase.com/./repo
```

The repository uses Borg `repokey-blake2` encryption. Recovery requires both
the Borg passphrase and a copy of the exported repository key. Store both
outside this repository.

## Local Secret Inputs

The Ansible role reads ignored local files from `.secrets/`:

```text
.secrets/borgbase_lab_ed25519
.secrets/borgbase_passphrase
```

The deployed key should normally be append-only in BorgBase. Keep a separate
admin key with full access for manual maintenance such as prune, compact, and
repair.

## Apply Client Configuration

```bash
make borg-backup
```

This installs Borg on each K3s host, deploys root-only credentials under
`/etc/borg`, installs `/usr/local/sbin/borg-k3s-etcd-backup`, and enables the
`borg-k3s-etcd-backup.timer` systemd timer.

The Borg playbook intentionally disables Ansible's `group_vars` loader so it can
run without decrypting the K3s Ansible Vault file.

## Schedule

The timer runs every six hours, offset from the K3s etcd snapshot schedule, with
a randomized delay. Borg create also waits for repository locks so multiple
nodes can safely share one repository.

## Backed Up Paths

The role currently backs up these paths when they exist:

```text
/var/lib/rancher/k3s/server/db/snapshots
/etc/rancher/k3s
/var/lib/rancher/k3s/server/token
/var/lib/rancher/k3s/server/node-token
```

This is enough for initial cluster-control-plane recovery drills. It does not
back up arbitrary application volumes.

## Manual Verification

Run a backup on one host:

```bash
ANSIBLE_VARS_ENABLED= ansible lab-um890 -i inventories/lab/hosts.yml -u lab -b \
  -m shell -a 'systemctl reset-failed borg-k3s-etcd-backup.service && systemctl start borg-k3s-etcd-backup.service'
```

Check timers:

```bash
ANSIBLE_VARS_ENABLED= ansible k3s_cluster -i inventories/lab/hosts.yml -u lab -b \
  -m command -a 'systemctl list-timers borg-k3s-etcd-backup.timer --no-pager'
```

For the restore drill and destructive recovery runbook, see
`docs/k3s-restore-drill.md`.
