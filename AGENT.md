# Agent Brief

This file is the original build brief for the project. It is kept for historical
context, but it is no longer the best source of truth for the current system.

For the current project state, start with:

- `README.md`
- `docs/INDEX.md`
- `docs/OVERVIEW.md`
- `docs/HARDWARE.md`
- `docs/SOFTWARE.md`

Build a Raspberry Pi 3B+ web control app for a Snap Circuits Rover using a relay board and a USB camera.

## Deliverable
A small deployable project that:
- exposes browser controls for forward, reverse, left, right, and stop
- streams the USB camera view in the browser
- starts in a safe stopped state
- cleans up safely on shutdown
- can run as a service on the Pi

## Historical Hardware Mapping

### Pi -> relay
Use BCM numbering in code.

- physical pin 11 -> BCM 17 -> IN1
- physical pin 13 -> BCM 27 -> IN2
- physical pin 15 -> BCM 22 -> IN3
- physical pin 16 -> BCM 23 -> IN4

Power:
- Pi pin 2 -> relay VCC
- Pi pin 6 -> relay GND

### Relay -> rover
For each relay channel:
- COM -> rover control pin
- NO -> Orange
- NC -> Gray

Channels:
- CH1 -> Green
- CH2 -> Blue
- CH3 -> Yellow
- CH4 -> White

## Rover motion model
Relays are active low:
- GPIO LOW energizes relay and connects COM to NO -> Orange
- GPIO HIGH de-energizes relay and connects COM to NC -> Gray

The final deployed rover required a corrected software action mapping after
bring-up testing because the effective relay channel order on the hardware did
not match the initial assumption.

Action states in the deployed app:
- forward: IN1 LOW, IN2 HIGH, IN3 HIGH, IN4 LOW
- reverse: IN1 HIGH, IN2 LOW, IN3 LOW, IN4 HIGH
- left:    IN1 LOW, IN2 HIGH, IN3 LOW, IN4 HIGH
- right:   IN1 HIGH, IN2 LOW, IN3 HIGH, IN4 LOW
- stop:    IN1 HIGH, IN2 HIGH, IN3 HIGH, IN4 HIGH

## Expectations
- choose an appropriate Python web stack
- add a simple browser UI
- add a camera stream endpoint suitable for a browser
- add a single-frame snapshot endpoint suitable for automation
- keep implementation compact and understandable
- include README and service/unit setup notes
- avoid unnecessary framework sprawl

## Safety
- initialize movement outputs to stop immediately at startup
- return to stop on shutdown and exceptions
- serialize movement changes so commands do not conflict
- do not change the wiring assumptions above without documenting why

## Current Note

The deployed project currently uses a 4-channel relay mapping in code and wiring
documentation. The earlier 8-channel mention in older planning notes did not
become the deployed design.
