# Documentation Index

This directory is intended to be the durable project memory for Lilbug. The goal
 is that someone can return to the project years later and recover the hardware
 design, software architecture, deployment model, operating assumptions, and the
 major decisions that led to the current system.

Read these in order if you are starting cold:

1. `../README.md`
2. `OVERVIEW.md`
3. `PARTS.md`
4. `HARDWARE.md`
5. `SOFTWARE.md`
6. `NETWORKING.md`
7. `OPERATIONS.md`
8. `DECISIONS.md`

Reference material:

- `WIRING_PI.md`
- `WIRING_ROVER.md`
- `LANDMARK_KB.md`
- `../API_SPEC.md`
- `../DRIVING_FOR_AGENTS.md`
- `../EXPLORE_LOG.md`

Historical implementation brief:

- `../AGENT.md`

Notes:

- The rover service on the Pi is intentionally small and dumb.
- Heavier perception, mapping, and exploration tooling are host-side utilities.
- The documentation may mention experimental work; when in doubt, prefer the
  stable operator path documented in `README.md`, `NETWORKING.md`, and
  `OPERATIONS.md`.
