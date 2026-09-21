"""Windows 10 launcher for the Bresser MikroCam dashboard executable.

The Bresser DirectShow driver must be installed on Windows. This launcher
excludes the unrelated Allied Vision SDK so no Vimba X installation is needed.
"""

import cv2

import config

# Restrict the packaged application to Bresser/OpenCV camera access.
config.ENABLE_ALLIEDVISION_DRIVER = False
config.ENABLE_BRESSER_SDK_DRIVER = True
config.OPENCV_BACKEND = cv2.CAP_DSHOW
config.OPENCV_DISCOVERY_MAX_INDEX = 10
config.OPENCV_DISCOVERY_BACKENDS = (
    (cv2.CAP_DSHOW, "MikroCam candidate / DirectShow camera"),
    (cv2.CAP_ANY, "USB webcam"),
)
config.OPENCV_DISCOVERY_REQUIRE_FRAME = False
config.SHOW_SAVE_DIRECTORY_DIALOG = False


def main() -> None:
    # HEADER: Starts the shared dashboard after applying Bresser settings.
    from app import main as start_dashboard

    start_dashboard()


if __name__ == "__main__":
    main()
