import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from ..config import config

logger = logging.getLogger(__name__)

class ArmService:
    """Service for managing system arm/disarm state"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._armed = False
        self._last_arm_time = None
        self._last_disarm_time = None
        self._arm_history = []
    
    async def arm_system(self) -> Dict[str, Any]:
        """
        Arm the security system
        
        Returns:
            Dict containing arm operation result
        """
        try:
            if self._armed:
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "already_armed",
                    "armed": True,
                    "message": "System is already armed"
                }
            
            # Perform arm operations
            arm_result = await self._perform_arm_operations()
            
            # Update state
            self._armed = True
            self._last_arm_time = datetime.utcnow()
            
            # Log arm event
            self._log_arm_event("armed", arm_result)
            
            return {
                "timestamp": self._last_arm_time.isoformat(),
                "status": "success",
                "armed": True,
                "message": "System armed successfully",
                "details": arm_result
            }
            
        except Exception as e:
            self.logger.error(f"System arm failed: {e}")
            raise
    
    async def disarm_system(self) -> Dict[str, Any]:
        """
        Disarm the security system
        
        Returns:
            Dict containing disarm operation result
        """
        try:
            if not self._armed:
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "already_disarmed",
                    "armed": False,
                    "message": "System is already disarmed"
                }
            
            # Perform disarm operations
            disarm_result = await self._perform_disarm_operations()
            
            # Update state
            self._armed = False
            self._last_disarm_time = datetime.utcnow()
            
            # Log disarm event
            self._log_arm_event("disarmed", disarm_result)
            
            return {
                "timestamp": self._last_disarm_time.isoformat(),
                "status": "success",
                "armed": False,
                "message": "System disarmed successfully",
                "details": disarm_result
            }
            
        except Exception as e:
            self.logger.error(f"System disarm failed: {e}")
            raise
    
    async def get_arm_status(self) -> Dict[str, Any]:
        """
        Get current system arm status
        
        Returns:
            Dict containing current arm status
        """
        try:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "armed": self._armed,
                "last_arm_time": self._last_arm_time.isoformat() if self._last_arm_time else None,
                "last_disarm_time": self._last_disarm_time.isoformat() if self._last_disarm_time else None,
                "arm_duration": self._calculate_arm_duration() if self._armed else None,
                "status": "armed" if self._armed else "disarmed"
            }
        except Exception as e:
            self.logger.error(f"Failed to get arm status: {e}")
            raise
    
    async def _perform_arm_operations(self) -> Dict[str, Any]:
        """Perform all operations required to arm the system"""
        try:
            operations = {}
            
            # Enable all sensors
            operations["sensors"] = await self._enable_sensors()
            
            # Enable motion detection
            operations["motion_detection"] = await self._enable_motion_detection()
            
            # Enable tamper detection
            operations["tamper_detection"] = await self._enable_tamper_detection()
            
            # Enable camera monitoring
            operations["camera_monitoring"] = await self._enable_camera_monitoring()
            
            # Send arm notification
            operations["notification"] = await self._send_arm_notification()
            
            return operations
            
        except Exception as e:
            self.logger.error(f"Arm operations failed: {e}")
            raise
    
    async def _perform_disarm_operations(self) -> Dict[str, Any]:
        """Perform all operations required to disarm the system"""
        try:
            operations = {}
            
            # Disable all sensors
            operations["sensors"] = await self._disable_sensors()
            
            # Disable motion detection
            operations["motion_detection"] = await self._disable_motion_detection()
            
            # Disable tamper detection
            operations["tamper_detection"] = await self._disable_tamper_detection()
            
            # Disable camera monitoring
            operations["camera_monitoring"] = await self._disable_camera_monitoring()
            
            # Send disarm notification
            operations["notification"] = await self._send_disarm_notification()
            
            return operations
            
        except Exception as e:
            self.logger.error(f"Disarm operations failed: {e}")
            raise
    
    async def _enable_sensors(self) -> Dict[str, Any]:
        """Enable all security sensors"""
        try:
            # Mock sensor enablement
            await asyncio.sleep(0.1)  # Simulate operation time
            
            return {
                "status": "success",
                "enabled_sensors": [
                    "motion_sensor_1",
                    "motion_sensor_2", 
                    "motion_sensor_3",
                    "motion_sensor_4",
                    "touch_sensor_1",
                    "touch_sensor_2",
                    "door_sensor_1",
                    "door_sensor_2",
                    "door_sensor_3"
                ],
                "total_sensors": 9
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _disable_sensors(self) -> Dict[str, Any]:
        """Disable all security sensors"""
        try:
            # Mock sensor disablement
            await asyncio.sleep(0.1)  # Simulate operation time
            
            return {
                "status": "success",
                "disabled_sensors": 9,
                "message": "All sensors disabled"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _enable_motion_detection(self) -> Dict[str, Any]:
        """Enable motion detection"""
        try:
            await asyncio.sleep(0.1)
            return {
                "status": "success",
                "motion_detection": "enabled"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _disable_motion_detection(self) -> Dict[str, Any]:
        """Disable motion detection"""
        try:
            await asyncio.sleep(0.1)
            return {
                "status": "success",
                "motion_detection": "disabled"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _enable_tamper_detection(self) -> Dict[str, Any]:
        """Enable tamper detection"""
        try:
            await asyncio.sleep(0.1)
            return {
                "status": "success",
                "tamper_detection": "enabled"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _disable_tamper_detection(self) -> Dict[str, Any]:
        """Disable tamper detection"""
        try:
            await asyncio.sleep(0.1)
            return {
                "status": "success",
                "tamper_detection": "disabled"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _enable_camera_monitoring(self) -> Dict[str, Any]:
        """Enable camera monitoring"""
        try:
            await asyncio.sleep(0.1)
            return {
                "status": "success",
                "camera_monitoring": "enabled",
                "active_cameras": 4
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _disable_camera_monitoring(self) -> Dict[str, Any]:
        """Disable camera monitoring"""
        try:
            await asyncio.sleep(0.1)
            return {
                "status": "success",
                "camera_monitoring": "disabled"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _send_arm_notification(self) -> Dict[str, Any]:
        """Send arm notification"""
        try:
            await asyncio.sleep(0.1)
            return {
                "status": "success",
                "notification": "System armed notification sent"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _send_disarm_notification(self) -> Dict[str, Any]:
        """Send disarm notification"""
        try:
            await asyncio.sleep(0.1)
            return {
                "status": "success",
                "notification": "System disarmed notification sent"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _log_arm_event(self, event_type: str, details: Dict[str, Any]):
        """Log arm/disarm event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details
        }
        self._arm_history.append(event)
        
        # Keep only last 100 events
        if len(self._arm_history) > 100:
            self._arm_history = self._arm_history[-100:]
    
    def _calculate_arm_duration(self) -> int:
        """Calculate how long the system has been armed (in seconds)"""
        if not self._armed or not self._last_arm_time:
            return 0
        
        duration = datetime.utcnow() - self._last_arm_time
        return int(duration.total_seconds()) 