# Overview

Lilbug is a Raspberry Pi-controlled rover built from a Snap Circuits Rover,
relay-based motor switching, and a USB camera. The Pi hosts a small Flask web
service that exposes camera feeds and motion controls. A separate set of
host-side utilities supports AprilTag-based exploration and navigation research.

## Project Goals

Primary goals:

- provide a simple, reliable browser-based driving interface
- expose a live camera stream and single-frame snapshots
- preserve safe startup and shutdown behavior on the Pi
- support field operation through the rover's own WiFi AP
- allow future autonomy research without making the Pi runtime complex

Secondary goals:

- support host-side AprilTag exploration and closed-loop experiments
- document the room and landmark knowledge as it evolves
- keep the system understandable and repairable without reverse-engineering code

## Core System Shape

There are two layers in this project:

1. Pi runtime
   - controls GPIO/relay outputs
   - streams camera frames
   - serves the web UI and JSON API
   - remains intentionally simple

2. Host-side tooling
   - exploration scripts
   - landmark database
   - optional depth estimation
   - calibration and autonomy experiments

This split is deliberate. The rover itself stays lightweight and dependable,
while the laptop or workstation can carry heavier perception and planning logic.

## Current Capabilities

- direct directional driving via browser UI
- keyboard and gamepad support in the browser
- MJPEG live camera stream
- JPEG snapshot endpoint
- AprilTag-assisted host-side exploration tooling
- two-radio network topology for field operation

## Current Limitations

- no throttle or PWM speed control
- no wheel encoders
- no IMU
- no onboard autonomy in the Pi service
- motion timing is surface- and obstacle-dependent
- not all placed AprilTags have been located yet

## Stable Field Use Model

When using Lilbug in the field:

- connect the client device to `lilbug-rover`
- open `http://192.168.4.1:8000`
- drive with direct directional input

That path should be treated as the canonical operating mode.
