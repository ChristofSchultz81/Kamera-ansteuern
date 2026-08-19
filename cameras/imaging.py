"""Shared image processing helpers used by every camera driver and the GUI."""

from typing import Optional

import cv2
import numpy as np

import config


def create_histogram(image: np.ndarray, height: int = config.HISTOGRAM_HEIGHT) -> np.ndarray:
    # HEADER: Renders a grayscale brightness histogram of the given image, scaled to the requested height.
    if image.ndim == 3 and image.shape[2] == 1:
        gray = image[:, :, 0]
    elif image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    hist = cv2.calcHist([gray], [0], None, [config.HISTOGRAM_BIN_COUNT], [0, 256])
    cv2.normalize(hist, hist, 0, height - 1, cv2.NORM_MINMAX)

    canvas = np.zeros((height, config.HISTOGRAM_WIDTH), dtype=np.uint8)
    for i in range(1, config.HISTOGRAM_BIN_COUNT):
        y1 = int(height - 1 - hist[i - 1][0])
        y2 = int(height - 1 - hist[i][0])
        cv2.line(canvas, (i - 1, y1), (i, y2), 255, 1)

    return canvas



def ensure_bgr(image: np.ndarray) -> np.ndarray:
    # HEADER: Converts a mono (2D or single-channel) frame to 3-channel BGR; passes color frames through unchanged.
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.ndim == 3 and image.shape[2] == 1:
        return cv2.cvtColor(image[:, :, 0], cv2.COLOR_GRAY2BGR)
    return image


def encode_jpeg(image: np.ndarray) -> Optional[bytes]:
    # HEADER: Encodes a BGR image to JPEG bytes using the configured quality setting.
    success, buffer = cv2.imencode(
        ".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), config.JPEG_QUALITY]
    )
    if not success:
        return None
    return buffer.tobytes()

