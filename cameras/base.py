"""Generic camera driver interface used by the GUI.

The GUI (app.py) only ever talks to this abstract interface. To support
a new camera model:

1. Create a new module in this package (e.g. ``my_camera_driver.py``).
2. Implement a class inheriting from ``CameraDriver`` that implements
   every abstract method below.
3. Register the class in ``registry.py``.

The GUI code itself never has to change.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np


@dataclass
class CameraDescriptor:
    """Lightweight description of a discoverable camera, before it is opened."""

    driver_key: str
    device_id: str
    display_name: str


class CameraDriver(ABC):
    """Abstract base class every concrete camera driver must implement."""

    driver_key: str = "base"

    @classmethod
    @abstractmethod
    def discover(cls) -> List[CameraDescriptor]:
        # HEADER: Scans for available devices of this driver type without opening them.
        raise NotImplementedError

    @abstractmethod
    def open(self, device_id: str) -> None:
        # HEADER: Opens and initializes the given camera device for streaming.
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        # HEADER: Releases the camera device and stops any background streaming.
        raise NotImplementedError

    @abstractmethod
    def read_frame(self) -> Optional[np.ndarray]:
        # HEADER: Returns the most recent frame as a BGR numpy array, or None if unavailable.
        raise NotImplementedError

    @abstractmethod
    def get_exposure_range(self) -> Tuple[float, float]:
        # HEADER: Returns the (min, max) exposure values supported by this camera.
        raise NotImplementedError

    @abstractmethod
    def get_exposure(self) -> float:
        # HEADER: Returns the currently configured exposure value.
        raise NotImplementedError

    @abstractmethod
    def set_exposure(self, value: float) -> None:
        # HEADER: Applies a new exposure value to the live camera.
        raise NotImplementedError
