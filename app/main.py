from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from .mqtt_listener import MQTTListener
from .kafka_producer import KafkaProducer
from .camera_controller import CameraController
from .health import HealthMonitor
from .models import *
from .routes import healthcheck, ping, arm, camera, sensors
from .config import config
import asyncio
import logging
from datetime import datetime
from typing import Dict, List
from .routes.camera import router as camera_router
from .state import mqtt_listener as global_mqtt_listener

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Global instances
mqtt_listener = None
kafka_producer = None
camera_controller = None
health_monitor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global mqtt_listener, kafka_producer, camera_controller, health_monitor
    
    # Startup
    logger.info("Starting Raspberry Pi Hub Backend...")
    
    # Initialize components
    kafka_producer = KafkaProducer()
    await kafka_producer.start()
    
    camera_controller = CameraController(kafka_producer)
    health_monitor = HealthMonitor(kafka_producer)
    
    mqtt_listener = MQTTListener(kafka_producer, camera_controller)
    await mqtt_listener.start()
    import app.state
    app.state.mqtt_listener = mqtt_listener
    
    # Start health monitoring
    asyncio.create_task(health_monitor.start_monitoring())
    
    logger.info("Hub backend started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if mqtt_listener:
        await mqtt_listener.stop()
    if kafka_producer:
        await kafka_producer.stop()

app = FastAPI(
    title="Smart Home Security Hub",
    description="Raspberry Pi Edge Intelligence Layer",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include modular routes
app.include_router(healthcheck.router, prefix="/api/healthcheck", tags=["healthcheck"])
app.include_router(ping.router, prefix="/api/ping", tags=["ping"])
app.include_router(arm.router, prefix="/api/arm", tags=["arm"])
app.include_router(camera.router, prefix="/api/cam", tags=["cam"])
app.include_router(sensors.router, prefix="/api/sensors", tags=["sensors"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "Smart Home Security Hub"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    global health_monitor
    if health_monitor:
        return await health_monitor.get_health_status()
    return {"status": "error", "message": "Health monitor not initialized"}

@app.get("/config")
async def get_config():
    """Get current configuration"""
    return {
        "status": "success",
        "config": config.to_dict()
    }

@app.post("/trigger/camera")
async def trigger_camera(request: CameraTriggerRequest):
    """Trigger specific camera to capture photo/video"""
    global camera_controller
    if not camera_controller:
        raise HTTPException(status_code=503, detail="Camera controller not available")
    
    try:
        result = await camera_controller.trigger_camera(
            request.cam_id, 
            request.capture_type, 
            request.duration,
            request.include_audio
        )
        return result
    except Exception as e:
        logger.error(f"Camera trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/set-tamper-mode")
async def toggle_tamper_mode(request: TamperModeRequest):
    """Enable/disable tamper detection alerts"""
    global mqtt_listener
    if not mqtt_listener:
        raise HTTPException(status_code=503, detail="MQTT listener not available")
    
    try:
        await mqtt_listener.set_tamper_mode(request.active)
        return {"status": "success", "tamper_mode": request.active}
    except Exception as e:
        logger.error(f"Tamper mode toggle failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cameras")
async def list_cameras():
    """List all available cameras"""
    global camera_controller
    if not camera_controller:
        raise HTTPException(status_code=503, detail="Camera controller not available")
    
    return await camera_controller.list_cameras()

@app.get("/sensors")
async def list_sensors():
    """List all connected sensors"""
    global mqtt_listener
    if not mqtt_listener:
        raise HTTPException(status_code=503, detail="MQTT listener not available")
    
    return await mqtt_listener.list_sensors()

@app.post("/sensors/{sensor_id}/calibrate")
async def calibrate_sensor(sensor_id: str):
    """Calibrate specific sensor"""
    global mqtt_listener
    if not mqtt_listener:
        raise HTTPException(status_code=503, detail="MQTT listener not available")
    
    try:
        result = await mqtt_listener.calibrate_sensor(sensor_id)
        return result
    except Exception as e:
        logger.error(f"Sensor calibration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stream/{camera_id}")
async def get_camera_stream(camera_id: str):
    """Get camera stream URL or metadata"""
    global camera_controller
    if not camera_controller:
        raise HTTPException(status_code=503, detail="Camera controller not available")
    
    try:
        stream_info = await camera_controller.get_stream_url(camera_id)
        return stream_info
    except Exception as e:
        logger.error(f"Stream access failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/arm")
async def arm_system():
    """Arm the security system"""
    global mqtt_listener, kafka_producer
    if not mqtt_listener or not kafka_producer:
        raise HTTPException(status_code=503, detail="System not available")
    
    try:
        # Enable all sensors
        await mqtt_listener.arm_system()
        
        # Send system armed event to Kafka
        event = {
            "type": "system_armed",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Security system armed from hub"
        }
        await kafka_producer.send_event("system.status", event)
        
        return {"status": "success", "armed": True}
    except Exception as e:
        logger.error(f"System arm failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/disarm")
async def disarm_system():
    """Disarm the security system"""
    global mqtt_listener, kafka_producer
    if not mqtt_listener or not kafka_producer:
        raise HTTPException(status_code=503, detail="System not available")
    
    try:
        # Disable sensor alerts
        await mqtt_listener.disarm_system()
        
        # Send system disarmed event to Kafka
        event = {
            "type": "system_disarmed",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Security system disarmed from hub"
        }
        await kafka_producer.send_event("system.status", event)
        
        return {"status": "success", "armed": False}
    except Exception as e:
        logger.error(f"System disarm failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/config")
async def get_system_config():
    """Get current system configuration"""
    global mqtt_listener, camera_controller
    if not mqtt_listener or not camera_controller:
        raise HTTPException(status_code=503, detail="System not available")
    
    try:
        config_data = {
            "sensor_mapping": await mqtt_listener.get_sensor_mapping(),
            "camera_config": await camera_controller.get_camera_config(),
            "system_settings": {
                "arm_timeout": config.SYSTEM_ARM_TIMEOUT,
                "sensor_calibration_timeout": config.SENSOR_CALIBRATION_TIMEOUT,
                "health_check_interval": config.HEALTH_CHECK_INTERVAL
            }
        }
        return config_data
    except Exception as e:
        logger.error(f"Failed to get system config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/config/mapping")
async def update_sensor_camera_mapping(mapping: Dict[str, List[str]]):
    """Update sensor to camera mapping"""
    global mqtt_listener
    if not mqtt_listener:
        raise HTTPException(status_code=503, detail="MQTT listener not available")
    
    try:
        await mqtt_listener.update_sensor_mapping(mapping)
        return {"status": "success", "message": "Sensor mapping updated"}
    except Exception as e:
        logger.error(f"Failed to update sensor mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cameras/{camera_id}/audio")
async def toggle_camera_audio(camera_id: str, enabled: bool):
    """Toggle camera audio recording"""
    global camera_controller
    if not camera_controller:
        raise HTTPException(status_code=503, detail="Camera controller not available")
    
    try:
        result = await camera_controller.toggle_audio(camera_id, enabled)
        return result
    except Exception as e:
        logger.error(f"Camera audio toggle failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cameras/{camera_id}/test-audio")
async def test_camera_audio(camera_id: str):
    """Test camera audio recording"""
    global camera_controller
    if not camera_controller:
        raise HTTPException(status_code=503, detail="Camera controller not available")
    
    try:
        result = await camera_controller.test_audio(camera_id)
        return result
    except Exception as e:
        logger.error(f"Camera audio test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/events/active")
async def get_active_events():
    """Get currently active security events"""
    global mqtt_listener
    if not mqtt_listener:
        raise HTTPException(status_code=503, detail="MQTT listener not available")
    
    try:
        events = await mqtt_listener.get_active_events()
        return {"status": "success", "events": events}
    except Exception as e:
        logger.error(f"Failed to get active events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )