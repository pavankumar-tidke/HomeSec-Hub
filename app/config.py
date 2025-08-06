import os
from typing import Dict, Any
from dotenv import load_dotenv
load_dotenv()
import glob
import cv2

class Config:
    """Configuration class for hub-backend"""
    
    # Server Configuration
    HOST: str = os.getenv("HUB_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("HUB_PORT", "5000"))
    DEBUG: bool = os.getenv("HUB_DEBUG", "False").lower() == "true"
    
    # MQTT Configuration
    MQTT_BROKER: str = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_USERNAME: str = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD: str = os.getenv("MQTT_PASSWORD", "")
    MQTT_CLIENT_ID: str = os.getenv("MQTT_CLIENT_ID", "hub-backend")
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_CLIENT_ID: str = os.getenv("KAFKA_CLIENT_ID", "hub-backend")
    SENSOR_DATA_TOPIC: str = os.getenv("SENSOR_DATA_TOPIC", "sensor-data")
    SENSOR_STREAM_INTERVAL: float = float(os.getenv("SENSOR_STREAM_INTERVAL", "1.0"))  # seconds
    SENSOR_STREAM_COUNT: int = int(os.getenv("SENSOR_STREAM_COUNT", "10"))  # number of messages to send
    
    # Camera Configuration
    CAMERA_TIMEOUT: int = int(os.getenv("CAMERA_TIMEOUT", "30"))
    CAMERA_RETRY_ATTEMPTS: int = int(os.getenv("CAMERA_RETRY_ATTEMPTS", "3"))
    CAMERA_CAPTURE_PATH: str = os.getenv("CAMERA_CAPTURE_PATH", "/tmp/captures")
    
    # Health Monitoring Configuration
    HEALTH_CHECK_INTERVAL: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))
    HEALTH_CHECK_TIMEOUT: int = int(os.getenv("HEALTH_CHECK_TIMEOUT", "10"))
    TEMPERATURE_WARNING_THRESHOLD: float = float(os.getenv("TEMPERATURE_WARNING_THRESHOLD", "70.0"))
    TEMPERATURE_CRITICAL_THRESHOLD: float = float(os.getenv("TEMPERATURE_CRITICAL_THRESHOLD", "80.0"))
    
    # System Configuration
    SYSTEM_ARM_TIMEOUT: int = int(os.getenv("SYSTEM_ARM_TIMEOUT", "5"))
    SENSOR_CALIBRATION_TIMEOUT: int = int(os.getenv("SENSOR_CALIBRATION_TIMEOUT", "10"))
    
    # Network Configuration
    PING_TIMEOUT: int = int(os.getenv("PING_TIMEOUT", "5"))
    PING_COUNT: int = int(os.getenv("PING_COUNT", "3"))
    # EC2_PROXY_HOST: str = os.getenv("EC2_PROXY_HOST", "ec2-proxy-host")
    EC2_PROXY_HOST: str = '192.168.1.51'
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # MongoDB Configuration
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb+srv://pavankumartidke12345:afph7ui1gWiXZIqO@cluster0.tdjcgf5.mongodb.net/homesec")
    ARM_STATUS_COLLECTION: str = os.getenv("ARM_STATUS_COLLECTION", "arm_status")

    # Automatically detect available camera devices
    @staticmethod
    def get_available_cameras():
        devices = sorted(glob.glob('/dev/video*'))
        cameras = []
        for device in devices:
            cap = cv2.VideoCapture(device)
            if cap.isOpened():
                cameras.append({
                    "id": f"usb{len(cameras)}",
                    "type": "usb",
                    "device_index": device,
                    "name": f"Camera {len(cameras)}"
                })
                cap.release()
        return cameras

    # List of available cameras
    CAMERAS = get_available_cameras.__func__()

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert config to dictionary for API responses"""
        return {
            "server": {
                "host": cls.HOST,
                "port": cls.PORT,
                "debug": cls.DEBUG
            },
            "mqtt": {
                "broker": cls.MQTT_BROKER,
                "port": cls.MQTT_PORT,
                "client_id": cls.MQTT_CLIENT_ID
            },
            "kafka": {
                "bootstrap_servers": cls.KAFKA_BOOTSTRAP_SERVERS,
                "client_id": cls.KAFKA_CLIENT_ID
            },
            "camera": {
                "timeout": cls.CAMERA_TIMEOUT,
                "retry_attempts": cls.CAMERA_RETRY_ATTEMPTS,
                "capture_path": cls.CAMERA_CAPTURE_PATH,
                "cameras": cls.CAMERAS,
            },
            "health": {
                "check_interval": cls.HEALTH_CHECK_INTERVAL,
                "check_timeout": cls.HEALTH_CHECK_TIMEOUT,
                "temperature_warning": cls.TEMPERATURE_WARNING_THRESHOLD,
                "temperature_critical": cls.TEMPERATURE_CRITICAL_THRESHOLD
            },
            "system": {
                "arm_timeout": cls.SYSTEM_ARM_TIMEOUT,
                "sensor_calibration_timeout": cls.SENSOR_CALIBRATION_TIMEOUT
            },
            "network": {
                "ping_timeout": cls.PING_TIMEOUT,
                "ping_count": cls.PING_COUNT,
                "ec2_proxy_host": cls.EC2_PROXY_HOST
            },
            "mongodb": {
                "uri": cls.MONGO_URI,
                "arm_status_collection": cls.ARM_STATUS_COLLECTION
            }
        }

# Global config instance
config = Config() 