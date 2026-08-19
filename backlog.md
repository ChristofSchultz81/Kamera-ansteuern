# Backlog

Open items, roughly in priority order. Move finished items to history.md instead of deleting them here.

- [x] Push repository to the new GitHub remote `https://github.com/ChristofSchultz81/Kamera-ansteuern` — done, commit `3863a8c` on `main`.
- [x] Hardware-test `AlliedVisionCameraDriver` directly against the real Allied Vision camera — done, works (open/read_frame/exposure/close all verified).
- [ ] Hardware-test the full `app.py` browser dashboard end-to-end with the Allied Vision camera selected from the dropdown (open/close through the Flask API, not just the driver directly) — image pipeline bug fixed, but full browser UI click-through with a real camera still needs confirmation from the user.
- [x] Hardware-test the generic USB webcam driver and the old Limi USB camera through the dashboard — done via the Bresser MikroCam SP 5.0 (same generic OpenCV driver); black-image issue traced to a flaky USB connection, resolved by re-plugging.
- [ ] Investigate the extra `DEV_Cam1/2/3` entries reported by vmbpy discovery (likely simulator/demo devices) and consider filtering them out in `AlliedVisionCameraDriver.discover()` if they are not real hardware.
- [ ] Verify vmbpy install instructions in `requirements.txt` against the actual SDK version in use.
- [ ] Consider adding automatic re-discovery / hot-plug detection instead of manual "Refresh camera list" button.
- [ ] Consider persisting the exposure value per camera between sessions.
- [ ] Add basic automated tests for `cameras/registry.py` (driver registration) and `cameras/imaging.py` (histogram shape/dtype).
- [ ] Decide whether `old/` scripts should eventually be deleted once the new dashboard is confirmed working in production.
- [ ] Next planned feature (new branch): measurement tool overlay on the camera image (e.g. draw a line/ruler on the live frame and read out a distance, likely needs a pixel-to-real-world calibration step per camera/lens).
