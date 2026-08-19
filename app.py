"""Unified, browser-based camera dashboard.

Replaces the previous per-camera scripts (see legacy/). Any camera model
registered in cameras/registry.py can be picked from a dropdown in the
browser; the GUI code below only ever talks to the generic
``CameraDriver`` interface, never to a specific camera SDK.
"""

import os
import threading
import time
from datetime import datetime

import cv2
import tkinter as tk
from tkinter import filedialog
from flask import Flask, Response, jsonify, render_template, request

import config
from cameras.imaging import create_histogram, encode_jpeg, ensure_bgr
from cameras.registry import create_driver, discover_all_cameras

app = Flask(__name__)

# Guards access to the currently active driver, since Flask serves requests
# (camera selection, exposure changes, streaming) on different threads.
_session_lock = threading.Lock()
_active_driver = None
_save_directory = os.getcwd()


def select_save_directory() -> str:
    # HEADER: Asks the user (via a native folder dialog) where captured images should be saved.
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    chosen_dir = filedialog.askdirectory(title="Select folder for saved images")
    root.destroy()

    if chosen_dir:
        return os.path.normpath(chosen_dir)
    return os.path.join(os.environ.get("USERPROFILE", os.getcwd()), config.DEFAULT_SAVE_SUBDIR)


@app.route("/")
def index():
    # HEADER: Renders the single-page dashboard shell (camera dropdown, video feed, controls).
    return render_template("index.html", save_dir=_save_directory)


@app.route("/api/cameras")
def api_cameras():
    # HEADER: Returns the list of currently discoverable cameras across all registered drivers.
    descriptors = discover_all_cameras()
    return jsonify(
        cameras=[
            {
                "driver_key": d.driver_key,
                "device_id": d.device_id,
                "display_name": d.display_name,
            }
            for d in descriptors
        ]
    )


@app.route("/api/select", methods=["POST"])
def api_select():
    # HEADER: Closes any previously active camera and opens the one requested by the browser.
    global _active_driver

    payload = request.get_json(force=True)
    driver_key = payload.get("driver_key")
    device_id = payload.get("device_id")

    with _session_lock:
        if _active_driver is not None:
            _active_driver.close()
            _active_driver = None

        try:
            driver = create_driver(driver_key)
            driver.open(device_id)
        except Exception as error:
            return jsonify(success=False, message=str(error))

        _active_driver = driver
        exposure_min, exposure_max = driver.get_exposure_range()
        exposure_current = driver.get_exposure()

    return jsonify(
        success=True,
        exposure_min=exposure_min,
        exposure_max=exposure_max,
        exposure_current=exposure_current,
    )


@app.route("/api/set_exposure", methods=["POST"])
def api_set_exposure():
    # HEADER: Forwards a new exposure value from the browser slider to the active camera driver.
    payload = request.get_json(force=True)
    value = float(payload.get("value"))

    with _session_lock:
        if _active_driver is None:
            return jsonify(success=False, message="No camera selected")
        try:
            _active_driver.set_exposure(value)
        except Exception as error:
            return jsonify(success=False, message=str(error))

    return jsonify(success=True)


@app.route("/api/save_image", methods=["POST"])
def api_save_image():
    # HEADER: Captures the current frame from the active camera and writes it to the save folder.
    with _session_lock:
        if _active_driver is None:
            return jsonify(success=False, message="No camera selected")
        frame = _active_driver.read_frame()

    if frame is None:
        return jsonify(success=False, message="No live image available to save")

    timestamp = datetime.now().strftime(config.IMAGE_TIMESTAMP_FORMAT)
    filename = f"{timestamp}{config.IMAGE_FILE_EXTENSION}"
    full_path = os.path.join(_save_directory, filename)

    success = cv2.imwrite(full_path, frame)
    if success:
        return jsonify(success=True, message=f"Saved: {filename}")
    return jsonify(success=False, message=f"Could not write file: {full_path}")


def _generate_stream_frames():
    # HEADER: Generator yielding MJPEG-encoded frames (image + histogram side by side) for the browser.
    while True:
        with _session_lock:
            driver = _active_driver

        if driver is None:
            time.sleep(config.STREAM_IDLE_RETRY_DELAY_SECONDS)
            continue

        try:
            frame = driver.read_frame()
            if frame is None:
                time.sleep(config.STREAM_IDLE_RETRY_DELAY_SECONDS)
                continue

            frame_bgr = ensure_bgr(frame)
            histogram = create_histogram(frame, height=frame_bgr.shape[0])
            histogram_bgr = cv2.cvtColor(histogram, cv2.COLOR_GRAY2BGR)
            combined = cv2.hconcat([frame_bgr, histogram_bgr])

            jpeg_bytes = encode_jpeg(combined)
            if jpeg_bytes is None:
                continue

            yield (
                b"--" + config.MJPEG_BOUNDARY.encode() + b"\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n"
            )
            time.sleep(config.OPENCV_STREAM_FRAME_DELAY_SECONDS)
        except Exception as error:
            print(f"[ERROR] Streaming loop failed: {error}")
            time.sleep(config.STREAM_ERROR_RETRY_DELAY_SECONDS)


@app.route("/video_feed")
def video_feed():
    # HEADER: Exposes the MJPEG stream at a stable URL consumed by the <img> tag in the browser.
    return Response(
        _generate_stream_frames(),
        mimetype=f"multipart/x-mixed-replace; boundary={config.MJPEG_BOUNDARY}",
    )


def main():
    # HEADER: Application entry point: asks for a save folder, then starts the Flask dev server.
    global _save_directory
    _save_directory = select_save_directory()
    print(f"[INFO] Images will be saved to: {_save_directory}")
    print(f"[INFO] Open your browser at: http://127.0.0.1:{config.FLASK_PORT}")
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG,
        use_reloader=config.FLASK_USE_RELOADER,
    )


if __name__ == "__main__":
    main()
