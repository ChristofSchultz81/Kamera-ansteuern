"""Shared image processing helpers used by every camera driver and the GUI."""

from typing import Optional

import cv2
import numpy as np

import config


def create_histogram(
    image: np.ndarray, height: int = config.HISTOGRAM_HEIGHT
) -> np.ndarray:
    # HEADER: Renders a grayscale histogram at the requested height.
    if image.ndim == 3 and image.shape[2] == 1:
        gray = image[:, :, 0]
    elif image.ndim == 3 and image.shape[2] == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif image.ndim == 3 and image.shape[2] == 4:
        gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    else:
        gray = image

    hist = cv2.calcHist(
        [gray], [0], None, [config.HISTOGRAM_BIN_COUNT], [0, 256]
    )
    cv2.normalize(hist, hist, 0, height - 1, cv2.NORM_MINMAX)

    canvas = np.zeros((height, config.HISTOGRAM_WIDTH), dtype=np.uint8)
    for i in range(1, config.HISTOGRAM_BIN_COUNT):
        y1 = int(height - 1 - hist[i - 1][0])
        y2 = int(height - 1 - hist[i][0])
        cv2.line(canvas, (i - 1, y1), (i, y2), 255, 1)

    return canvas


def ensure_bgr(image: np.ndarray) -> np.ndarray:
    # HEADER: Converts mono frames to BGR and passes color frames through.
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.ndim == 3 and image.shape[2] == 1:
        return cv2.cvtColor(image[:, :, 0], cv2.COLOR_GRAY2BGR)
    if image.ndim == 3 and image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return image


def draw_measurements(
    image: np.ndarray, measurements: list[dict]
) -> np.ndarray:
    # HEADER: Draws validated measurements onto a frame copy.
    annotated = ensure_bgr(image).copy()
    image_height, image_width = annotated.shape[:2]

    for index, measurement in enumerate(measurements):
        try:
            first = measurement["first"]
            second = measurement["second"]
            first_x = float(first["nativeX"])
            first_y = float(first["nativeY"])
            second_x = float(second["nativeX"])
            second_y = float(second["nativeY"])
        except (KeyError, TypeError, ValueError):
            continue

        coordinates = (first_x, first_y, second_x, second_y)
        if not all(np.isfinite(value) for value in coordinates):
            continue
        if not all(
            0 <= coordinate < limit
            for coordinate, limit in (
                (first_x, image_width),
                (second_x, image_width),
                (first_y, image_height),
                (second_y, image_height),
            )
        ):
            continue

        first_point = (round(first_x), round(first_y))
        second_point = (round(second_x), round(second_y))
        cv2.line(
            annotated,
            first_point,
            second_point,
            config.MEASUREMENT_COLOR_BGR,
            config.MEASUREMENT_LINE_THICKNESS,
        )
        for point in (first_point, second_point):
            cv2.circle(
                annotated,
                point,
                config.MEASUREMENT_POINT_RADIUS,
                config.MEASUREMENT_COLOR_BGR,
                -1,
            )

        distance = float(np.hypot(second_x - first_x, second_y - first_y))
        label = f"#{index + 1}: {distance:.2f} px"
        text_size, baseline = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            config.MEASUREMENT_TEXT_SCALE,
            config.MEASUREMENT_TEXT_THICKNESS,
        )
        middle_x = round((first_x + second_x) / 2)
        middle_y = round((first_y + second_y) / 2)
        label_x = min(
            max(middle_x, config.MEASUREMENT_TEXT_PADDING),
            image_width - text_size[0] - config.MEASUREMENT_TEXT_PADDING,
        )
        label_y = min(
            max(middle_y, text_size[1] + config.MEASUREMENT_TEXT_PADDING),
            image_height - baseline - config.MEASUREMENT_TEXT_PADDING,
        )
        background_top_left = (
            label_x - config.MEASUREMENT_TEXT_PADDING,
            label_y - text_size[1] - config.MEASUREMENT_TEXT_PADDING,
        )
        background_bottom_right = (
            label_x + text_size[0] + config.MEASUREMENT_TEXT_PADDING,
            label_y + baseline + config.MEASUREMENT_TEXT_PADDING,
        )
        cv2.rectangle(
            annotated,
            background_top_left,
            background_bottom_right,
            config.MEASUREMENT_TEXT_BACKGROUND_BGR,
            -1,
        )
        cv2.putText(
            annotated,
            label,
            (label_x, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            config.MEASUREMENT_TEXT_SCALE,
            config.MEASUREMENT_TEXT_COLOR_BGR,
            config.MEASUREMENT_TEXT_THICKNESS,
            cv2.LINE_AA,
        )

    return annotated


def create_no_signal_frame(message: str) -> np.ndarray:
    # HEADER: Builds a BGR placeholder with a status message.
    frame = np.zeros(
        (config.NO_SIGNAL_FRAME_HEIGHT, config.NO_SIGNAL_FRAME_WIDTH, 3),
        dtype=np.uint8,
    )
    frame[:] = config.NO_SIGNAL_BG_COLOR_BGR
    cv2.putText(
        frame, message, (40, config.NO_SIGNAL_FRAME_HEIGHT // 2),
        cv2.FONT_HERSHEY_SIMPLEX, 1.0, config.NO_SIGNAL_TEXT_COLOR_BGR, 2,
    )
    return frame


def encode_jpeg(image: np.ndarray) -> Optional[bytes]:
    # HEADER: Encodes a BGR image to JPEG with the configured quality.
    success, buffer = cv2.imencode(
        ".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), config.JPEG_QUALITY]
    )
    if not success:
        return None
    return buffer.tobytes()
