import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import cv2
import numpy as np
from .kafka_producer import KafkaProducer
from .models import CameraInfo, CameraEvent
from .config import Config

logger = logging.getLogger(__name__)

class CameraController:
    def __init__(self, kafka_producer: KafkaProducer):
        self.kafka_producer = kafka_producer
        self.cameras: Dict[str, CameraInfo] = {}
        self.active_streams: Dict[str, any] = {}
        
        # Initialize cameras for your home setup
        self._initialize_cameras()
    
    def _initialize_cameras(self):
        """Initialize cameras for your home setup with USB cameras"""
        # Use auto-detected cameras from config
        for camera in Config.CAMERAS:
            self.cameras[camera["id"]] = CameraInfo(
                camera_id=camera["id"],
                name=camera.get("name", camera["id"]),
                location=camera.get("location", "Unknown"),
                status="online",
                stream_url=f"http://192.168.1.200:8000/stream/{camera['id']}",
                thumbnail_url=f"http://192.168.1.200:8000/thumbnails/{camera['id']}.jpg",
                resolution=camera.get("resolution", "Unknown"),
                last_frame=datetime.utcnow(),
                has_audio=camera.get("has_audio", False),
                audio_enabled=camera.get("has_audio", False)
            )
    
    async def trigger_camera(self, camera_id: str, capture_type: str = "photo", duration: int = 5, include_audio: bool = True) -> Dict:
        """Trigger camera to capture photo or video with optional audio"""
        try:
            if camera_id not in self.cameras:
                raise ValueError(f"Camera {camera_id} not found")
            
            camera = self.cameras[camera_id]
            
            # Simulate camera capture with audio
            logger.info(f"Triggering {capture_type} capture for camera {camera_id} (audio: {include_audio})")
            
            # Mock capture process
            await asyncio.sleep(1)  # Simulate capture time
            
            # Generate mock file URLs
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_url = None
            thumbnail_url = None
            audio_url = None
            
            if capture_type == "photo":
                file_url = f"http://192.168.1.200:8000/captures/{camera_id}/{timestamp}.jpg"
                thumbnail_url = f"http://192.168.1.200:8000/thumbnails/{camera_id}/{timestamp}_thumb.jpg"
                
                # Capture audio if enabled
                if include_audio and camera.audio_enabled:
                    audio_url = f"http://192.168.1.200:8000/audio/{camera_id}/{timestamp}.wav"
            else:
                file_url = f"http://192.168.1.200:8000/captures/{camera_id}/{timestamp}.mp4"
                thumbnail_url = f"http://192.168.1.200:8000/thumbnails/{camera_id}/{timestamp}_thumb.jpg"
                
                # Video with audio
                if include_audio and camera.audio_enabled:
                    audio_url = f"http://192.168.1.200:8000/audio/{camera_id}/{timestamp}.wav"
            
            # Create camera event
            event = CameraEvent(
                camera_id=camera_id,
                event_type="sensor_triggered",
                image_url=file_url,
                thumbnail_url=thumbnail_url,
                audio_url=audio_url,
                timestamp=datetime.utcnow(),
                metadata={
                    "capture_type": capture_type,
                    "duration": duration if capture_type == "video" else None,
                    "resolution": camera.resolution,
                    "audio_captured": audio_url is not None,
                    "triggered_by": "sensor"
                }
            )
            
            # Send to Kafka
            await self.kafka_producer.send_camera_event(
                camera_id, 
                "sensor_triggered", 
                file_url, 
                event.metadata
            )
            
            logger.info(f"Camera {camera_id} captured {capture_type} successfully (audio: {audio_url is not None})")
            
            return {
                "camera_id": camera_id,
                "capture_type": capture_type,
                "file_url": file_url,
                "thumbnail_url": thumbnail_url,
                "audio_url": audio_url,
                "timestamp": event.timestamp.isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Camera trigger failed: {e}")
            raise
    
    async def get_stream_url(self, camera_id: str) -> Dict:
        """Get camera stream URL and metadata"""
        if camera_id not in self.cameras:
            raise ValueError(f"Camera {camera_id} not found")
        
        camera = self.cameras[camera_id]
        
        # Check if camera is online
        if camera.status != "online":
            raise ValueError(f"Camera {camera_id} is {camera.status}")
        
        return {
            "camera_id": camera_id,
            "stream_url": camera.stream_url,
            "thumbnail_url": camera.thumbnail_url,
            "resolution": camera.resolution,
            "status": camera.status,
            "has_audio": camera.has_audio,
            "audio_enabled": camera.audio_enabled,
            "last_frame": camera.last_frame.isoformat() if camera.last_frame else None
        }
    
    async def list_cameras(self) -> List[CameraInfo]:
        """Get list of all cameras"""
        return list(self.cameras.values())
    
    async def start_motion_detection(self, camera_id: str) -> Dict:
        """Start motion detection for specific camera"""
        if camera_id not in self.cameras:
            raise ValueError(f"Camera {camera_id} not found")
        
        # Mock motion detection startup
        logger.info(f"Starting motion detection for camera {camera_id}")
        
        # Start background motion detection task
        asyncio.create_task(self._motion_detection_loop(camera_id))
        
        return {
            "camera_id": camera_id,
            "motion_detection": "started",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def stop_motion_detection(self, camera_id: str) -> Dict:
        """Stop motion detection for specific camera"""
        if camera_id not in self.cameras:
            raise ValueError(f"Camera {camera_id} not found")
        
        logger.info(f"Stopping motion detection for camera {camera_id}")
        
        return {
            "camera_id": camera_id,
            "motion_detection": "stopped",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _motion_detection_loop(self, camera_id: str):
        """Background motion detection simulation"""
        try:
            while camera_id in self.cameras and self.cameras[camera_id].status == "online":
                # Simulate motion detection
                import random
                if random.random() < 0.03:  # 3% chance every 30 seconds
                    logger.info(f"Motion detected on camera {camera_id}")
                    
                    # Auto-trigger capture with audio
                    capture_result = await self.trigger_camera(
                        camera_id, 
                        "photo", 
                        include_audio=self.cameras[camera_id].audio_enabled
                    )
                    
                    # Send motion event
                    event = {
                        "camera_id": camera_id,
                        "event_type": "motion_detected",
                        "image_url": capture_result["file_url"],
                        "audio_url": capture_result.get("audio_url"),
                        "confidence": random.uniform(0.7, 0.95),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    await self.kafka_producer.send_event("camera.motion.detected", event, camera_id)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except Exception as e:
            logger.error(f"Motion detection error for camera {camera_id}: {e}")
    
    async def get_camera_health(self, camera_id: str) -> Dict:
        """Get camera health status"""
        if camera_id not in self.cameras:
            raise ValueError(f"Camera {camera_id} not found")
        
        camera = self.cameras[camera_id]
        
        # Mock health check
        import random
        return {
            "camera_id": camera_id,
            "status": camera.status,
            "last_frame": camera.last_frame.isoformat() if camera.last_frame else None,
            "fps": random.randint(25, 30),
            "resolution": camera.resolution,
            "has_audio": camera.has_audio,
            "audio_enabled": camera.audio_enabled,
            "storage_used": f"{random.randint(1, 10)}GB",
            "uptime": f"{random.randint(1, 24)}h {random.randint(1, 59)}m",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def enable_audio(self, camera_id: str, enabled: bool) -> Dict:
        """Enable/disable audio capture for camera"""
        if camera_id not in self.cameras:
            raise ValueError(f"Camera {camera_id} not found")
        
        camera = self.cameras[camera_id]
        camera.audio_enabled = enabled
        
        logger.info(f"Audio {'enabled' if enabled else 'disabled'} for camera {camera_id}")
        
        return {
            "camera_id": camera_id,
            "audio_enabled": enabled,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def test_audio_capture(self, camera_id: str) -> Dict:
        """Test audio capture for camera"""
        if camera_id not in self.cameras:
            raise ValueError(f"Camera {camera_id} not found")
        
        camera = self.cameras[camera_id]
        
        if not camera.has_audio:
            raise ValueError(f"Camera {camera_id} does not have audio capability")
        
        # Simulate audio test
        logger.info(f"Testing audio capture for camera {camera_id}")
        await asyncio.sleep(2)  # Simulate test time
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        test_audio_url = f"http://192.168.1.200:8000/audio/{camera_id}/test_{timestamp}.wav"
        
        return {
            "camera_id": camera_id,
            "test_audio_url": test_audio_url,
            "audio_level": "normal",
            "timestamp": datetime.utcnow().isoformat()
        }