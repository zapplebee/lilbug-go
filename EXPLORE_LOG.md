# Explore Log

## 2026-04-19

### Confirmed tags before manual exploration

- tag `0`: blue bin near fridge / doorway
- tag `1`: black bin under TV stand by fireplace
- tag `5`: attached to the front base of the light-colored sofa beneath the window blinds
- tag `3`: attached low on the front of the stainless refrigerator, left of tag `0`

### Notes from supervised exploration so far

- A full rotational scan from a living-room pose saw tags `0`, `1`, and `5`.
- Tag `5` appears low on the sofa base and is small at long range, usually around
  `18-24 px` side when first acquired.
- The current `find_april_tag.py` prototype can keep reacquiring tag `5`, but it
  is still too jittery in the approach phase to count as good automation yet.
- The room remains asymmetric enough that room-specific handoff notes matter.

### Next exploration goals

- find tags `3`, `4`, `6`, `7`, and `8`
- identify what objects they are attached to
- note likely handoff directions between known landmarks
- collect enough observations to improve `find_april_tag.py`

### Additional supervised exploration notes

- Rotating left from the sofa-side lane exposed tag `3` on the refrigerator.
- Tag `3` is visible in the same sector as tag `0`, suggesting the kitchen side
  now contains a landmark cluster rather than a single target.
- The leather-sofa / half-wall side did not show additional tags in the first
  manual sweep.
- A second exploratory sweep from the lane pose confirmed tag `3` and also saw
  tag `0`, tag `1`, and tag `5` from the same general open-floor region.
- Tag `5` lives on the light sofa base below the window blinds.
- The rover eventually drifted into the kitchen-stool area and became effectively
  stuck: repeated turn scans and a 1-second reverse produced almost no visual
  change, indicating slip or a physical wedge rather than useful exploration.
- Afterward, a disconnected cord was found and reconnected. That likely explains
  part of the earlier inconsistent motion and should make later exploration more
  trustworthy than the pre-fix movement runs.
- A fresh post-fix open-floor scan also exposed tag `4` on the lower front of
  the tall wooden cabinet beside the beaded-curtain doorway.

### Confirmed tag locations after manual exploration

- tag `0`: blue bin near fridge / doorway
- tag `1`: black bin under TV stand by fireplace
- tag `3`: low on the refrigerator front
- tag `4`: low on the tall wooden cabinet beside the beaded-curtain doorway
- tag `5`: sofa base below window blinds

### Tags still not located

- tag `6`
- tag `7`
- tag `8`
