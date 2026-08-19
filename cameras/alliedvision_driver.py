"""Driver for Allied Vision cameras (e.g. Alvium) using the vmbpy SDK.

vmbpy delivers frames asynchronously through a callback, so this driver
keeps the VmbSystem/camera context open for as long as the device is
selected and stores the most recent frame for ``read_frame`` to return.
"""

from typing import List, Optional, Tuple

import numpy as np

import config
from cameras.base import CameraDescriptor, CameraDriver

try:
    from vmbpy import VmbSystem, FrameStatus
except ImportError:  # vmbpy is only installed on machines with the Vimba X SDK
    VmbSystem = None
    FrameStatus = None


class AlliedVisionCameraDriver(CameraDriver):
    """Camera driver for Allied Vision cameras exposed through vmbpy."""

    driver_key = "allied_vision"

    def __init__(self) -> None:
        self._vmb_context = None
        self._cam_context = None
        self._camera = None
        self._latest_frame: Optional[np.ndarray] = None
        self._is_streaming = False

    @classmethod
    def discover(cls) -> List[CameraDescriptor]:
        # HEADER: Lists every Allied Vision camera currently reachable through vmbpy.
        if VmbSystem is None:
            return []

        descriptors: List[CameraDescriptor] = []
        with VmbSystem.get_instance() as vmb:
            for cam in vmb.get_all_cameras():
                descriptors.append(
                    CameraDescriptor(
                        driver_key=cls.driver_key,
                        device_id=cam.get_id(),
                        display_name=f"Allied Vision {cam.get_id()}",
                    )
                )
        return descriptors

    def _frame_handler(self, cam, stream, frame) -> None:
        # HEADER: vmpby callback invoked for every incoming frame; stores it and re-queues the buffer.
        if frame.get_status() == FrameStatus.Complete:
            self._latest_frame = frame.as_opencv_image().copy()
        cam.queue_frame(frame)

    def open(self, device_id: str) -> None:
        # HEADER: Opens the requested Allied Vision camera and starts asynchronous frame streaming.
        if VmbSystem is None:
            raise RuntimeError("vmbpy is not installed on this machine")

        self._vmb_context = VmbSystem.get_instance()
        self._vmb_context.__enter__()

        cams = self._vmb_context.get_all_cameras()
        matching = [cam for cam in cams if cam.get_id() == device_id]
        if not matching:
            raise ValueError(f"Allied Vision camera '{device_id}' not found")
        self._camera = matching[0]

        self._cam_context = self._camera
        self._cam_context.__enter__()

        self._camera.start_streaming(
            handler=self._frame_handler, buffer_count=config.ALLIEDVISION_BUFFER_COUNT
        )
        self._is_streaming = True

    def close(self) -> None:
        # HEADER: Stops streaming and releases the camera and VmbSystem contexts in reverse order.
        if self._is_streaming and self._camera is not None:
            self._camera.stop_streaming()
            self._is_streaming = False
        if self._cam_context is not None:
            self._cam_context.__exit__(None, None, None)
            self._cam_context = None
        if self._vmb_context is not None:
            self._vmb_context.__exit__(None, None, None)
            self._vmb_context = None
        self._camera = None
        self._latest_frame = None

    def read_frame(self) -> Optional[np.ndarray]:
        # HEADER: Returns the latest frame captured by the streaming callback, or None if none yet.
        return self._latest_frame

    def get_exposure_range(self) -> Tuple[float, float]:
        # HEADER: Reads the exposure range from the camera feature, clamped to a sane maximum.
        min_exp, max_exp = self._camera.get_feature_by_name("ExposureTime").get_range()
        if max_exp > config.ALLIEDVISION_MAX_EXPOSURE_US:
            max_exp = config.ALLIEDVISION_MAX_EXPOSURE_US
        return float(min_exp), float(max_exp)

    def get_exposure(self) -> float:
        # HEADER: Reads the current exposure time directly from the camera feature.
        return float(self._camera.get_feature_by_name("ExposureTime").get())

    def set_exposure(self, value: float) -> None:
        # HEADER: Writes a new exposure time to the camera's ExposureTime feature.
        self._camera.get_feature_by_name("ExposureTime").set(float(value))
