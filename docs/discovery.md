# Discovery Notes

Discovery run from workstation `z16` on `192.168.32.0/24`.

## Results

| Name | IP | Source | Reachability |
| --- | --- | --- | --- |
| `lab-um890` | `192.168.32.41` | UniFi dashboard screenshot, verified from `z16` | Ping ok, SSH open, K3s API closed before install. |
| `lab-bosgame` | `192.168.32.69` | UniFi dashboard screenshot, verified from `z16` | Ping ok, SSH open, K3s API closed before install. |
| `lab-beelink-mini-s` | `192.168.32.169` | UniFi dashboard screenshot, verified from `z16` | Ping ok, SSH open, K3s API closed before install. |

## Commands Used

```bash
nmap -sn 192.168.32.0/24
nmap -p 22,80,443,6443 --open 192.168.32.0/24
nmap -p 22,6443 --open 192.168.32.169 192.168.32.69 192.168.32.41
for i in $(seq 1 254); do dig +time=1 +tries=1 +short -x 10.10.24.$i @192.168.32.1; done
nmap -sn 10.10.24.0/24
nmap -p 22,80,443,6443 --open 10.10.24.0/24
nmap -Pn -p 22 --open 10.10.24.0/24
nmap -Pn -p 22,80,443,6443 --open --system-dns --dns-servers 192.168.32.1 10.10.24.0/24
tailscale status
```

Earlier stale UniFi data pointed at different MACs and a routed `10.10.24.0/24` network. The current dashboard screenshot identifies the active three-node lab on `192.168.32.0/24`, and those three nodes are reachable from workstation `z16`.
