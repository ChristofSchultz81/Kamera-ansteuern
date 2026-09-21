# Handover

Status snapshot for whoever picks up this project next. Update this file as the project evolves; it reflects the *current* state (unlike history.md, which is append-only).

## Current state (2026-09-21)

- Unified, generic camera dashboard implemented:
  - `app.py` — single Flask app, browser-based GUI, camera dropdown, MJPEG video feed, exposure slider, histogram, save button.
  - `cameras/` — driver abstraction (`base.py`), two concrete drivers (`opencv_driver.py` for generic USB/DirectShow cameras, `alliedvision_driver.py` for Allied Vision via `vmbpy`), plus `registry.py` and shared `imaging.py`.
  - `config.py` — all magic numbers centralized.
  - `templates/index.html` — the dashboard page.
- Allied Vision camera hardware-tested successfully: `AlliedVisionCameraDriver` opens the real camera (`DEV_1AB22C0301FB`), reads frames (2064x2464 mono), reports/reads exposure range and current value, and closes cleanly. See history.md for details and a pitfall about hung processes if `close()` isn't called after a failed `open()`.
- Fixed: browser video feed was black for the Allied Vision camera because `create_histogram()` crashed on mono `(H, W, 1)` frames and the image/histogram height check in `app.py` almost never matched. Fixed in `cameras/imaging.py` (`ensure_bgr()` helper, `create_histogram(height=...)` parameter) and `app.py`. Verified with synthetic frames and live against the real camera.
- Second camera (Bresser MikroCam SP 5.0) verified working through the existing generic `OpenCVCameraDriver` once its DirectShow driver was installed on the machine — no new driver code needed.
- `app.py` now auto-opens the default browser on startup and auto-shuts-down (including releasing the active camera) once the browser tab stops sending heartbeats, i.e. when it's closed. See `config.py` (`AUTO_OPEN_BROWSER*`, `HEARTBEAT_*`).
- The obsolete per-camera scripts were removed after their driver logic had been absorbed into `cameras/opencv_driver.py` and `cameras/alliedvision_driver.py`.
- Bresser MikroCam SP 5.0 confirmed fully working end-to-end through the browser dashboard (generic `OpenCVCameraDriver`, no new code needed). An earlier black-image report was a flaky USB connection, not a bug — resolved by re-plugging the camera.
- Video feed (`#videoFeed`) now scales responsively to the browser window/screen resolution (`max-width: 90vw; max-height: 70vh; object-fit: contain`), regardless of the camera's native resolution.
- Python 3.14.6 compatibility was checked. The runtime dependencies in `requirements.txt` now use Python-3.14-compatible version ranges; central camera-module imports pass under Python 3.14.6.
- OpenCV USB discovery and opening now use `CAP_ANY` via `config.OPENCV_BACKEND`, allowing UVC cameras to use DirectShow or Media Foundation automatically. Verified with a live frame through the `MSMF` backend.
- The browser dashboard now supports two-point pixel-distance measurements directly on the live camera image. The overlay converts responsive display coordinates back to native camera pixels, ignores histogram clicks, and can be reset.
- Completed measurements are labeled directly on the image, and `Add another pair` starts additional measurements without removing earlier ones. Overlays are recalculated from native coordinates after resizing.
- Saving now sends native measurement coordinates to Flask, which renders points, lines, and distance labels into the captured image before writing the file.
- Separate UVC launchers are available: `app_ubuntu.py` uses Ubuntu Video4Linux2, while `app_windows11.py` lets OpenCV use the Windows inbox UVC backend. They share the same dashboard and require no camera-vendor driver for standard UVC cameras.
- The save-folder picker is optional. Without Tkinter or a graphical session, the application creates and uses the current user's `Downloads` directory.
- A Windows distribution was built with PyInstaller. Deliver `dist\CameraDashboard-Windows11\` as a complete folder and start `CameraDashboard-Windows11.exe`; Python and Python packages are bundled. The Bresser DirectShow driver is still required on the target PC.
- Generic USB webcam driver and full end-to-end browser GUI with the Allied Vision camera still need verification (see backlog.md).
- Git: existing `origin` remote (GitLab, HTW Berlin) untouched. A `github` remote was added and the refactor commit was pushed to `https://github.com/ChristofSchultz81/Kamera-ansteuern` (branch `main`).

## How to run

```powershell
pip install -r requirements.txt
python app_windows11.py
```

A folder picker dialog appears first (where to save images), then open `http://127.0.0.1:5000` in a browser.

On Ubuntu, use:

```bash
python3 -m pip install -r requirements.txt
python3 app_ubuntu.py
```

## Windows EXE distribution

- Build configuration: `app_windows11.spec`.
- Ready-to-distribute application: `dist\CameraDashboard-Windows11\CameraDashboard-Windows11.exe`.
- Rebuild with `python -m PyInstaller --noconfirm --clean app_windows11.spec` after installing PyInstaller.

## Adding a new camera

1. Create `cameras/<name>_driver.py` implementing `CameraDriver` from `cameras/base.py`.
2. Add the class to `DRIVER_CLASSES` in `cameras/registry.py`.
3. Add any camera-specific constants to `config.py`.

No changes to `app.py` or `templates/index.html` should be necessary.
