import cv2
import os
from typing import List, Dict
from ..config import Config

# Optional: Pi Camera support
try:
    from picamera2 import Picamera2
    PI_CAMERA_AVAILABLE = True
except ImportError:
    PI_CAMERA_AVAILABLE = False

# Optionally, load RTSP cameras from config/env
RTSP_CAMERAS = []  # Example: [{"id": "rtsp1", "url": "rtsp://...", "name": "Front Door", ...}]


def list_cameras() -> List[Dict]:
    cams = []
    # USB Cameras (from config)
    cams.extend(Config.CAMERAS)
    # Pi Camera (picamera2)
    if PI_CAMERA_AVAILABLE:
        try:
            picam = Picamera2()
            cam_info = picam.camera_properties
            cams.append({
                "id": "picam",
                "name": "Pi Camera",
                "type": "picamera",
                "status": "online",
                "resolution": f"{cam_info.get('PixelArrayWidth', 'N/A')}x{cam_info.get('PixelArrayHeight', 'N/A')}",
                "fps": 30,
                "device_index": None
            })
        except Exception:
            pass
    # RTSP Cameras (from config)
    for cam in RTSP_CAMERAS:
        cams.append({
            **cam,
            "type": "rtsp",
            "status": "online"
        })
    return cams 