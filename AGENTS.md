# AGENTS.md

## Project structure

```
kamera-anteuern-und-auslesen/
├── app.py                       # Flask GUI entry point, run with `python app.py`
├── config.py                    # all magic numbers/constants live here
├── requirements.txt
├── cameras/
│   ├── base.py                  # CameraDriver interface (generic API)
│   ├── opencv_driver.py         # generic USB/DirectShow webcam driver
│   ├── alliedvision_driver.py   # Allied Vision driver (vmbpy)
│   ├── registry.py              # driver_key -> driver class registration
│   └── imaging.py                # shared histogram / JPEG helpers
├── templates/
│   └── index.html               # dashboard page (camera dropdown, video feed, controls)
├── old/                         # original per-camera scripts, reference only
│   ├── camera_dashboard.py
│   ├── camera_dashboard_Alliedvision.py
│   ├── Any_Cam_USB_WEBCAM-BROWSER.py
│   └── USB_OLDLiMi_Cam.py
├── docs/                        # camera datasheets etc.
├── history.md                   # append-only project history (German, never delete entries)
├── handover.md                  # current status snapshot
├── backlog.md                   # open work items
└── handoff.md                   # session-to-session handoff notes
```

## Rules for changes in this repository

- All code and comments must be written in English.
- Every function must have a one-line `# HEADER: ...` comment (or docstring)
  as the first line of its body, describing what it does. **This header
  must never be removed**, even during refactors — extend it if behavior
  changes, but do not delete it.
- No magic numbers in the code: add constants to `config.py` instead.
- Camera hardware support must go through the `CameraDriver` interface in
  `cameras/base.py`. Adding a new camera model must only require a new
  driver module + one registry entry in `cameras/registry.py` — never
  changes to `app.py` or `templates/index.html`.
- `history.md` is append-only: add new dated sections, never edit or
  delete existing ones. Written in German.
- `handover.md` reflects current state (may be rewritten). `backlog.md`
  tracks open items. `handoff.md` is session-handoff notes. Keep all
  three updated when finishing significant work.
