# Kamera ansteuern und auslesen

A unified browser dashboard for selecting cameras, viewing live images,
adjusting exposure, saving frames, and measuring pixel distances.

## Project structure

- `app.py` - Flask entry point and API routes.
- `config.py` - Central application and camera settings.
- `cameras/` - Camera drivers and shared image processing.
- `templates/index.html` - Browser dashboard.
- `requirements.txt` - Python dependencies.

## Getting started

Install the dependencies and start the dashboard:

```powershell
pip install -r requirements.txt
python app.py
```

At startup, select the folder for captured images. The browser opens the
dashboard automatically at `http://127.0.0.1:5000`.

## Windows 10 executable

The Bresser-specific, ready-to-distribute Windows 10 application is:

`dist\BresserCameraDashboard-Windows10.exe`

Copy this one `.exe` file to the target PC and start it by double-clicking it.
The target PC does not need internet access, Python, or the packages from
`requirements.txt`. The browser opens automatically and captured images are
saved in the current user's `Downloads` folder.

To rebuild the distribution folder on a development PC, install PyInstaller
and run:

```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean app_bresser_windows10.spec
```

The Bresser MikroCam SP 5.0 is not a UVC camera. Its Bresser DirectShow driver
must still be installed on the Windows target PC before the executable can
access it.

The Bresser executable first uses the Bresser/ToupTek OEM SDK installed by
MikroCamLabII. A detected proprietary camera appears as
`Bresser MikroCam SDK: ...` in the dropdown. It then falls back to DirectShow;
entries labeled `USB webcam` are generic webcam devices.

If MikroCamLabII was installed in a custom location and the SDK camera does not
appear, set `BRESSER_CAMERA_SDK_DLL` on the laboratory PC to the full path of
the installed `BresserCam.dll` or `toupcam.dll`, then start the executable
again. This does not require Python or an internet connection.
DirectShow entries marked `(initializing)` are deliberately kept in the list
even when the camera has not returned its first image during the scan.

## Using the dashboard

1. Select a camera and adjust its exposure with the slider.
2. Click two points in the camera image to measure their distance in pixels.
3. Use **Add another pair** to keep the first measurement and start another.
4. Use **Reset measurement** to clear all measurements.
5. Enter an optional filename label before saving an image.

The histogram area is not part of the pixel measurement.
Saved images include the visible measurement points, lines, and distance labels.

## Development checks

Run the Python syntax check from the project directory:

```powershell
python -m compileall -q app.py app_bresser_windows10.py cameras
```
