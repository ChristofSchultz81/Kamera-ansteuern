"""Windows 11 launcher for the driver-free UVC camera dashboard.

This entry point lets OpenCV select the Windows inbox UVC backend, such as
Media Foundation or DirectShow, without a camera-vendor SDK.
"""

import cv2

import config
from app import main

# Let OpenCV select the Windows inbox UVC backend available for this camera.
config.OPENCV_BACKEND = cv2.CAP_ANY

if __name__ == "__main__":
    main()
