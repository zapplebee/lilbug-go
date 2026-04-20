"""Loop Lilbug between AprilTag id=0 and id=1.

This version is tuned from live experiments in the current room.

Room assumptions validated during testing:
  - tag25h9 id=0 is on the blue bin near the fridge / doorway
  - tag25h9 id=1 is on the black bin under the TV stand by the fireplace
  - from near tag1, a reverse then left search reacquires tag0
  - from near tag0, a reverse then right search reacquires tag1

Practical behavior:
  - arrival threshold is about 45 px tag side in the image
  - forward strides can be 1000 ms when a tag is visible and roughly centered
  - search turns are 350 ms and recenter turns are 180 ms

Run:
    python scripts/loop_between_tags.py --once
    python scripts/loop_between_tags.py --base http://192.168.1.179:8000
    python scripts/loop_between_tags.py --once --skip-acquire

Stop with Ctrl-C; the rover is always commanded to `stop` on exit.
"""
from __future__ import annotations

import argparse
import atexit
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import requests
from pupil_apriltags import Detector

# ---------- configuration ----------

DEFAULT_BASE = "http://192.168.1.179:8000"

TAG_FAMILY = "tag25h9"
TAG_SIZE_MM = 100.0
ASSUMED_HFOV_DEG = 60.0

# Approach geometry calibrated from live tests.
TARGET_SIDE_PX = 45
APPROACH_FWD_MS = 1000
APPROACH_NEAR_FWD_MS = 700
APPROACH_CORR_MS = 180
APPROACH_DEAD_PX = 60
APPROACH_RECENTER_PX = 90
APPROACH_MAX_STEPS = 10
APPROACH_SETTLE_S = 1.2

# Search geometry
SEARCH_PULSE_MS = 350
SEARCH_SETTLE_S = 0.8
SEARCH_MAX_STEPS = 12
SEARCH_ACCEPT_OFFSET_PX = 160

# Center geometry
CENTER_PULSE_MS = 180
CENTER_SETTLE_S = 0.8
CENTER_DEAD_PX = 60
CENTER_MAX_STEPS = 4

# Between-leg maneuvers
BACKAWAY_MS = 700
BACKAWAY_SETTLE_S = 1.1
HANDOFF_SETTLE_S = 1.0
BLIND_HANDOFF_LEFT_MS = 1400
BLIND_HANDOFF_RIGHT_MS = 1000

# Snapshot buffer drain (the server holds the camera open and stale frames
# accumulate in V4L2 — drain before reading)
SNAP_DRAIN_FRAMES = 3


@dataclass
class Detection:
    tag_id: int
    cx: float
    cy: float
    side: float
    image_w: int
    image_h: int
    margin: float

    @property
    def offset_px(self) -> float:
        return self.cx - self.image_w / 2

    @property
    def estimated_distance_mm(self) -> float:
        focal_px = (self.image_w / 2) / __import__("math").tan(
            __import__("math").radians(ASSUMED_HFOV_DEG / 2)
        )
        return TAG_SIZE_MM * focal_px / self.side


# ---------- client ----------


class LilbugClient:
    def __init__(self, base: str, snap_dir: Path):
        self.base = base.rstrip("/")
        self.session = requests.Session()
        self.det = Detector(
            families=TAG_FAMILY, nthreads=2, quad_decimate=1.0, refine_edges=True
        )
        self.snap_dir = snap_dir
        snap_dir.mkdir(parents=True, exist_ok=True)

    def stop(self) -> None:
        try:
            self.session.post(f"{self.base}/api/stop", timeout=5).raise_for_status()
        except Exception as exc:
            print(f"[client] stop failed: {exc}")

    def _move(self, action: str) -> None:
        self.session.post(f"{self.base}/api/move/{action}", timeout=5).raise_for_status()

    def pulse(self, action: str, ms: int) -> None:
        t0 = time.perf_counter()
        self._move(action)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        remaining = max(0.0, (ms - elapsed_ms) / 1000.0)
        time.sleep(remaining)
        self.stop()

    def fresh_snap(self, name: str, drain: int = SNAP_DRAIN_FRAMES) -> Path:
        path = self.snap_dir / name
        last = None
        for _ in range(drain):
            last = self.session.get(f"{self.base}/snapshot.jpg", timeout=10).content
        path.write_bytes(last)
        return path

    def detect(self, image_path: Path, target_id: int | None = None,
               min_margin: float = 30.0) -> list[Detection]:
        img = cv2.imread(str(image_path))
        if img is None:
            return []
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        out: list[Detection] = []
        for r in self.det.detect(gray):
            if r.hamming != 0 or r.decision_margin < min_margin:
                continue
            if target_id is not None and int(r.tag_id) != target_id:
                continue
            xs = [p[0] for p in r.corners]
            ys = [p[1] for p in r.corners]
            side = max(max(xs) - min(xs), max(ys) - min(ys))
            out.append(Detection(
                tag_id=int(r.tag_id),
                cx=float(r.center[0]),
                cy=float(r.center[1]),
                side=float(side),
                image_w=w,
                image_h=h,
                margin=float(r.decision_margin),
            ))
        return out

    def detect_largest(self, image_path: Path, target_id: int) -> Detection | None:
        cands = self.detect(image_path, target_id=target_id)
        return max(cands, key=lambda c: c.side) if cands else None


