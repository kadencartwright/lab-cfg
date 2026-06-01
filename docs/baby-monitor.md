# Baby Monitor

The baby monitor app is deployed by Flux from:

```text
clusters/lab/apps/baby-monitor
```

The container image is:

```text
ghcr.io/kadencartwright/baby-monitor:lab
```

Because the GHCR package is private, the app needs a SOPS-encrypted image pull secret:

```bash
make ghcr-pull-secret
```

The runtime config is also SOPS-encrypted:

```bash
make baby-monitor-secret
```

By default, `make baby-monitor-secret` imports the existing Kubernetes Secret from the
local baby-monitor checkout:

```text
../baby-monitor/deploy/kubernetes/secret.local.yaml
```

To import a different Secret manifest:

```bash
BABY_MONITOR_SECRET_SOURCE=/path/to/secret.local.yaml make baby-monitor-secret
```

To intentionally replace an existing encrypted secret after changing camera config:

```bash
OVERWRITE=1 make baby-monitor-secret
```

If no existing Secret manifest is found, the helper falls back to prompting for an
access token and an optional camera JSON file. In that fallback mode, it writes a
local copy of the generated access token to:

```text
.secrets/baby-monitor-access-token
```

The service is exposed only through Tailscale:

```text
http://baby-monitor.bleak-banana.ts.net
```
