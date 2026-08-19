"""Central configuration for the camera dashboard project.

All magic numbers used across the application must live here, not
scattered inside the driver or GUI code. If you need a new constant,
add it here with a short comment explaining what it controls.
"""

# --- Flask web server settings -------------------------------------------------
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = False
FLASK_USE_RELOADER = False  # must stay False, otherwise cameras get opened twice

# --- MJPEG video stream settings -----------------------------------------------
JPEG_QUALITY = 90               # 0-100, passed to cv2.imencode
MJPEG_BOUNDARY = "frame"        # multipart boundary name used by the browser stream
STREAM_IDLE_RETRY_DELAY_SECONDS = 0.2   # pause between frames when no camera is active
STREAM_ERROR_RETRY_DELAY_SECONDS = 1.0  # pause after an unexpected streaming error

# --- Generic OpenCV camera driver defaults (covers USB / webcam style cameras) -
OPENCV_DISCOVERY_MAX_INDEX = 5    # how many device indices to probe when scanning
OPENCV_FRAME_WIDTH = 640
OPENCV_FRAME_HEIGHT = 480
OPENCV_EXPOSURE_MIN = -13
OPENCV_EXPOSURE_MAX = 0
OPENCV_EXPOSURE_DEFAULT = -5
OPENCV_WARMUP_DELAY_SECONDS = 1.0   # time given to older drivers to wake up after opening
OPENCV_STREAM_FRAME_DELAY_SECONDS = 0.03  # caps the stream at roughly 30 FPS

# --- Allied Vision (vmbpy) camera driver defaults ------------------------------
ALLIEDVISION_MAX_EXPOSURE_US = 200000  # clamp, some lenses report unusable huge ranges
ALLIEDVISION_BUFFER_COUNT = 5
ALLIEDVISION_FRAME_POLL_DELAY_SECONDS = 0.03

# --- Histogram rendering --------------------------------------------------------
HISTOGRAM_HEIGHT = 150
HISTOGRAM_WIDTH = 256
HISTOGRAM_BIN_COUNT = 256

# --- Image saving ----------------------------------------------------------------
DEFAULT_SAVE_SUBDIR = "Downloads"          # fallback folder relative to the user's profile
IMAGE_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"
IMAGE_FILE_EXTENSION = ".jpg"
IMAGE_LABEL_MAX_LENGTH = 40   # user-supplied filename text is truncated to this many characters
