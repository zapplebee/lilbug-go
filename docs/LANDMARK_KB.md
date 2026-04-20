# Landmark Knowledge Base

Lilbug does not need a heavyweight map system yet. The repo uses a lightweight
SQLite landmark knowledge base for room-specific navigation hints and observed
AprilTag metadata.

## Why SQLite

- one file
- easy to inspect manually
- easy to update from scripts
- enough for tags, search hints, handoffs, and observations

## Tables

### `landmarks`
- `tag_id`
- `label`
- `zone`
- `notes`
- `status`

### `handoffs`
- `from_tag`
- `to_tag`
- `reverse_ms`
- `search_direction`
- `blind_turn_ms`
- `confidence`
- `notes`

### `observations`
- `tag_id`
- `snapshot_path`
- tag pixel center/size/margin
- visible tag set
- optional depth warning flag
- freeform note

## Current Seed Data

- tag `0`: blue bin near fridge / doorway
- tag `1`: black bin under TV stand by fireplace
- tag `3`: low on the refrigerator front
- tag `4`: low on the tall wooden cabinet by the beaded-curtain doorway
- tag `5`: on the front base of the light sofa under the blinds
- tags `6` through `8`: placeholder entries marked unconfirmed until found

## Intended Use

- `scripts/find_april_tag.py` uses the KB to choose search directions from known
  landmarks and handoff hints.
- future exploration scripts should record observations and confirm landmark rows
  as new tags are found.
