---
name: using-vpn
description: Use when a task needs IVPN, a US or geo-specific IP, VPN-backed browser/API testing, or the workstation's opt-in VPN proxy.
---

# Using IVPN

- Use the installed `ivpn` CLI only to inspect state. Useful commands are `ivpn status`, `ivpn splittun -status_full`, and `ivpn firewall -status`.
- This workstation uses IVPN inverse split tunneling: ordinary applications stay on the normal connection and selected test traffic uses the VPN. Never switch to ordinary/exclusion mode.
- Do not launch individual commands with `ivpn splittun -appadd` or `ivpn exclude`. Adding and removing selected processes rewrites shared policy-routing rules and can interrupt Helium and Tailscale.
- A user service automatically maintains the persistent opt-in HTTP proxy at `http://127.0.0.1:18080` whenever IVPN is connected in inverse mode. Do not start, stop, or enroll the proxy manually. Configure only the application being tested; for Redact claws set `CLAWS_PROXY_SERVER=http://127.0.0.1:18080`, and for a diagnostic curl use `--proxy http://127.0.0.1:18080`.
- Before relying on a live result, verify the proxied egress differs from direct egress. The proxy must use IVPN while a normal unproxied request remains on the ISP connection. A failed proxy check blocks the VPN-dependent test; it never authorizes changing routes, DNS, firewall, Tailscale, or IVPN state.
- The CLI should already be logged in and connected. Preserve split-tunnel, firewall, DNS, connection, and autoconnect state. Never use `ivpn splittun -clean`, enable the IVPN firewall, or disconnect a connection you did not start for the current task.

