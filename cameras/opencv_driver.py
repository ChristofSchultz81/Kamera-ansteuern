"""Generic driver for any USB webcam accessible through OpenCV's VideoCapture API.

This single driver replaces the previous ``Any_Cam_USB_WEBCAM-BROWSER.py``
and ``USB_OLDLiMi_Cam.py`` scripts: both used plain OpenCV + DirectShow,
so they are really the same camera family from the GUI's point of view.
"""

import time
from typing import List, Optional, Tuple

import cv2
import numpy as np

import config
from cameras.base import CameraDescriptor, CameraDriver


class OpenCVCameraDriver(CameraDriver):
    """Camera driver for any device reachable via cv2.VideoCapture (DirectShow backend)."""

    driver_key = "opencv_usb"

    def __init__(self) -> None:
        self._capture: Optional[cv2.VideoCapture] = None
        self._current_exposure = float(config.OPENCV_EXPOSURE_DEFAULT)

    @classmethod
    def discover(cls) -> List[CameraDescriptor]:
        # HEADER: Probes device indices 0..N and reports every index that returns a valid frame.
        descriptors: List[CameraDescriptor] = []
        for index in range(config.OPENCV_DISCOVERY_MAX_INDEX):
            capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if capture.isOpened():
                success, _ = capture.read()
                if success:
                    descriptors.append(
                        CameraDescriptor(
                            driver_key=cls.driver_key,
                            device_id=str(index),
                            display_name=f"USB Camera #{index}",
                        )
                    )
            capture.release()
        return descriptors

    def open(self, device_id: str) -> None:
        # HEADER: Opens the requested device index and applies the default resolution/exposure.
        index = int(device_id)
        self._capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.OPENCV_FRAME_WIDTH)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.OPENCV_FRAME_HEIGHT)
        time.sleep(config.OPENCV_WARMUP_DELAY_SECONDS)
        self.set_exposure(config.OPENCV_EXPOSURE_DEFAULT)

    def close(self) -> None:
        # HEADER: Releases the underlying VideoCapture device, if one is open.
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def read_frame(self) -> Optional[np.ndarray]:
        # HEADER: Reads and returns the next available frame from the open device, or None on failure.
        if self._capture is None:
            return None
        success, frame = self._capture.read()
        if not success:
            return None
        return frame

    def get_exposure_range(self) -> Tuple[float, float]:
        # HEADER: Returns the configured exposure slider range for OpenCV/DirectShow cameras.
        return float(config.OPENCV_EXPOSURE_MIN), float(config.OPENCV_EXPOSURE_MAX)

    def get_exposure(self) -> float:
        # HEADER: Returns the last exposure value applied through this driver.
        return self._current_exposure

    def set_exposure(self, value: float) -> None:
        # HEADER: Applies the given exposure value to the open camera via CAP_PROP_EXPOSURE.
        if self._capture is not None:
            self._capture.set(cv2.CAP_PROP_EXPOSURE, value)
        self._current_exposure = float(value)
