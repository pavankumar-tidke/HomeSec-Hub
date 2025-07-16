import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import paho.mqtt.client as mqtt
from .kafka_producer import KafkaProducer
from .models import SensorEvent, SensorInfo, SystemConfig, SecurityEvent
from .camera_controller import CameraController

logger = logging.getLogger(__name__)

class MQTTListener:
    def __init__(self, kafka_producer: KafkaProducer, camera_controller: CameraController):
        self.kafka_producer = kafka_producer
        self.camera_controller = camera_controller
        self.client = None
        self.sensors: Dict[str, SensorInfo] = {}
        self.system_config = SystemConfig()
        self.active_events: Dict[str, SecurityEvent] = {}  # Track ongoing events
        
        # MQTT Configuration
        self.mqtt_broker = "localhost"  # Change to your MQTT broker
        self.mqtt_port = 1883
        self.mqtt_topics = [
            "sensors/+/motion",      # PIR motion sensors
            "sensors/+/touch",        # Touch sensors (doors/windows)
            "sensors/+/tamper",       # Tamper detection
            "sensors/+/status",       # Sensor status updates
            "sensors/+/battery"       # Battery level updates
        ]
        
        # Initialize sensors and camera mapping
        self._initialize_sensors_and_mapping()
    
    def _initialize_sensors_and_mapping(self):
        """Initialize sensors and camera-sensor mapping for your home setup"""
        # Define your sensors based on your setup
        sensors_config = [
            # PIR Motion Sensors with ESP8266
            {
                "id": "pir_entrance_gate", 
                "type": "motion", 
                "location": "Entrance Gate",
                "assigned_cameras": ["cam_entrance_gate", "cam_garden"]
            },
            {
                "id": "pir_main_door", 
                "type": "motion", 
                "location": "Main Door",
                "assigned_cameras": ["cam_main_door", "cam_entrance_gate"]
            },
            {
                "id": "pir_garage", 
                "type": "motion", 
                "location": "Garage",
                "assigned_cameras": ["cam_garage", "cam_entrance_gate"]
            },
            {
                "id": "pir_backyard", 
                "type": "motion", 
                "location": "Backyard",
                "assigned_cameras": ["cam_backyard", "cam_garden"]
            },
            
            # Touch Sensors (for iron doors/windows)
            {
                "id": "touch_kitchen_window", 
                "type": "touch", 
                "location": "Kitchen Window",
                "assigned_cameras": ["cam_backyard", "cam_garden"]
            },
            {
                "id": "touch_main_door", 
                "type": "touch", 
                "location": "Main Door",
                "assigned_cameras": ["cam_main_door", "cam_entrance_gate"]
            },
            {
                "id": "touch_bedroom_window", 
                "type": "touch", 
                "location": "Bedroom Window",
                "assigned_cameras": ["cam_backyard", "cam_garden"]
            },
            {
                "id": "touch_garage_door", 
                "type": "touch", 
                "location": "Garage Door",
                "assigned_cameras": ["cam_garage", "cam_entrance_gate"]
            }
        ]
        
        # Initialize sensors
        for sensor_config in sensors_config:
            self.sensors[sensor_config["id"]] = SensorInfo(
                sensor_id=sensor_config["id"],
                sensor_type=sensor_config["type"],
                location=sensor_config["location"],
                status="online",
                last_seen=datetime.utcnow(),
                battery_level=85.0,
                assigned_cameras=sensor_config["assigned_cameras"]
            )
            
            # Add to system config mapping
            self.system_config.sensor_camera_mapping[sensor_config["id"]] = sensor_config["assigned_cameras"]
    
    async def start(self):
        """Start MQTT client and connect to broker"""
        try:
            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
            
            logger.info(f"Connecting to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}")
            self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.client.loop_start()
            
            # Start sensor simulation for demo
            asyncio.create_task(self._simulate_sensor_events())
            
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")
            # Continue without MQTT for demo purposes
            asyncio.create_task(self._simulate_sensor_events())
    
    async def stop(self):
        """Stop MQTT client"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            for topic in self.mqtt_topics:
                client.subscribe(topic)
                logger.info(f"Subscribed to {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker, code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        logger.warning(f"Disconnected from MQTT broker, code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Process incoming MQTT messages"""
        try:
            topic_parts = msg.topic.split('/')
            if len(topic_parts) >= 3:
                sensor_id = topic_parts[1]
                event_type = topic_parts[2]
                
                payload = json.loads(msg.payload.decode())
                asyncio.create_task(self._process_sensor_event(sensor_id, event_type, payload))
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    async def _process_sensor_event(self, sensor_id: str, event_type: str, payload: Dict):
        """Process sensor events and trigger camera captures"""
        try:
            if sensor_id not in self.sensors:
                logger.warning(f"Unknown sensor: {sensor_id}")
                return
            
            sensor = self.sensors[sensor_id]
            
            # Update sensor status
            sensor.last_seen = datetime.utcnow()
            sensor.status = "triggered"
            
            # Create sensor event
            sensor_event = SensorEvent(
                sensor_id=sensor_id,
                sensor_type=sensor.sensor_type,
                value=payload.get("value", "detected"),
                location=sensor.location,
                timestamp=datetime.utcnow(),
                metadata=payload
            )
            
            # Send to Kafka
            topic_map = {
                "motion": "sensor.motion.detected",
                "touch": "sensor.touch.triggered",
                "tamper": "sensor.tamper.triggered",
                "door": "sensor.door.changed"
            }
            
            kafka_topic = topic_map.get(event_type, "sensor.general")
            await self.kafka_producer.send_event(kafka_topic, sensor_event.dict())
            
            # Handle camera triggering if system is armed
            if self.system_config.system_armed:
                await self._handle_camera_trigger(sensor_id, sensor_event)
            
            logger.info(f"Processed {event_type} event from {sensor_id}")
            
        except Exception as e:
            logger.error(f"Error processing sensor event: {e}")
    
    async def _handle_camera_trigger(self, sensor_id: str, sensor_event: SensorEvent):
        """Handle camera triggering based on sensor activation"""
        try:
            # Get assigned cameras for this sensor
            assigned_cameras = self.system_config.sensor_camera_mapping.get(sensor_id, [])
            
            if not assigned_cameras:
                logger.warning(f"No cameras assigned to sensor {sensor_id}")
                return
            
            # Create security event
            event_id = f"event_{sensor_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            security_event = SecurityEvent(
                event_id=event_id,
                sensor_id=sensor_id,
                sensor_type=sensor_event.sensor_type,
                location=sensor_event.location,
                timestamp=sensor_event.timestamp,
                triggered_cameras=assigned_cameras,
                severity="high" if sensor_event.sensor_type in ["touch", "tamper"] else "medium"
            )
            
            # Store active event
            self.active_events[event_id] = security_event
            
            # Trigger camera captures
            captured_images = []
            audio_recording = None
            
            for camera_id in assigned_cameras:
                try:
                    # Trigger camera with audio
                    capture_result = await self.camera_controller.trigger_camera(
                        camera_id, 
                        capture_type="photo",
                        include_audio=self.system_config.audio_enabled
                    )
                    
                    if capture_result.get("file_url"):
                        captured_images.append(capture_result["file_url"])
                    
                    if capture_result.get("audio_url"):
                        audio_recording = capture_result["audio_url"]
                        
                except Exception as e:
                    logger.error(f"Failed to trigger camera {camera_id}: {e}")
            
            # Update security event with captured data
            security_event.captured_images = captured_images
            security_event.audio_recording = audio_recording
            
            # Send complete security event to Kafka
            await self.kafka_producer.send_event("security.event", security_event.dict())
            
            # Start continuous monitoring if needed
            asyncio.create_task(self._monitor_continuous_activity(event_id, sensor_id))
            
            logger.info(f"Triggered cameras for sensor {sensor_id}: {assigned_cameras}")
            
        except Exception as e:
            logger.error(f"Error handling camera trigger: {e}")
    
    async def _monitor_continuous_activity(self, event_id: str, sensor_id: str):
        """Monitor for continuous activity and trigger periodic captures"""
        try:
            start_time = datetime.utcnow()
            capture_count = 0
            
            while event_id in self.active_events:
                await asyncio.sleep(self.system_config.capture_interval)
                
                # Check if sensor is still active
                if sensor_id in self.sensors and self.sensors[sensor_id].status == "triggered":
                    # Trigger another capture
                    assigned_cameras = self.system_config.sensor_camera_mapping.get(sensor_id, [])
                    
                    for camera_id in assigned_cameras:
                        try:
                            capture_result = await self.camera_controller.trigger_camera(
                                camera_id, 
                                capture_type="photo",
                                include_audio=self.system_config.audio_enabled
                            )
                            
                            if capture_result.get("file_url"):
                                self.active_events[event_id].captured_images.append(capture_result["file_url"])
                            
                            capture_count += 1
                            
                        except Exception as e:
                            logger.error(f"Continuous capture failed for camera {camera_id}: {e}")
                    
                    # Send update to Kafka
                    await self.kafka_producer.send_event("security.event.update", {
                        "event_id": event_id,
                        "capture_count": capture_count,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    logger.info(f"Continuous capture #{capture_count} for event {event_id}")
                else:
                    # Sensor is no longer active, stop monitoring
                    break
            
            # Clean up event after monitoring
            if event_id in self.active_events:
                del self.active_events[event_id]
                
        except Exception as e:
            logger.error(f"Error in continuous activity monitoring: {e}")
    
    async def _simulate_sensor_events(self):
        """Simulate sensor events for demonstration"""
        while True:
            try:
                if self.system_config.system_armed:
                    # Simulate random sensor events
                    import random
                    if random.random() < 0.05:  # 5% chance every 30 seconds
                        sensor_ids = list(self.sensors.keys())
                        sensor_id = random.choice(sensor_ids)
                        sensor = self.sensors[sensor_id]
                        
                        event_data = {
                            "value": "detected" if sensor.sensor_type == "motion" else "triggered",
                            "strength": random.randint(60, 100),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
                        await self._process_sensor_event(sensor_id, sensor.sensor_type, event_data)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in sensor simulation: {e}")
                await asyncio.sleep(5)
    
    async def set_tamper_mode(self, active: bool):
        """Enable/disable tamper detection"""
        self.system_config.audio_enabled = active  # Use audio for tamper detection
        logger.info(f"Tamper mode {'enabled' if active else 'disabled'}")
    
    async def arm_system(self):
        """Arm the security system"""
        self.system_config.system_armed = True
        logger.info("Security system armed")
        
        # Send system armed event
        event = {
            "type": "system_armed",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Security system armed via hub"
        }
        await self.kafka_producer.send_event("system.status", event)
    
    async def disarm_system(self):
        """Disarm the security system"""
        self.system_config.system_armed = False
        logger.info("Security system disarmed")
        
        # Reset all sensor statuses
        for sensor in self.sensors.values():
            sensor.status = "online"
        
        # Clear active events
        self.active_events.clear()
        
        # Send system disarmed event
        event = {
            "type": "system_disarmed",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Security system disarmed via hub"
        }
        await self.kafka_producer.send_event("system.status", event)
    
    async def list_sensors(self) -> List[SensorInfo]:
        """Get list of all sensors"""
        return list(self.sensors.values())
    
    async def calibrate_sensor(self, sensor_id: str) -> Dict:
        """Calibrate a specific sensor"""
        if sensor_id not in self.sensors:
            raise ValueError(f"Sensor {sensor_id} not found")
        
        # Mock calibration process
        logger.info(f"Calibrating sensor {sensor_id}")
        await asyncio.sleep(2)  # Simulate calibration time
        
        return {
            "sensor_id": sensor_id,
            "status": "calibrated",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_system_config(self) -> SystemConfig:
        """Get current system configuration"""
        return self.system_config
    
    async def update_sensor_camera_mapping(self, mapping: Dict[str, List[str]]):
        """Update sensor-camera mapping"""
        self.system_config.sensor_camera_mapping.update(mapping)
        logger.info(f"Updated sensor-camera mapping: {mapping}")