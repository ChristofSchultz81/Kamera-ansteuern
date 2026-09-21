"""Bresser MikroCam driver using the OEM SDK installed with MikroCamLabII.

MikroCamLabII cameras may be exposed as proprietary USB devices instead of
OpenCV-compatible webcams. This driver loads the installed Bresser/ToupTek SDK
and uses its pull-mode API to obtain RGB frames.
"""

import ctypes
import os
import sys
import threading
import time
from pathlib import Path
from typing import Callable, List, Optional, Tuple

import cv2
import numpy as np

import config
from cameras.base import CameraDescriptor, CameraDriver

try:
    import winreg
except ImportError:
    winreg = None


class _SdkCameraInfo(ctypes.Structure):
    """Legacy ToupTek-compatible camera descriptor returned by Enum."""

    _fields_ = [
        (
            "display_name",
            ctypes.c_char * config.BRESSER_SDK_DEVICE_NAME_MAX_LENGTH,
        ),
        (
            "device_id",
            ctypes.c_char * config.BRESSER_SDK_DEVICE_NAME_MAX_LENGTH,
        ),
        ("model", ctypes.c_void_p),
    ]


class BresserSdkCameraDriver(CameraDriver):
    """Driver for MikroCamLabII cameras exposed through an OEM SDK DLL."""

    driver_key = "bresser_sdk"

    def __init__(self) -> None:
        self._dll = None
        self._api_prefix = ""
        self._handle = None
        self._event_callback = None
        self._frame_buffer = None
        self._width = 0
        self._height = 0
        self._image_ready = threading.Event()
        self._last_pull_error_log = 0.0

    @staticmethod
    def _log(message: str) -> None:
        # HEADER: Keeps diagnostics available without a packaged-app console.
        try:
            log_path = Path(os.environ.get("TEMP", os.getcwd())) / (
                "BresserCameraDashboard.log"
            )
            with log_path.open("a", encoding="utf-8") as log_file:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                log_file.write(f"{timestamp} {message}\n")
        except OSError:
            pass

    @classmethod
    def _decode_sdk_text(cls, value: bytes) -> str:
        # HEADER: Decodes a null-terminated SDK byte string safely.
        return value.split(b"\0", maxsplit=1)[0].decode(
            "mbcs", errors="replace"
        )

    @classmethod
    def _installed_application_paths(cls) -> List[Path]:
        # HEADER: Reads MikroCamLabII paths from Windows uninstall entries.
        if winreg is None:
            return []

        paths: List[Path] = []
        uninstall_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        registry_views = (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY)
        for registry_view in registry_views:
            try:
                root = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    uninstall_key,
                    0,
                    winreg.KEY_READ | registry_view,
                )
            except OSError:
                continue
            try:
                subkey_count = winreg.QueryInfoKey(root)[0]
                for index in range(subkey_count):
                    try:
                        subkey_name = winreg.EnumKey(root, index)
                        with winreg.OpenKey(root, subkey_name) as subkey:
                            display_name = str(
                                winreg.QueryValueEx(subkey, "DisplayName")[0]
                            )
                            if not any(
                                name.casefold() in display_name.casefold()
                                for name in config.BRESSER_SDK_INSTALLER_NAMES
                            ):
                                continue
                            install_path = Path(
                                str(
                                    winreg.QueryValueEx(
                                        subkey, "InstallLocation"
                                    )[0]
                                )
                            )
                            paths.append(install_path)
                    except OSError:
                        continue
            finally:
                winreg.CloseKey(root)
        return paths

    @classmethod
    def _sdk_search_paths(cls) -> List[Path]:
        # HEADER: Builds likely locations for the installed OEM SDK DLL.
        paths: List[Path] = []
        configured_path = os.environ.get(
            config.BRESSER_SDK_ENVIRONMENT_VARIABLE
        )
        if configured_path:
            paths.append(Path(configured_path))
        paths.extend(cls._installed_application_paths())
        paths.extend(
            (
                Path.cwd(),
                Path(sys.executable).parent,
                Path(getattr(sys, "_MEIPASS", sys.executable)),
                Path(__file__).resolve().parents[1] / "driver" / "Bresser#",
            )
        )
        for environment_name in ("ProgramFiles", "ProgramFiles(x86)"):
            program_files = os.environ.get(environment_name)
            if program_files:
                paths.extend(
                    Path(program_files) / vendor
                    for vendor in config.BRESSER_SDK_INSTALLER_NAMES
                )
        return paths

    @classmethod
    def _find_sdk_dll(cls) -> Optional[Path]:
        # HEADER: Finds the Bresser or ToupTek SDK DLL from MikroCamLabII.
        for search_path in cls._sdk_search_paths():
            if search_path.is_file():
                return search_path
            for filename in config.BRESSER_SDK_DLL_FILENAMES:
                direct_path = search_path / filename
                if direct_path.is_file():
                    return direct_path
                try:
                    matches = list(search_path.rglob(filename))
                except OSError:
                    matches = []
                if matches:
                    return matches[0]
        return None

    @staticmethod
    def _api_prefix_for_dll(dll_path: Path) -> str:
        # HEADER: Maps an OEM DLL filename to its exported API prefix.
        return "Toupcam"

    @classmethod
    def _enumerate(cls) -> List[Tuple[Path, str, str, str]]:
        # HEADER: Finds cameras through the installed Bresser/ToupTek SDK.
        dll_path = cls._find_sdk_dll()
        if dll_path is None:
            return []
        try:
            dll = ctypes.WinDLL(str(dll_path))
            api_prefix = cls._api_prefix_for_dll(dll_path)
            enumerate_cameras = getattr(dll, f"{api_prefix}_Enum")
            enumerate_cameras.argtypes = (ctypes.POINTER(_SdkCameraInfo),)
            enumerate_cameras.restype = ctypes.c_uint
            cameras = (_SdkCameraInfo * config.BRESSER_SDK_MAX_CAMERA_COUNT)()
            camera_count = min(
                int(enumerate_cameras(cameras)),
                config.BRESSER_SDK_MAX_CAMERA_COUNT,
            )
        except (AttributeError, OSError):
            return []

        return [
            (
                dll_path,
                api_prefix,
                cls._decode_sdk_text(camera.display_name),
                cls._decode_sdk_text(camera.device_id),
            )
            for camera in cameras[:camera_count]
        ]

    @classmethod
    def discover(cls) -> List[CameraDescriptor]:
        # HEADER: Reports Bresser cameras found through the MikroCamLabII SDK.
        return [
            CameraDescriptor(
                driver_key=cls.driver_key,
                device_id=device_id,
                display_name=(
                    f"Bresser MikroCam SDK: {display_name or device_id}"
                ),
            )
            for _, _, display_name, device_id in cls._enumerate()
        ]

    def _function(self, suffix: str) -> Callable:
        # HEADER: Returns an SDK function using the prefix of the loaded DLL.
        return getattr(self._dll, f"{self._api_prefix}_{suffix}")

    def _on_sdk_event(self, event_code: int, context) -> None:
        # HEADER: Receives SDK notifications required by pull-mode streaming.
        if event_code == 1:
            self._image_ready.set()

    def open(self, device_id: str) -> None:
        # HEADER: Opens a Bresser camera through the OEM SDK in pull mode.
        matches = [
            item for item in self._enumerate() if item[3] == device_id
        ]
        if not matches:
            raise ValueError("Bresser MikroCam was not found through its SDK")
        dll_path, self._api_prefix, _, _ = matches[0]
        self._dll = ctypes.WinDLL(str(dll_path))

        open_camera = self._function("Open")
        open_camera.argtypes = (ctypes.c_char_p,)
        open_camera.restype = ctypes.c_void_p
        self._handle = open_camera(device_id.encode("mbcs"))
        if not self._handle:
            self._log("Open failed")
            raise RuntimeError("The Bresser SDK could not open the MikroCam")

        get_size = self._function("get_Size")
        get_size.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
        )
        get_size.restype = ctypes.c_int
        width = ctypes.c_int()
        height = ctypes.c_int()
        if get_size(
            self._handle, ctypes.byref(width), ctypes.byref(height)
        ) < 0:
            self._log("get_Size failed")
            self.close()
            raise RuntimeError("The Bresser SDK did not report an image size")
        self._width = width.value
        self._height = height.value
        self._log(f"Opened camera with size {self._width}x{self._height}")

        callback_type = ctypes.WINFUNCTYPE(
            None, ctypes.c_uint, ctypes.c_void_p
        )
        self._event_callback = callback_type(self._on_sdk_event)
        start_pull_mode = self._function("StartPullModeWithCallback")
        start_pull_mode.argtypes = (
            ctypes.c_void_p,
            callback_type,
            ctypes.c_void_p,
        )
        start_pull_mode.restype = ctypes.c_int
        start_result = start_pull_mode(
            self._handle, self._event_callback, None
        )
        self._log(f"StartPullModeWithCallback result={start_result}")
        if start_result < 0:
            self.close()
            raise RuntimeError(
                "The Bresser SDK could not start image streaming"
            )

    def close(self) -> None:
        # HEADER: Stops the OEM SDK stream and releases the camera handle.
        if self._handle:
            try:
                self._function("Close")(self._handle)
            except AttributeError:
                pass
        self._handle = None
        self._event_callback = None
        self._frame_buffer = None
        self._image_ready.clear()
        self._width = 0
        self._height = 0
        self._dll = None

    def read_frame(self) -> Optional[np.ndarray]:
        # HEADER: Pulls the latest SDK RGB frame and converts it to BGR.
        if not self._handle or self._width <= 0 or self._height <= 0:
            return None
        self._image_ready.wait(
            timeout=config.BRESSER_SDK_FRAME_WAIT_TIMEOUT_SECONDS
        )
        self._image_ready.clear()
        buffer_size = (
            self._width
            * self._height
            * (config.BRESSER_SDK_RGB_BITS_PER_PIXEL // 8)
        )
        self._frame_buffer = (ctypes.c_ubyte * buffer_size)()
        width = ctypes.c_uint(self._width)
        height = ctypes.c_uint(self._height)
        pull_image = self._function("PullImageV2")
        pull_image.argtypes = (
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint),
            ctypes.POINTER(ctypes.c_uint),
        )
        pull_image.restype = ctypes.c_int
        result = pull_image(
            self._handle,
            self._frame_buffer,
            config.BRESSER_SDK_RGB_BITS_PER_PIXEL,
            ctypes.byref(width),
            ctypes.byref(height),
        )
        if result != config.BRESSER_SDK_SUCCESS:
            now = time.monotonic()
            if now - self._last_pull_error_log >= 5.0:
                print(f"[WARNING] Bresser SDK PullImageV2 failed: {result}")
                self._log(f"PullImageV2 failed with result={result}")
                self._last_pull_error_log = now
            return None
        rgb_frame = np.ctypeslib.as_array(self._frame_buffer).reshape(
            (height.value, width.value, 3)
        )
        return cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

    def get_exposure_range(self) -> Tuple[float, float]:
        # HEADER: Returns the OEM SDK exposure range when supported.
        return (
            float(config.OPENCV_EXPOSURE_MIN),
            float(config.OPENCV_EXPOSURE_MAX),
        )

    def get_exposure(self) -> float:
        # HEADER: Returns a neutral slider value when the OEM SDK is selected.
        return float(config.OPENCV_EXPOSURE_DEFAULT)

    def set_exposure(self, value: float) -> None:
        # HEADER: Leaves exposure unchanged until its SDK API is verified.
        return None
