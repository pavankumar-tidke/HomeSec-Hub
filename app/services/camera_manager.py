import cv2
import os
from typing import List, Dict

# Optional: Pi Camera support
try:
    from picamera2 import Picamera2
    PI_CAMERA_AVAILABLE = True
except ImportError:
    PI_CAMERA_AVAILABLE = False

# Optionally, load RTSP cameras from config/env
RTSP_CAMERAS = []  # Example: [{"id": "rtsp1", "url": "rtsp://...", "name": "Front Door", ...}]


def list_cameras(max_cams=5) -> List[Dict]:
    cams = []
    # USB Cameras (OpenCV)
    for i in range(max_cams):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
            cams.append({
                "id": f"usb{i}",
                "name": f"USB Camera {i}",
                "type": "usb",
                "status": "online",
                "resolution": f"{width}x{height}",
                "fps": fps,
                "device_index": i
            })
            cap.release()
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