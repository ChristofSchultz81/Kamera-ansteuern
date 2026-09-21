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

## UVC camera versions

The two operating-system launchers support generic USB Video Class (UVC)
cameras using only the camera interface built into the operating system. They
do not require a camera-vendor driver or SDK. A non-UVC camera, including an
Allied Vision camera or the Bresser MikroCam SP 5.0, still requires its
manufacturer's driver or SDK.

On Ubuntu, use the kernel's Video4Linux2 interface:

```bash
python3 -m pip install -r requirements.txt
python3 app_ubuntu.py
```

On Windows 11, use the built-in UVC backend (Media Foundation or DirectShow):

```powershell
python -m pip install -r requirements.txt
python app_windows11.py
```

If the graphical folder picker is unavailable, for example on an Ubuntu
installation without Tkinter, captured images are saved in `~/Downloads`.

## Windows 11 executable

The ready-to-distribute Windows application is:

`dist\CameraDashboard-Windows11\CameraDashboard-Windows11.exe`

Copy the complete `CameraDashboard-Windows11` folder to the target PC and run
the executable inside it. Do not copy the `.exe` by itself because it needs the
bundled `_internal` folder. The target PC does not need Python or the packages
from `requirements.txt`.

To rebuild the distribution folder on a development PC, install PyInstaller
and run:

```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean app_windows11.spec
```

The Bresser MikroCam SP 5.0 is not a UVC camera. Its Bresser DirectShow driver
must still be installed on the Windows target PC before the executable can
access it.

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
python -m compileall -q app.py cameras
```
