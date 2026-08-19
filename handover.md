# Handover

Status snapshot for whoever picks up this project next. Update this file as the project evolves; it reflects the *current* state (unlike history.md, which is append-only).

## Current state (2026-08-19)

- Unified, generic camera dashboard implemented:
  - `app.py` — single Flask app, browser-based GUI, camera dropdown, MJPEG video feed, exposure slider, histogram, save button.
  - `cameras/` — driver abstraction (`base.py`), two concrete drivers (`opencv_driver.py` for generic USB/DirectShow cameras, `alliedvision_driver.py` for Allied Vision via `vmbpy`), plus `registry.py` and shared `imaging.py`.
  - `config.py` — all magic numbers centralized.
  - `templates/index.html` — the dashboard page.
  - `legacy/` — the three original per-camera scripts, kept for reference only, no longer maintained.
- Not yet hardware-tested: no camera was physically connected in the environment where this refactor was done. `python -m py_compile` and module imports succeed, but the actual camera streaming/exposure paths need to be verified on a machine with the cameras attached.
- Git: existing `origin` remote (GitLab, HTW Berlin) untouched. A new `github` remote should be added pointing to `https://github.com/ChristofSchultz81/Kamera-ansteuern` and pushed there (see backlog.md).

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
