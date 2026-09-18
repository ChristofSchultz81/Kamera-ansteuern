# Handoff

Notes for the next person/session continuing this work.

## What changed in this session

- Refactored three separate camera scripts into one generic, driver-based architecture (`app.py` + `cameras/`).
- Centralized all magic numbers in `config.py`.
- Added the mandatory `# HEADER: ...` one-line comment to every function (see AGENTS.md — this rule must not be removed).
- Removed the obsolete per-camera scripts after their functionality was absorbed by the generic dashboard.
- Added `history.md` (German, append-only), `handover.md`, `backlog.md`, this `handoff.md`.

## What still needs attention

- No physical camera was available to test streaming/exposure end-to-end during this refactor — see backlog.md.
- The GitHub remote is configured and the refactor has already been pushed; see `history.md` for the commit details.

## Where to look first

- Start at `app.py` to understand the GUI/Flask layer.
- Start at `cameras/base.py` to understand the driver contract before touching any driver.