# ---------- behaviors ----------


def search_for_tag(client: LilbugClient, tag_id: int, direction: str) -> Detection | None:
    print(f"[search] tag={tag_id} dir={direction}")
    snap = "search.jpg"
    for step in range(SEARCH_MAX_STEPS):
        path = client.fresh_snap(snap)
        det = client.detect_largest(path, tag_id)
        if det is not None:
            if abs(det.offset_px) <= SEARCH_ACCEPT_OFFSET_PX:
                print(f"  step {step}: FOUND cx={det.cx:.0f} side={det.side:.0f}")
                return det
            print(f"  step {step}: edge sighting cx={det.cx:.0f} side={det.side:.0f}, continuing sweep")
            client.pulse(direction, CENTER_PULSE_MS)
            time.sleep(CENTER_SETTLE_S)
            continue
        client.pulse(direction, SEARCH_PULSE_MS)
        time.sleep(SEARCH_SETTLE_S)
    return None


def center_tag(client: LilbugClient, tag_id: int) -> Detection | None:
    snap = "center.jpg"
    last_seen: Detection | None = None
    for step in range(CENTER_MAX_STEPS):
        path = client.fresh_snap(snap)
        det = client.detect_largest(path, tag_id)
        if det is None:
            if last_seen is None:
                print("  [center] tag never seen, abort")
                return None
            recover = "left" if last_seen.offset_px > 0 else "right"
            client.pulse(recover, CENTER_PULSE_MS)
            time.sleep(CENTER_SETTLE_S)
            continue
        last_seen = det
        if abs(det.offset_px) <= CENTER_DEAD_PX:
            return det
        action = "right" if det.offset_px > 0 else "left"
        client.pulse(action, CENTER_PULSE_MS)
        time.sleep(CENTER_SETTLE_S)
    return last_seen


def approach_tag(client: LilbugClient, tag_id: int, target_side_px: float) -> Detection | None:
    snap = "approach.jpg"
    last_seen: Detection | None = None
    for step in range(APPROACH_MAX_STEPS):
        path = client.fresh_snap(snap)
        det = client.detect_largest(path, tag_id)
        if det is None:
            print(f"  [approach] step {step}: lost tag")
            if last_seen is None:
                return None
            # Tag likely swung out of frame from last forward pulse — recover.
            recover = "left" if last_seen.offset_px > 0 else "right"
            client.pulse(recover, CENTER_PULSE_MS)
            time.sleep(CENTER_SETTLE_S)
            continue
        last_seen = det
        if det.side >= target_side_px:
            print(f"  [approach] reached: side={det.side:.0f} >= {target_side_px} "
                  f"(~{det.estimated_distance_mm:.0f} mm)")
            return det
        if abs(det.offset_px) > APPROACH_RECENTER_PX:
            print(f"  [approach] step {step}: drift {det.offset_px:+.0f}px, correcting")
            action = "right" if det.offset_px > 0 else "left"
            client.pulse(action, APPROACH_CORR_MS)
            continue
        if abs(det.offset_px) >= APPROACH_DEAD_PX:
            action = "right" if det.offset_px > 0 else "left"
            client.pulse(action, APPROACH_CORR_MS)
        else:
            forward_ms = APPROACH_FWD_MS if det.side < 35 else APPROACH_NEAR_FWD_MS
            client.pulse("forward", forward_ms)
        time.sleep(APPROACH_SETTLE_S)
    print("  [approach] step budget exhausted")
    return None


def go_to_tag(client: LilbugClient, tag_id: int, target_side_px: float,
              search_dir: str = "right") -> Detection | None:
    found = search_for_tag(client, tag_id, search_dir)
    if found is None:
        opp = "left" if search_dir == "right" else "right"
        print(f"[go] sweeping {opp} as fallback")
        found = search_for_tag(client, tag_id, opp)
    if found is None:
        print(f"[go] tag {tag_id} not found in 360° sweep")
        return None
    reached = approach_tag(client, tag_id, target_side_px)
    if reached is not None:
        return reached
    print(f"[go] lost tag {tag_id} during approach; retrying acquisition")
    found = search_for_tag(client, tag_id, search_dir)
    if found is None:
        opp = "left" if search_dir == "right" else "right"
        found = search_for_tag(client, tag_id, opp)
    if found is None:
        return None
    return approach_tag(client, tag_id, target_side_px)


