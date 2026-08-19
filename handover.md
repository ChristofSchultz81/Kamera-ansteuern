# Handover

Status snapshot for whoever picks up this project next. Update this file as the project evolves; it reflects the *current* state (unlike history.md, which is append-only).

## Current state (2026-08-19)

- Unified, generic camera dashboard implemented:
  - `app.py` — single Flask app, browser-based GUI, camera dropdown, MJPEG video feed, exposure slider, histogram, save button.
  - `cameras/` — driver abstraction (`base.py`), two concrete drivers (`opencv_driver.py` for generic USB/DirectShow cameras, `alliedvision_driver.py` for Allied Vision via `vmbpy`), plus `registry.py` and shared `imaging.py`.
  - `config.py` — all magic numbers centralized.
  - `templates/index.html` — the dashboard page.
  - `legacy/` — the three original per-camera scripts, kept for reference only, no longer maintained.
- Allied Vision camera hardware-tested successfully: `AlliedVisionCameraDriver` opens the real camera (`DEV_1AB22C0301FB`), reads frames (2064x2464 mono), reports/reads exposure range and current value, and closes cleanly. See history.md for details and a pitfall about hung processes if `close()` isn't called after a failed `open()`.
- Fixed: browser video feed was black for the Allied Vision camera because `create_histogram()` crashed on mono `(H, W, 1)` frames and the image/histogram height check in `app.py` almost never matched. Fixed in `cameras/imaging.py` (`ensure_bgr()` helper, `create_histogram(height=...)` parameter) and `app.py`. Verified with synthetic frames and live against the real camera.
- Second camera (Bresser MikroCam SP 5.0) verified working through the existing generic `OpenCVCameraDriver` once its DirectShow driver was installed on the machine — no new driver code needed.
- `app.py` now auto-opens the default browser on startup and auto-shuts-down (including releasing the active camera) once the browser tab stops sending heartbeats, i.e. when it's closed. See `config.py` (`AUTO_OPEN_BROWSER*`, `HEARTBEAT_*`).
- Generic USB webcam driver and full end-to-end browser GUI with the Allied Vision camera still need verification (see backlog.md).
- Git: existing `origin` remote (GitLab, HTW Berlin) untouched. A `github` remote was added and the refactor commit was pushed to `https://github.com/ChristofSchultz81/Kamera-ansteuern` (branch `main`).

## How to run

```
pip install -r requirements.txt
python app.py
```

A folder picker dialog appears first (where to save images), then open `http://127.0.0.1:5000` in a browser.

## Adding a new camera

1. Create `cameras/<name>_driver.py` implementing `CameraDriver` from `cameras/base.py`.
2. Add the class to `DRIVER_CLASSES` in `cameras/registry.py`.
3. Add any camera-specific constants to `config.py`.

No changes to `app.py` or `templates/index.html` should be necessary.
