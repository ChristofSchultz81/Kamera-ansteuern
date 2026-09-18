"""Central configuration for the camera dashboard project.

All magic numbers used across the application must live here, not
scattered inside the driver or GUI code. If you need a new constant,
add it here with a short comment explaining what it controls.
"""

# --- Flask web server settings ---
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = False
# Keep false so cameras are not opened twice by the reloader.
FLASK_USE_RELOADER = False

# --- Browser lifecycle ---
AUTO_OPEN_BROWSER = True
AUTO_OPEN_BROWSER_DELAY_SECONDS = 1.0
HEARTBEAT_INTERVAL_MS = 2000
HEARTBEAT_CHECK_INTERVAL_SECONDS = 1.0
HEARTBEAT_TIMEOUT_SECONDS = 6.0

# --- MJPEG video stream settings ---
JPEG_QUALITY = 90               # 0-100, passed to cv2.imencode
MJPEG_BOUNDARY = "frame"
STREAM_IDLE_RETRY_DELAY_SECONDS = 0.2
STREAM_ERROR_RETRY_DELAY_SECONDS = 1.0

# --- Generic OpenCV camera defaults ---
OPENCV_DISCOVERY_MAX_INDEX = 5
# CAP_ANY lets Windows select DirectShow or Media Foundation.
OPENCV_BACKEND = 0
OPENCV_FRAME_WIDTH = 640
OPENCV_FRAME_HEIGHT = 480
OPENCV_EXPOSURE_MIN = -13
OPENCV_EXPOSURE_MAX = 0
OPENCV_EXPOSURE_DEFAULT = -5
OPENCV_WARMUP_DELAY_SECONDS = 1.0
OPENCV_STREAM_FRAME_DELAY_SECONDS = 0.03

# --- Allied Vision camera defaults ---
ALLIEDVISION_MAX_EXPOSURE_US = 200000
ALLIEDVISION_BUFFER_COUNT = 5
ALLIEDVISION_FRAME_POLL_DELAY_SECONDS = 0.03

# --- Histogram rendering ---
HISTOGRAM_HEIGHT = 150
HISTOGRAM_WIDTH = 256
HISTOGRAM_BIN_COUNT = 256

# --- Saved measurement annotations ---
MEASUREMENT_COLOR_BGR = (0, 204, 255)
MEASUREMENT_TEXT_COLOR_BGR = (255, 255, 255)
MEASUREMENT_TEXT_BACKGROUND_BGR = (0, 0, 0)
MEASUREMENT_LINE_THICKNESS = 2
MEASUREMENT_POINT_RADIUS = 5
MEASUREMENT_TEXT_SCALE = 0.6
MEASUREMENT_TEXT_THICKNESS = 2
MEASUREMENT_TEXT_PADDING = 6

# --- No-signal placeholder frame ---
NO_SIGNAL_FRAME_WIDTH = 640
NO_SIGNAL_FRAME_HEIGHT = 480
NO_SIGNAL_BG_COLOR_BGR = (120, 50, 50)
NO_SIGNAL_TEXT_COLOR_BGR = (255, 255, 255)
NO_SIGNAL_MESSAGE_NO_CAMERA = "No camera selected"
NO_SIGNAL_MESSAGE_NO_FRAME = "NO SIGNAL - waiting for camera..."


# --- Image saving ---
DEFAULT_SAVE_SUBDIR = "Downloads"
IMAGE_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"
IMAGE_FILE_EXTENSION = ".jpg"
IMAGE_LABEL_MAX_LENGTH = 40