def back_away(client: LilbugClient, ms: int = BACKAWAY_MS) -> None:
    print(f"[back] reversing {ms}ms for clearance")
    client.pulse("reverse", ms)
    time.sleep(BACKAWAY_SETTLE_S)


def blind_handoff(client: LilbugClient, direction: str, ms: int) -> None:
    if ms <= 0:
        return
    print(f"[handoff] turning {direction} {ms}ms before reacquire")
    client.pulse(direction, ms)
    time.sleep(HANDOFF_SETTLE_S)


# ---------- main ----------


def install_safety_handlers(client: LilbugClient) -> None:
    atexit.register(client.stop)

    def _h(signum, _frame):
        print(f"\n[main] caught signal {signum}, stopping rover")
        client.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _h)
    signal.signal(signal.SIGTERM, _h)


def blind_handoff_for_direction(direction: str, override_ms: int) -> int:
    if override_ms >= 0:
        return override_ms
    return BLIND_HANDOFF_LEFT_MS if direction == "left" else BLIND_HANDOFF_RIGHT_MS


def run_lap(client: LilbugClient, *, first_tag: int, second_tag: int,
            first_search_dir: str, second_search_dir: str,
            target_side_px: float,
            skip_acquire: bool,
            blind_handoff_ms: int) -> bool:
    if not skip_acquire:
        print(f"\n=== acquire start tag {first_tag} ===")
        start = go_to_tag(client, first_tag, target_side_px, first_search_dir)
        if start is None:
            print(f"[lap] failed to acquire start tag {first_tag}")
            return False
    else:
        print(f"\n=== using current pose as tag {first_tag} start ===")
    back_away(client)
    blind_handoff(client, second_search_dir, blind_handoff_for_direction(second_search_dir, blind_handoff_ms))
    print(f"\n=== leg: {first_tag} -> {second_tag} ===")
    b = go_to_tag(client, second_tag, target_side_px, second_search_dir)
    if b is None:
        print(f"[lap] failed to reach tag {second_tag}")
        return False
    back_away(client)
    blind_handoff(client, first_search_dir, blind_handoff_for_direction(first_search_dir, blind_handoff_ms))
    print(f"\n=== leg: {second_tag} -> {first_tag} ===")
    c = go_to_tag(client, first_tag, target_side_px, first_search_dir)
    if c is None:
        print(f"[lap] failed to return to tag {first_tag}")
        return False
    back_away(client)
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--snap-dir", default="/tmp/lilbug_loop")
    ap.add_argument("--target-side-px", type=float, default=TARGET_SIDE_PX,
                    help="image-pixel side of the tag at which we declare 'arrived'")
    ap.add_argument("--first-tag", type=int, default=1,
                    help="tag the rover starts nearest to")
    ap.add_argument("--second-tag", type=int, default=0)
    ap.add_argument("--first-search-dir", default="right",
                    choices=["left", "right"],
                    help="rotation direction to reacquire FIRST tag from the SECOND tag area")
    ap.add_argument("--second-search-dir", default="left",
                    choices=["left", "right"],
                    help="rotation direction to acquire SECOND tag from the FIRST tag area")
    ap.add_argument("--once", action="store_true",
                    help="run one full out-and-back lap and exit")
    ap.add_argument("--max-laps", type=int, default=0,
                    help="stop after this many laps (0 = forever)")
    ap.add_argument("--skip-acquire", action="store_true",
                    help="assume the rover is already positioned near the first tag")
    ap.add_argument("--blind-handoff-ms", type=int, default=-1,
                    help="override blind handoff turn for both directions; default uses room-specific asymmetric values")
    args = ap.parse_args()

    client = LilbugClient(args.base, Path(args.snap_dir))
    install_safety_handlers(client)
    client.stop()

    lap = 0
    while True:
        lap += 1
        print(f"\n############ LAP {lap} ############")
        ok = run_lap(
            client,
            first_tag=args.first_tag,
            second_tag=args.second_tag,
            first_search_dir=args.first_search_dir,
            second_search_dir=args.second_search_dir,
            target_side_px=args.target_side_px,
            skip_acquire=args.skip_acquire,
            blind_handoff_ms=args.blind_handoff_ms,
        )
        if not ok:
            print("[main] lap failed; stopping rover. Reposition and rerun.")
            client.stop()
            break
        if args.once:
            break
        if args.max_laps and lap >= args.max_laps:
            break
    client.stop()


if __name__ == "__main__":
    main()
