# Operations

## Daily Use

### Field Driving

1. Power the rover and Pi.
2. Connect the client device to `lilbug-rover`.
3. Open `http://192.168.4.1:8000`.
4. Use the direct controls:
   - buttons
   - arrow keys
   - d-pad or left stick

### Camera Use

- live stream: `/stream.mjpg`
- snapshot: `/snapshot.jpg`
- fullscreen is available from the browser UI

## Service Management

### Status

```bash
sudo systemctl status lilbug-rover.service
```

### Restart

```bash
sudo systemctl restart lilbug-rover.service
```

### Logs

```bash
journalctl -u lilbug-rover.service -f
```

## Networking

Expected steady state:

- `wlan0` = `lilbug-rover`
- `wlan1` = upstream network

Field note:

- use `192.168.4.1` directly
- do not rely on `lilbug:8000` when the rover may leave upstream WiFi range

## Recovery

### Best Recovery Path

- `eth0` is intentionally left untouched

### Network Rollback Assets

- `/usr/local/bin/network-rollback.sh`
- `/usr/local/bin/network-failsafe.sh`
- `network-failsafe.service`

### Manual Recovery Pattern

If the Pi remains reachable over SSH but networking is in a bad state:

```bash
sudo /usr/local/bin/network-rollback.sh
```

### Worst Case

- connect Ethernet
- or recover by editing the SD card offline

## Known Operational Pitfalls

- cables can work loose and mimic control/software bugs
- rugs can trap or stall the rover
- stools and coolers create narrow mechanical traps
- browser hostname resolution can follow the wrong interface
- upstream DHCP addresses are not stable identifiers

## Exploration Workflow

For AprilTag exploration work:

1. start from open floor if possible
2. log what is physically visible
3. prefer snapshots and closed-loop motion
4. record discoveries in `EXPLORE_LOG.md`
5. update landmark knowledge after confirmation

## What Not To Assume

- that motion timing alone is reliable
- that the upstream network identity is the field identity
- that every tested control experiment remains the active operator UI
- that every placed AprilTag has already been found
