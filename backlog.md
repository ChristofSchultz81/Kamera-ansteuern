# Backlog

Open items, roughly in priority order. Move finished items to history.md instead of deleting them here.

- [ ] Push repository to the new GitHub remote `https://github.com/ChristofSchultz81/Kamera-ansteuern` (auth needs to be set up: SSH key or GitHub CLI login for this machine).
- [ ] Hardware-test the unified dashboard with all three physical cameras (generic USB webcam, old Limi USB camera, Allied Vision Alvium).
- [ ] Verify vmbpy install instructions in `requirements.txt` against the actual SDK version in use.
- [ ] Consider adding automatic re-discovery / hot-plug detection instead of manual "Refresh camera list" button.
- [ ] Consider persisting the exposure value per camera between sessions.
- [ ] Add basic automated tests for `cameras/registry.py` (driver registration) and `cameras/imaging.py` (histogram shape/dtype).
- [ ] Decide whether `legacy/` scripts should eventually be deleted once the new dashboard is confirmed working in production.
