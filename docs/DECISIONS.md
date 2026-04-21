# Design Decisions

This file explains major choices that shaped the project, especially where the
current system differs from earlier assumptions.

## 1. Keep The Pi Runtime Simple

Decision:

- the Pi should run a small web service, not a heavyweight autonomy stack

Why:

- easier to debug in the field
- fewer moving parts on the robot itself
- easier recovery after crashes or misconfiguration
- heavier perception can run on a more capable host

Result:

- Flask app on the Pi
- host-side exploration and perception tooling in scripts

## 2. Relay-Based Motor Control Instead Of PWM

Decision:

- use relay switching and discrete states

Why:

- matches the rover wiring constraints
- simple electrical model
- acceptable for a prototype rover

Consequence:

- no speed control
- motion is discrete and environment-sensitive

## 3. Trust Empirical Motion Mapping Over Theory

Decision:

- remap action states to what the real rover actually does

Why:

- the first theoretical mapping did not match the final effective relay order

Consequence:

- documentation must preserve the measured action table, not just the original
  wiring theory

## 4. Use Direct Directional Controls In The Browser

Decision:

- revert to simple direct directional control as the stable UI

Why:

- mixed throttle/steering experiments felt inconsistent
- one attempted mixed model caused sticky or confusing drive states
- direct input is easier to explain and operate on keyboard and gamepad

Consequence:

- current UI is intentionally simple
- more advanced mixing can be revisited later under a clearer spec

## 5. Prefer `192.168.4.1` Over Hostnames In The Field

Decision:

- use the AP-side IP directly for field driving

Why:

- `lilbug:8000` proved unreliable once the rover left upstream WiFi range
- hostname resolution can bind to the wrong interface identity

Consequence:

- field docs should point users to `http://192.168.4.1:8000`

## 6. Use Two Radios

Decision:

- split the AP and upstream roles across two WiFi interfaces

Final layout:

- `wlan0` = AP
- `wlan1` = upstream client

Why:

- the tested USB adapter could not host AP mode reliably in practice
- the onboard radio could

Consequence:

- onboard radio hosts the rover network
- USB radio carries internet/backhaul

## 7. Install Recovery Before Risky Networking Changes

Decision:

- install rollback/failsafe before changing interface roles

Why:

- the Pi is headless in normal operation
- accidental lockout would be expensive and disruptive

Consequence:

- rollback and boot failsafe are part of the deployment record

## 8. Use SQLite For Landmark Knowledge

Decision:

- use a lightweight SQLite database for room landmarks and observations

Why:

- simple
- inspectable
- durable enough for a small evolving map
- avoids a heavyweight mapping stack too early

Consequence:

- host-side scripts can accumulate project memory without complicating the rover
  service

## 9. Treat Exploration Notes As Field Notes, Not Always Stable Truth

Decision:

- separate durable system docs from environment-specific exploration notes

Why:

- room layout, obstacle placement, cable routing, and tag placements can change
- one exploratory session should not become misleading permanent truth

Consequence:

- `EXPLORE_LOG.md` remains a log
- higher-level docs should summarize confirmed, durable findings
