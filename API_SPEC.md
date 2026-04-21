# Lilbug Rover API Spec

Base URL:

```text
Primary field URL on rover AP: http://192.168.4.1:8000
Upstream/home-network URL: DHCP-assigned on wlan1
```

## Endpoints

### `GET /`
Returns the HTML browser control UI.

### `GET /api/status`
Returns current rover status as JSON.

Example response:

```json
{
  "action": "stop",
  "camera_stream": "/stream.mjpg",
  "gpio_mode": "rpi"
}
```

### `POST /api/move/<action>`
Starts continuous motion for one action until another command is sent.

Valid actions:
- `forward`
- `reverse`
- `left`
- `right`

Example:

```text
POST /api/move/forward
```

Success response:

```json
{
  "action": "forward"
}
```

Invalid action response:

```json
{
  "error": "Unknown action: foo"
}
```

### `POST /api/stop`
Stops rover motion.

Success response:

```json
{
  "action": "stop"
}
```

### `GET /stream.mjpg`
Returns a live MJPEG stream.

Response content type:

```text
multipart/x-mixed-replace; boundary=frame
```

### `GET /snapshot.jpg`
Returns a single current camera frame.

Response content type:

```text
image/jpeg
```

## Control Notes

- Movement is continuous until another move command or `POST /api/stop` is sent.
- For scripted control, send a move command, wait briefly, then send stop.
- The current UI is direct directional input: hold one direction, release to stop.
- Keyboard and gamepad clients should also treat control as direct four-direction input, not throttle-plus-steering.

Example movement pulse:

```bash
curl -X POST http://192.168.4.1:8000/api/move/forward
sleep 0.4
curl -X POST http://192.168.4.1:8000/api/stop
```

Example snapshot fetch:

```bash
curl -o snapshot.jpg http://192.168.4.1:8000/snapshot.jpg
```

## Current Motion Mapping

- `forward`: GPIO17 low, GPIO27 high, GPIO22 high, GPIO23 low
- `right`: GPIO17 high, GPIO27 low, GPIO22 high, GPIO23 low
- `reverse`: GPIO17 high, GPIO27 low, GPIO22 low, GPIO23 high
- `left`: GPIO17 low, GPIO27 high, GPIO22 low, GPIO23 high
- `stop`: all high

## Operational Notes

- The camera is available as both a live MJPEG stream and single-frame JPEG snapshots.
- There is no authentication on the current API.
- The rover service is running on the Pi under systemd as `lilbug-rover.service`.
- The most reliable driving URL in the field is the AP-side address `192.168.4.1`, not the upstream-side DHCP address.
