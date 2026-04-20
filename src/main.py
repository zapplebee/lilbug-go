"""Snap Rover web control app."""

from __future__ import annotations

import atexit
import logging
import os
import signal
import sys
import threading
import time
from typing import Iterator

from flask import Flask, Response, jsonify, render_template

try:
    import cv2  # type: ignore
except ImportError:  # pragma: no cover - handled at runtime on the Pi
    cv2 = None

try:
    import RPi.GPIO as GPIO  # type: ignore
except ImportError:  # pragma: no cover - local development fallback
    GPIO = None


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
LOGGER = logging.getLogger("lilbug")


PINS = {
    "in1": 17,
    "in2": 27,
    "in3": 22,
    "in4": 23,
}

STATE_BY_ACTION = {
    # Relay channel order was changed during wiring, so motion commands are
    # remapped to the states that produce the intended rover behavior.
    "forward": {"in1": 0, "in2": 1, "in3": 1, "in4": 0},
    "reverse": {"in1": 1, "in2": 0, "in3": 0, "in4": 1},
    "left": {"in1": 0, "in2": 1, "in3": 0, "in4": 1},
    "right": {"in1": 1, "in2": 0, "in3": 1, "in4": 0},
    "stop": {"in1": 1, "in2": 1, "in3": 1, "in4": 1},
}


class FakeGPIO:
    BCM = "BCM"
    OUT = "OUT"

    def __init__(self) -> None:
        self.values: dict[int, int] = {}

    def setmode(self, mode: str) -> None:
        LOGGER.info("Using fake GPIO mode=%s", mode)

    def setwarnings(self, enabled: bool) -> None:
        LOGGER.debug("Fake GPIO warnings=%s", enabled)

    def setup(self, pin: int, mode: str, initial: int | None = None) -> None:
        if initial is not None:
            self.values[pin] = initial
        LOGGER.info("Fake GPIO setup pin=%s mode=%s initial=%s", pin, mode, initial)

    def output(self, pin: int, value: int) -> None:
        self.values[pin] = value
        LOGGER.info("Fake GPIO output pin=%s value=%s", pin, value)

    def cleanup(self) -> None:
        LOGGER.info("Fake GPIO cleanup")


class RoverController:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._gpio = GPIO if GPIO is not None else FakeGPIO()
        self._current_action = "stop"

        self._gpio.setwarnings(False)
        self._gpio.setmode(self._gpio.BCM)
        for name, pin in PINS.items():
            self._gpio.setup(pin, self._gpio.OUT, initial=STATE_BY_ACTION["stop"][name])
        self.apply("stop")

    @property
    def current_action(self) -> str:
        return self._current_action

    def apply(self, action: str) -> str:
        if action not in STATE_BY_ACTION:
            raise ValueError(f"Unknown action: {action}")

        with self._lock:
            for name, value in STATE_BY_ACTION[action].items():
                self._gpio.output(PINS[name], value)
            self._current_action = action
            LOGGER.info("Applied rover action=%s", action)
            return action

    def stop(self) -> None:
        self.apply("stop")

    def cleanup(self) -> None:
        try:
            self.stop()
        finally:
            self._gpio.cleanup()


class CameraStream:
    def __init__(self) -> None:
        self._camera_index = int(os.getenv("CAMERA_INDEX", "0"))
        self._width = int(os.getenv("CAMERA_WIDTH", "640"))
        self._height = int(os.getenv("CAMERA_HEIGHT", "480"))
        self._fps = int(os.getenv("CAMERA_FPS", "20"))
        self._lock = threading.Lock()
        self._capture = None

    def _open(self):
        if cv2 is None:
            raise RuntimeError("OpenCV is not installed")

        if self._capture is None:
            capture = cv2.VideoCapture(self._camera_index)
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
            capture.set(cv2.CAP_PROP_FPS, self._fps)
            if not capture.isOpened():
                capture.release()
                raise RuntimeError(f"Unable to open camera index {self._camera_index}")
            self._capture = capture
            LOGGER.info("Opened camera index=%s", self._camera_index)

        return self._capture

    def frames(self) -> Iterator[bytes]:
        frame_delay = 1 / max(self._fps, 1)

        while True:
            try:
                with self._lock:
                    capture = self._open()
                    ok, frame = capture.read()
                if not ok:
                    raise RuntimeError("Camera read failed")

                ok, encoded = cv2.imencode(".jpg", frame)
                if not ok:
                    raise RuntimeError("JPEG encode failed")

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + encoded.tobytes() + b"\r\n"
                )
                time.sleep(frame_delay)
            except GeneratorExit:
                raise
            except Exception as exc:  # pragma: no cover - hardware/runtime path
                LOGGER.warning("Camera stream interrupted: %s", exc)
                self.release()
                break

    def snapshot(self) -> bytes:
        with self._lock:
            capture = self._open()
            ok, frame = capture.read()

        if not ok:
            raise RuntimeError("Camera read failed")

        ok, encoded = cv2.imencode(".jpg", frame)
        if not ok:
            raise RuntimeError("JPEG encode failed")

        return encoded.tobytes()

    def release(self) -> None:
        with self._lock:
            if self._capture is not None:
                self._capture.release()
                self._capture = None
                LOGGER.info("Released camera")


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
rover = RoverController()
camera = CameraStream()


def _shutdown(*_args: object) -> None:
    rover.cleanup()
    camera.release()


def _handle_signal(signum: int, _frame: object) -> None:
    LOGGER.info("Received signal=%s, shutting down", signum)
    _shutdown()
    raise SystemExit(0)


atexit.register(_shutdown)
signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


@app.get("/")
def index() -> str:
    return render_template("index.html", actions=[a for a in STATE_BY_ACTION if a != "stop"])


@app.get("/api/status")
def status() -> Response:
    return jsonify(
        {
            "action": rover.current_action,
            "camera_stream": "/stream.mjpg",
            "gpio_mode": "rpi" if GPIO is not None else "fake",
        }
    )


@app.post("/api/move/<action>")
def move(action: str) -> Response:
    try:
        applied_action = rover.apply(action)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # pragma: no cover - hardware/runtime path
        LOGGER.exception("Failed to apply action=%s", action)
        rover.stop()
        return jsonify({"error": str(exc)}), 500

    return jsonify({"action": applied_action})


@app.post("/api/stop")
def stop() -> Response:
    rover.stop()
    return jsonify({"action": rover.current_action})


@app.get("/stream.mjpg")
def stream() -> Response:
    return Response(
        camera.frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/snapshot.jpg")
def snapshot() -> Response:
    try:
        return Response(camera.snapshot(), mimetype="image/jpeg")
    except Exception as exc:  # pragma: no cover - hardware/runtime path
        LOGGER.exception("Failed to capture snapshot")
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    try:
        app.run(
            host=os.getenv("LILBUG_HOST", "0.0.0.0"),
            port=int(os.getenv("LILBUG_PORT", "8000")),
            debug=False,
            threaded=True,
            use_reloader=False,
        )
    except KeyboardInterrupt:
        _shutdown()
        sys.exit(0)
