# Driving Lilbug For Agents

This guide is based on live experiments against the real rover in the current
room, not just the relay/API wiring. The experiments in this file were run from
this host with the human supervising the robot and a kill switch available.

## Robot Reality

Lilbug is a five-state latched-action robot:

- `forward`
- `reverse`
- `left`
- `right`
- `stop`

Important:

- there is no throttle
- there is no odometry
- there is no IMU
- there is no automatic timeout on move commands
- every move must be paired with `POST /api/stop`

The only trustworthy feedback is the camera.

## Base URL

```text
http://192.168.1.179:8000
```

## API

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/status` | GET | `{action, camera_stream, gpio_mode}` |
| `/api/move/<forward\|reverse\|left\|right>` | POST | Latch a movement state |
| `/api/stop` | POST | Latch stop |
| `/snapshot.jpg` | GET | Single JPEG frame |
| `/stream.mjpg` | GET | Live MJPEG |

Authentication: none.

## Current Deployed Motion Mapping

The running rover uses this remapped action table:

- `forward`: GPIO17 low, GPIO27 high, GPIO22 high, GPIO23 low
- `right`: GPIO17 high, GPIO27 low, GPIO22 high, GPIO23 low
- `reverse`: GPIO17 high, GPIO27 low, GPIO22 low, GPIO23 high
- `left`: GPIO17 low, GPIO27 high, GPIO22 low, GPIO23 high
- `stop`: all high

## Live Endpoint Timing

Measured against the live rover from this host:

- `GET /api/status`: about `30-39 ms`
- `POST /api/stop`: about `26-34 ms`
- `GET /snapshot.jpg`: about `88-116 ms`
- snapshot payload: about `144-145 KB`

These are command/vision overhead numbers, not motion calibration constants.

## What Is In The Room

Five `tag25h9` AprilTags are currently confirmed live.

### Tag 0

- AprilTag id `0`
- attached to a blue bin/cooler near the refrigerator and doorway
- often appears with the fridge on the left and a wood door with a toy hoop in
  the background

Representative view:

- fridge left
- blue bin with tag in the foreground
- doorway / hallway behind it

### Tag 1

- AprilTag id `1`
- attached to a black bin under the TV stand beside the stone fireplace
- often appears with the fireplace on the left and the TV stand dominating the
  center/right of frame

Representative view:

- stone fireplace left
- TV stand / TV centered
- black bin with tag below the TV stand

### Tag 3

- AprilTag id `3`
- attached low on the front of the stainless refrigerator
- usually appears in the same sector as tag `0`

### Tag 4

- AprilTag id `4`
- attached low on the tall wooden cabinet beside the beaded-curtain doorway
- marks the cabinet / side-passage sector beyond the cooler

### Tag 5

- AprilTag id `5`
- attached to the front base of the light-colored sofa beneath the blinds
- acts as a sofa-side anchor for room exploration

## What The Experiments Showed

### Short pulses do move the rover

The earlier claim that sub-`500 ms` pulses often do nothing is not reliable on
the current live rover.

Observed examples:

| Action | Requested pulse | Measured motor-on time | Result |
| --- | --- | --- | --- |
| `right` | `200 ms` | `258 ms` | modest visible scene change |
| `left` | `200 ms` | `272 ms` | large visible scene change |
| `reverse` | `180 ms` | `260 ms` | modest visible scene change |
| `forward` | `180 ms` | `273 ms` | small visible scene change |
| `forward` | `300 ms` | `374 ms` | small visible scene change |

The rover is responsive, but not symmetric. Equal-length pulses can produce very
different visible motion.

### Longer forward strides are usable when a tag is visible

Toward tag `1`, with the tag centered and the path visually clear:

- `1000 ms` forward increased tag side from about `28 px` to about `33 px`
- a second `1000 ms` forward increased it again to about `48 px`

So 1-second forward strides are usable for tag-directed approach in this room if
the target is visible and reasonably centered.

## Practical Driving Rules

1. Always stop explicitly after every move.
2. Always take a fresh snapshot before sending another forward command.
3. Prefer camera-closed-loop driving over dead-reckoning.
4. When a tag is visible and centered, longer forward strides are acceptable.
5. When no tag is visible, rotate in controlled search steps and re-observe.
6. If the scene changes less than expected, assume slip or camera swing and
   verify before escalating.

## Fast Lane

There is now a faster room-specific mode in `scripts/loop_between_tags.py`.

What changed:

- no redundant pre-stop before each pulse
- longer forward strides
- longer reverse handoff
- optional blind handoff turn based on the known room geometry

Best use:

- start the rover already near one of the two tags
- run with `--skip-acquire`
- let the fast loop handle the steady-state shuttling between tags

This is the right mode if you want the rover to look lively and zip between the
two known bins. It is less robust from a completely arbitrary starting pose than
the conservative closed-loop approach.

## Working Pulse Sizes In This Room

These values were validated live and are good starting defaults for this room.

- search turn: `350 ms`
- small recenter turn: `180 ms`
- back-away clearance: `700 ms`
- tag-directed forward stride: `1000 ms`
- post-turn settle: `0.8 s`
- post-forward settle: `1.2 s`

These are still not universal constants. They are room-specific and target-
specific enough to be useful, but agents should still close the loop with the
camera.

## Tag Handoff Geometry

The most useful room-specific finding is the handoff between the two tags.

### From Tag 1 To Tag 0

Validated behavior near tag `1`:

- reverse `700 ms`
- search `left` in `350 ms` pulses
- tag `0` was reacquired after about `4` left search pulses

### From Tag 0 To Tag 1

Validated behavior near tag `0`:

- reverse `700 ms`
- search `right` in `350 ms` pulses
- tag `1` was reacquired after about `4` right search pulses during the lap test

This is the core of the loop script.

## Repo Script Validation

The repo's `scripts/loop_between_tags.py` was validated live after these
experiments. A successful one-lap run completed:

- acquire tag `1`
- reverse `700 ms`
- search left to tag `0`
- approach tag `0` to about `50 px`
- reverse `700 ms`
- search right to tag `1`
- approach tag `1` to about `49 px`

The script still assumes the rover starts somewhere in the same room and that
the tags are not physically blocked. It is closed-loop and vision-based, not
blindly timed.

## Arrival Condition

The old loop script used an absurd tag-size threshold. The validated practical
arrival condition in this room is:

- declare arrival when tag side reaches about `45 px`

That is close enough to hand off to the other tag without needing to drive all
the way up to the bin.

## Recommended Closed-Loop Pattern

```text
1. snapshot
2. detect tag(s)
3. if target visible and centered enough:
   - forward 1000 ms
4. else if target visible but offset:
   - recenter turn 180 ms
5. else:
   - search turn 350 ms in known direction
6. stop
7. settle
8. snapshot again
```

## Bottom Line

For the current room:

- use `1000 ms` forward strides when a target tag is visible
- use `350 ms` turns to search
- use `180 ms` turns to recenter
- use `700 ms` reverse before handoff between tags
- handoff `tag 1 -> tag 0` by searching left
- handoff `tag 0 -> tag 1` by searching right

For a faster-looking shuttle in the current room, the repo script now also
supports a more aggressive steady-state mode built around:

- `900 ms` reverse handoff
- `1400 ms` blind handoff turn
- `1200 ms` long forward stride
- `1000 ms` near forward stride

Do not trust blind pulse-count navigation when the camera is available. The room
is navigable precisely because the tags are visible enough to keep the loop
closed.
