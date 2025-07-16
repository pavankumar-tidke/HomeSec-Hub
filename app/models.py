from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class CameraTriggerRequest(BaseModel):
    cam_id: str
    capture_type: Optional[str] = "photo"  # "photo" or "video"
    duration: Optional[int] = 5  # for video capture
    include_audio: Optional[bool] = True  # for audio capture

class TamperModeRequest(BaseModel):
    active: bool

class SensorEvent(BaseModel):
    sensor_id: str
    sensor_type: str  # "motion", "tamper", "touch", "door"
    value: str  # "detected", "triggered", "open", "closed"
    location: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class CameraEvent(BaseModel):
    camera_id: str
    event_type: str  # "motion_detected", "manual_trigger", "stream_start", "sensor_triggered"
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    audio_url: Optional[str] = None  # for audio recordings
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class SystemHealthEvent(BaseModel):
    cpu_usage: float
    memory_usage: float
    temperature: float
    uptime: int
    mqtt_status: str
    kafka_status: str
    camera_count: int
    sensor_count: int
    timestamp: datetime

class SensorInfo(BaseModel):
    sensor_id: str
    sensor_type: str  # "motion", "tamper", "touch", "door"
    location: str
    status: str  # "online", "offline", "triggered"
    last_seen: datetime
    battery_level: Optional[float] = None
    assigned_cameras: List[str] = []  # cameras that trigger when this sensor activates

class CameraInfo(BaseModel):
    camera_id: str
    name: str
    location: str
    status: str  # "online", "offline", "streaming"
    stream_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    resolution: Optional[str] = None
    last_frame: Optional[datetime] = None
    has_audio: bool = True  # USB cameras have built-in microphones
    audio_enabled: bool = True

class SystemConfig(BaseModel):
    """System configuration for camera-sensor mapping"""
    sensor_camera_mapping: Dict[str, List[str]] = {}  # sensor_id -> [camera_ids]
    capture_interval: int = 120  # seconds between captures during continuous detection
    audio_enabled: bool = True
    system_armed: bool = False

class SecurityEvent(BaseModel):
    """Complete security event with sensor and camera data"""
    event_id: str
    sensor_id: str
    sensor_type: str
    location: str
    timestamp: datetime
    triggered_cameras: List[str] = []
    captured_images: List[str] = []
    audio_recording: Optional[str] = None
    severity: str = "medium"  # "low", "medium", "high"
    status: str = "active"  # "active", "resolved", "false_alarm"