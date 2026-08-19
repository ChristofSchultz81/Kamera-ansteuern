"""Registry mapping driver keys to driver classes.

To add support for a new camera model, implement a new ``CameraDriver``
subclass in this package and add one line to ``DRIVER_CLASSES`` below.
No other file needs to change.
"""

from typing import Dict, List, Type

from cameras.base import CameraDescriptor, CameraDriver
from cameras.opencv_driver import OpenCVCameraDriver
from cameras.alliedvision_driver import AlliedVisionCameraDriver

DRIVER_CLASSES: Dict[str, Type[CameraDriver]] = {
    OpenCVCameraDriver.driver_key: OpenCVCameraDriver,
    AlliedVisionCameraDriver.driver_key: AlliedVisionCameraDriver,
}


def discover_all_cameras() -> List[CameraDescriptor]:
    # HEADER: Asks every registered driver class to discover its devices and merges the results.
    descriptors: List[CameraDescriptor] = []
    for driver_class in DRIVER_CLASSES.values():
        try:
            descriptors.extend(driver_class.discover())
        except Exception as error:
            print(f"[WARNING] Discovery failed for driver '{driver_class.driver_key}': {error}")
    return descriptors


def create_driver(driver_key: str) -> CameraDriver:
    # HEADER: Instantiates a fresh driver object for the given driver key.
    if driver_key not in DRIVER_CLASSES:
        raise ValueError(f"Unknown driver key: {driver_key}")
    return DRIVER_CLASSES[driver_key]()
