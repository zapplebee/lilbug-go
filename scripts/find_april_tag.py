"""Find a target AprilTag using landmark hints and optional depth-aware caution.

Examples:
    python scripts/find_april_tag.py --target-tag 3
    python scripts/find_april_tag.py --target-tag 1 --use-depth
"""

from __future__ import annotations

import argparse
import atexit
import json
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import requests
from PIL import Image
from pupil_apriltags import Detector

from landmark_kb import LandmarkKB

try:
    from transformers import pipeline
except ImportError:  # pragma: no cover - optional path
    pipeline = None


DEFAULT_BASE = "http://192.168.1.179:8000"
DB_PATH = Path("data/landmarks.sqlite3")
SNAP_DIR = Path("/tmp/lilbug_find")
SEARCH_PULSE_MS = 350
TURN_CORR_MS = 180
FORWARD_MS = 900
FORWARD_NEAR_MS = 600
REVERSE_MS = 600
SETTLE_S = 0.8
ARRIVAL_SIDE_PX = 55
SEARCH_ACCEPT_OFFSET_PX = 170
CENTER_DEAD_PX = 70


@dataclass
class Detection:
    tag_id: int
    cx: float
    cy: float
    side: float
    margin: float
    image_w: int
    image_h: int

    @property
    def offset_px(self) -> float:
        return self.cx - self.image_w / 2


class DepthEstimator:
    def __init__(self) -> None:
        if pipeline is None:
            raise RuntimeError("transformers is not installed; use requirements-vision.txt")
        self._pipe = pipeline("depth-estimation", model="LiheYoung/depth-anything-small-hf")

    def obstacle_warning(self, image_path: Path) -> bool:
        image = Image.open(image_path).convert("RGB")
        depth = self._pipe(image)["depth"]
        depth_map = cv2.resize(
            cv2.cvtColor(__import__("numpy").array(depth), cv2.COLOR_RGB2GRAY),
            (image.width, image.height),
            interpolation=cv2.INTER_CUBIC,
        )
        lower = depth_map[int(image.height * 0.60):, int(image.width * 0.30):int(image.width * 0.70)]
        if lower.size == 0:
            return False
        # Depth-anything output is relative. High brightness in the lower-middle
        # of the frame is treated as "near obstacle likely".
        return float(lower.mean()) > 160.0


class RoverClient:
    def __init__(self, base: str, snap_dir: Path) -> None:
        self.base = base.rstrip("/")
        self.session = requests.Session()
        self.detector = Detector(families="tag25h9", nthreads=2, quad_decimate=1.0, refine_edges=True)
        self.snap_dir = snap_dir
        self.snap_dir.mkdir(parents=True, exist_ok=True)

    def stop(self) -> None:
        try:
            self.session.post(f"{self.base}/api/stop", timeout=5).raise_for_status()
        except Exception:
            pass

    def pulse(self, action: str, ms: int, settle_s: float = SETTLE_S) -> None:
        self.session.post(f"{self.base}/api/move/{action}", timeout=5).raise_for_status()
        time.sleep(ms / 1000)
        self.stop()
        time.sleep(settle_s)

    def snapshot(self, name: str) -> Path:
        last = None
        for _ in range(3):
            last = self.session.get(f"{self.base}/snapshot.jpg", timeout=10).content
        path = self.snap_dir / name
        path.write_bytes(last)
        return path

    def detect(self, image_path: Path) -> list[Detection]:
        image = cv2.imread(str(image_path))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        out: list[Detection] = []
        for result in self.detector.detect(gray):
            if result.hamming != 0 or result.decision_margin < 20:
                continue
            xs = [point[0] for point in result.corners]
            ys = [point[1] for point in result.corners]
            out.append(
                Detection(
                    tag_id=int(result.tag_id),
                    cx=float(result.center[0]),
                    cy=float(result.center[1]),
                    side=float(max(max(xs) - min(xs), max(ys) - min(ys))),
                    margin=float(result.decision_margin),
                    image_w=w,
                    image_h=h,
                )
            )
        return out


def best_detection(detections: list[Detection], tag_id: int) -> Detection | None:
    matches = [det for det in detections if det.tag_id == tag_id]
    return max(matches, key=lambda det: det.side) if matches else None


def visible_tag_ids(detections: list[Detection]) -> str:
    return json.dumps(sorted({det.tag_id for det in detections}))


def preferred_search_direction(kb: LandmarkKB, detections: list[Detection], target_tag: int, fallback: str) -> str:
    known = [det.tag_id for det in detections if kb.landmark(det.tag_id) is not None and det.tag_id != target_tag]
    for source in known:
        handoff = kb.handoff(source, target_tag)
        if handoff is not None and handoff["search_direction"] in {"left", "right"}:
            return str(handoff["search_direction"])
    return fallback


def install_safety(client: RoverClient) -> None:
    atexit.register(client.stop)

    def _handler(signum: int, _frame: object) -> None:
        print(f"caught signal {signum}, stopping rover")
        client.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-tag", type=int, required=True)
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--snap-dir", default=str(SNAP_DIR))
    parser.add_argument("--search-dir", default="left", choices=["left", "right"])
    parser.add_argument("--max-steps", type=int, default=40)
    parser.add_argument("--use-depth", action="store_true")
    args = parser.parse_args()

    kb = LandmarkKB(args.db)
    client = RoverClient(args.base, Path(args.snap_dir))
    install_safety(client)
    depth = DepthEstimator() if args.use_depth else None

    for step in range(args.max_steps):
        image_path = client.snapshot(f"step_{step:03d}.jpg")
        detections = client.detect(image_path)
        target = best_detection(detections, args.target_tag)
        obstacle_warning = depth.obstacle_warning(image_path) if depth is not None else False

        kb.record_observation(
            tag_id=target.tag_id if target is not None else None,
            snapshot_path=str(image_path),
            center_x=target.cx if target is not None else None,
            center_y=target.cy if target is not None else None,
            side_px=target.side if target is not None else None,
            decision_margin=target.margin if target is not None else None,
            visible_tags=visible_tag_ids(detections),
            depth_warning=obstacle_warning,
            note=f"step={step}",
        )

        if target is not None:
            print(f"step {step}: tag {args.target_tag} cx={target.cx:.0f} side={target.side:.0f}")
            if target.side >= ARRIVAL_SIDE_PX:
                kb.confirm_landmark(args.target_tag, None, f"Observed during find_april_tag run from {image_path}")
                print(f"arrived near tag {args.target_tag}")
                client.stop()
                kb.close()
                return
            if abs(target.offset_px) >= CENTER_DEAD_PX:
                client.pulse("right" if target.offset_px > 0 else "left", TURN_CORR_MS)
                continue
            if obstacle_warning:
                print("depth warning in lower-center frame, backing away before continuing")
                client.pulse("reverse", REVERSE_MS)
                continue
            forward_ms = FORWARD_MS if target.side < 35 else FORWARD_NEAR_MS
            client.pulse("forward", forward_ms)
            continue

        direction = preferred_search_direction(kb, detections, args.target_tag, args.search_dir)
        if obstacle_warning:
            print(f"step {step}: no target, obstacle warning active, rotating {direction}")
            client.pulse(direction, TURN_CORR_MS)
        else:
            print(f"step {step}: no target, searching {direction}")
            client.pulse(direction, SEARCH_PULSE_MS)

    client.stop()
    kb.close()
    raise SystemExit(f"Failed to find tag {args.target_tag} within {args.max_steps} steps")


if __name__ == "__main__":
    main()
