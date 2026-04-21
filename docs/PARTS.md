# Parts List

This is the practical bill of materials for the project as currently understood.
It is not a purchasing BOM with exact vendor SKUs for every item, but it is
intended to be enough to reconstruct the system design.

## Core Rover Stack

- Snap Circuits Rover base
- Raspberry Pi 3B+
- microSD card for the Pi OS / Debian-based install
- Pi power supply
- 4-channel relay board
- USB webcam

## Networking

- onboard Pi WiFi (`wlan0`) used as AP in the final field setup
- USB WiFi adapter (`wlan1`) used as upstream client in the final field setup
  - current working upstream chipset class: MT7601U
- Ethernet cable for recovery via `eth0` (recommended to keep available)

## Wiring / Connectors

- jumper wires from Pi GPIO to relay board
- power leads from Pi to relay board (`VCC` / `GND`)
- relay screw-terminal connections to rover leads

## Rover Lead Colors Used By The Project

- Orange
- Gray
- Green
- Blue
- Yellow
- White

## Operator / Development Devices

- laptop or workstation for host-side tooling
- phone or Steam Deck for browser-based driving
- optional attached display for Pi console experiments

## Software/Runtime Components To Remember

These are not hardware parts, but they matter enough operationally to call out
in the same recovery-oriented reference:

- Flask runtime service
- OpenCV camera access
- NetworkManager-managed dual-radio networking
- SQLite landmark knowledge base
- optional host-side depth tooling

## Notes

- Earlier notes mentioned an 8-channel relay board, but the current deployed
  system and code use four active relay channels.
- The exact USB WiFi adapter matters. One tested adapter could join upstream
  WiFi but could not actually host AP mode in practice.
