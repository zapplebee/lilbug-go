# Networking

Lilbug is configured as a dual-radio node.

## Final Interface Roles

- `wlan0`: rover access point
- `wlan1`: upstream/home-network client
- `eth0`: untouched recovery path

## Rover AP

- SSID: `lilbug-rover`
- password: `lilbug123`
- Pi address on AP: `192.168.4.1`

Preferred field URL:

```text
http://192.168.4.1:8000
```

Implementation note:

- the final working AP uses NetworkManager shared mode on `wlan0`
- `hostapd`/`dnsmasq` were tested during development but are not the active
  runtime path in the final stable configuration

## Upstream Network

`wlan1` connects to the home network and receives a DHCP address there. That
address may change and should not be treated as the primary field-control URL.

## Why This Layout

The USB adapter that was tested could join the upstream network reliably, but it
did not work as an AP host in practice. The final stable design is therefore:

- onboard radio hosts the rover AP
- USB radio provides upstream connectivity

## Recovery Strategy

Safety protections were installed before changing interface roles:

- `/usr/local/bin/network-rollback.sh`
- `/usr/local/bin/network-failsafe.sh`
- `network-failsafe.service`

Additional deployment helper files remain in `deploy/` as historical artifacts of
the bring-up and rollback work.

Backups were also created under `/var/backups/lilbug-network/`.

`eth0` remains untouched as a physical recovery option.

## Operator Notes

- When connected to `lilbug-rover`, use `192.168.4.1` directly.
- Do not rely on `lilbug:8000` in the field.
- The hostname may resolve to the upstream-side address instead of the AP-side
  address, especially once the upstream network is out of range.

## Current Runtime Expectation

After reboot, the intended steady state is:

- `wlan0` active as `lilbug-rover`
- `wlan1` active on the upstream WiFi
- default route via `wlan1`
- rover web service listening on all interfaces
