# Discovery Notes

Discovery run from workstation `z16` on `192.168.32.0/24`.

## Results

| Name | IP | Source | Reachability |
| --- | --- | --- | --- |
| `lab-um890` | `10.10.24.45` | Gateway DNS at `192.168.32.1` | Did not answer ping or TCP 22/6443 from `192.168.32.38`. |

## Commands Used

```bash
nmap -sn 192.168.32.0/24
nmap -p 22,80,443,6443 --open 192.168.32.0/24
for i in $(seq 1 254); do dig +time=1 +tries=1 +short -x 10.10.24.$i @192.168.32.1; done
nmap -sn 10.10.24.0/24
nmap -p 22,80,443,6443 --open 10.10.24.0/24
tailscale status
```

`10.10.24.0/24` appears routed through `192.168.32.1`, but discovery probes from this workstation saw zero live hosts on that subnet. The missing lab nodes likely need to be read from router DHCP leases or scanned from a host on the `10.10.24.0/24` network itself.
