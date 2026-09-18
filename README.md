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
