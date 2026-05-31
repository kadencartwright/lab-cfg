# Discovery Notes

Discovery run from workstation `z16` on `192.168.32.0/24`.

## Results

| Name | IP | Source | Reachability |
| --- | --- | --- | --- |
| stale dashboard label `lab-um890` | `10.10.24.45`, unconfirmed | Gateway DNS at `192.168.32.1`; screenshot MAC `58:47:ca:7b:8a:5d` | Did not answer ping or TCP 22/6443 from `192.168.32.38`. |
| stale dashboard label unknown | unknown | Screenshot MAC `e8:ff:1e:d4:26:8b` | No IP visible in screenshot. |
| stale dashboard label `devserver` | unknown | Screenshot MAC `1c:69:7a:c7:6f:f3`; Tailscale has offline peer `100.89.40.114` | No LAN DNS record found. |
| stale dashboard label `pve` | unknown | Screenshot MAC `84:47:09:2f:48:9a` | No LAN DNS record found. |

## Commands Used

```bash
nmap -sn 192.168.32.0/24
nmap -p 22,80,443,6443 --open 192.168.32.0/24
for i in $(seq 1 254); do dig +time=1 +tries=1 +short -x 10.10.24.$i @192.168.32.1; done
nmap -sn 10.10.24.0/24
nmap -p 22,80,443,6443 --open 10.10.24.0/24
nmap -Pn -p 22 --open 10.10.24.0/24
nmap -Pn -p 22,80,443,6443 --open --system-dns --dns-servers 192.168.32.1 10.10.24.0/24
tailscale status
```

`10.10.24.0/24` appears routed through `192.168.32.1`, but discovery probes from this workstation saw zero live hosts on that subnet. The missing lab nodes likely need to be read from router DHCP leases or scanned from a host on the `10.10.24.0/24` network itself.

The screenshot identifies four candidate machines, but its hostnames are stale. Treat MAC addresses as the source of truth until current hostnames/IPs are confirmed.

Current hostnames could not be recovered from these MAC addresses from workstation `z16`. The local ARP table does not contain the target MAC addresses, gateway DNS only exposes the stale `lab-um890` record, Pi-hole does not answer DNS on `192.168.32.66`, and forced `nmap -Pn` scans found no open SSH/HTTP/API ports on `10.10.24.0/24`.

For K3s embedded etcd, use three of the four as `server` nodes and one as an `agent`; do not run a four-member etcd cluster.
