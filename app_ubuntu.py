"""Ubuntu launcher for the driver-free UVC camera dashboard.

This entry point uses the Video4Linux2 interface that Ubuntu provides for
USB Video Class (UVC) cameras. It does not require a camera-vendor SDK.
"""

import cv2

import config
from app import main

# Use Ubuntu's built-in Video4Linux2 UVC interface for generic USB cameras.
config.OPENCV_BACKEND = cv2.CAP_V4L2

if __name__ == "__main__":
    main()
