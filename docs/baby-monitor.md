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

`make baby-monitor-secret` writes a local copy of the generated access token to:

```text
.secrets/baby-monitor-access-token
```

The service is exposed only through Tailscale:

```text
http://baby-monitor.bleak-banana.ts.net
```
