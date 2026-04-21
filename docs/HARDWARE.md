# Hardware

## Main Components

The project currently depends on these physical components.

### Rover Platform

- Snap Circuits Rover base
- rover motor/control harness using color-coded leads:
  - Orange
  - Gray
  - Green
  - Blue
  - Yellow
  - White

### Compute and I/O

- Raspberry Pi 3B+
- microSD card with Debian/Raspberry Pi OS-compatible userland
- Pi power supply

### Switching and Control

- 4-channel relay board
  - only 4 channels are used by the current build
  - earlier notes may mention 8-channel boards, but the deployed system and code
    assume four active control channels

### Vision

- USB webcam
  - currently used through OpenCV as camera index `0`
  - deployed camera during bring-up: eMeet C960

### Networking

- onboard Pi WiFi (`wlan0`)
- USB WiFi adapter (`wlan1`)
  - current working upstream adapter: MT7601U-class adapter

### Optional / Operational Equipment

- Ethernet cable for recovery via `eth0`
- Steam Deck or other browser-capable client
- keyboard for local console work when needed

## Wiring Summary

Pi to relay:

- pin 2 -> relay VCC
- pin 6 -> relay GND
- pin 11 -> IN1
- pin 13 -> IN2
- pin 15 -> IN3
- pin 16 -> IN4

BCM mapping:

- IN1 -> GPIO17
- IN2 -> GPIO27
- IN3 -> GPIO22
- IN4 -> GPIO23

Relay to rover:

- COM -> rover control pin
- NO -> Orange
- NC -> Gray

Channel mapping:

- CH1 -> Green
- CH2 -> Blue
- CH3 -> Yellow
- CH4 -> White

See also:

- `WIRING_PI.md`
- `WIRING_ROVER.md`

## Electrical Behavior

The relay board is treated as active-low:

- GPIO LOW energizes the relay and connects COM to NO -> Orange
- GPIO HIGH de-energizes the relay and connects COM to NC -> Gray

This assumption is baked into the deployed motion table.

## Motion Mapping Reality

The physically wired system did not behave exactly like the first theoretical
mapping. After bring-up testing, the software action table was remapped to the
actual relay order that produced the intended rover behavior.

Current deployed directional states:

- `forward`: IN1 LOW, IN2 HIGH, IN3 HIGH, IN4 LOW
- `reverse`: IN1 HIGH, IN2 LOW, IN3 LOW, IN4 HIGH
- `left`: IN1 LOW, IN2 HIGH, IN3 LOW, IN4 HIGH
- `right`: IN1 HIGH, IN2 LOW, IN3 HIGH, IN4 LOW
- `stop`: IN1 HIGH, IN2 HIGH, IN3 HIGH, IN4 HIGH

Additional internal states exist in code for experimentation, but the stable UI
and documented operator path use only the direct four directions plus stop.

## Physical Environment Notes

Lilbug operates in a lived-in household environment with:

- rugs
- stools
- sofas
- TV stand/fireplace area
- cooler/bin obstacles
- doorway/beaded-curtain passage

This matters because field performance is not just a software problem. Cable
snags, rug drag, and wheel slip materially affect rover behavior.
