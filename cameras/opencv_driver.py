"""Generic driver for USB webcams accessible through OpenCV.

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
    """Driver for devices reachable through ``cv2.VideoCapture``."""

    driver_key = "opencv_usb"

    def __init__(self) -> None:
        self._capture: Optional[cv2.VideoCapture] = None
        self._current_exposure = float(config.OPENCV_EXPOSURE_DEFAULT)

    @classmethod
    def discover(cls) -> List[CameraDescriptor]:
        # HEADER: Reports device indices that return a valid frame.
        descriptors: List[CameraDescriptor] = []
        for index in range(config.OPENCV_DISCOVERY_MAX_INDEX):
            capture = cv2.VideoCapture(index, config.OPENCV_BACKEND)
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
        # HEADER: Opens the device and applies default resolution and exposure.
        index = int(device_id)
        self._capture = cv2.VideoCapture(index, config.OPENCV_BACKEND)
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.OPENCV_FRAME_WIDTH)
        self._capture.set(
            cv2.CAP_PROP_FRAME_HEIGHT, config.OPENCV_FRAME_HEIGHT
        )
        time.sleep(config.OPENCV_WARMUP_DELAY_SECONDS)
        self.set_exposure(config.OPENCV_EXPOSURE_DEFAULT)

    def close(self) -> None:
        # HEADER: Releases the underlying VideoCapture device, if one is open.
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def read_frame(self) -> Optional[np.ndarray]:
        # HEADER: Reads the next frame, or returns None on failure.
        if self._capture is None:
            return None
        success, frame = self._capture.read()
        if not success:
            return None
        return frame

    def get_exposure_range(self) -> Tuple[float, float]:
        # HEADER: Returns the configured exposure slider range.
        return (
            float(config.OPENCV_EXPOSURE_MIN),
            float(config.OPENCV_EXPOSURE_MAX),
        )

    def get_exposure(self) -> float:
        # HEADER: Returns the last exposure value applied through this driver.
        return self._current_exposure

    def set_exposure(self, value: float) -> None:
        # HEADER: Applies an exposure value through OpenCV.
        if self._capture is not None:
            self._capture.set(cv2.CAP_PROP_EXPOSURE, value)
        self._current_exposure = float(value)
