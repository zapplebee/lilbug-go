# Software Architecture

## Overview

The software is intentionally split into:

- a small Pi runtime service
- optional host-side research and exploration tools

The Pi runtime should remain dependable, easy to restart, and easy to reason
about. The host-side scripts are where heavier experimentation belongs.

## Pi Runtime

Main entrypoint:

- `src/main.py`

Key responsibilities:

- initialize GPIO safely
- map actions to relay states
- serve the browser UI
- expose HTTP control and status endpoints
- stream MJPEG camera frames
- provide single-frame snapshots
- return to `stop` on shutdown

### Main Components

#### `RoverController`

- owns the GPIO interface
- serializes action changes behind a lock
- applies named actions from `STATE_BY_ACTION`
- ensures startup and cleanup go through `stop`

#### `CameraStream`

- opens the USB camera lazily through OpenCV
- serves MJPEG frame chunks for `/stream.mjpg`
- serves single JPEG snapshots for `/snapshot.jpg`
- releases the camera on shutdown/errors

#### Flask routes

- `/`
- `/api/status`
- `/api/move/<action>`
- `/api/stop`
- `/stream.mjpg`
- `/snapshot.jpg`

## Browser Client

Template:

- `templates/index.html`

Responsibilities:

- render camera stream and controls
- send direct directional commands to the API
- support keyboard input
- support gamepad input
- provide fullscreen camera viewing

Current client control model:

- hold a direction to move
- release to stop
- d-pad and left stick map directly to the four directions

This is the current stable UX after more complex mixed-control experiments were
backed out.

## Host-Side Tooling

### `scripts/loop_between_tags.py`

- room-specific closed-loop AprilTag lap script
- built from empirical exploration results
- still experimental outside the validated route

### `scripts/find_april_tag.py`

- host-side tag search utility
- uses AprilTag detection and the landmark KB
- optional depth-estimation hook for cautious experimentation

### `scripts/landmark_kb.py`

- lightweight SQLite-backed project memory for tags, handoffs, and observations

## Dependencies

### Runtime Dependencies

File:

- `requirements.txt`

Current runtime stack:

- Flask
- OpenCV headless
- `pupil-apriltags`
- `requests`

Note: `pupil-apriltags` and `requests` are primarily needed for host-side tools,
but are currently documented in the shared Python environment for convenience.

### Optional Vision Dependencies

File:

- `requirements-vision.txt`

These are host-side only and intended for experimentation with monocular depth
and other heavier perception layers.

## Services

### Rover Web Service

- systemd unit: `deploy/rover.service`
- deployed name on the Pi: `lilbug-rover.service`

This service runs the Flask app and is the core deployed application.

### Networking Safety Assets

Deploy helpers exist for network rollback/failsafe work and are documented in
`NETWORKING.md`. They are operational scaffolding, not part of the rover web app
itself.
