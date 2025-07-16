import asyncio
import json
import logging
from typing import Dict, Any, Optional
from aiokafka import AIOKafkaProducer
from datetime import datetime

logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.bootstrap_servers = "localhost:9092"  # Change to your Kafka broker
        self.connected = False
        
    async def start(self):
        """Start Kafka producer"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                retry_backoff_ms=1000,
                request_timeout_ms=30000,
                max_batch_size=16384
            )
            
            await self.producer.start()
            self.connected = True
            logger.info("Kafka producer started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            logger.info("Running in local mode without Kafka")
            self.connected = False
    
    async def stop(self):
        """Stop Kafka producer"""
        if self.producer:
            await self.producer.stop()
            self.connected = False
            logger.info("Kafka producer stopped")
    
    async def send_event(self, topic: str, event: Dict[str, Any], key: Optional[str] = None):
        """Send event to Kafka topic"""
        try:
            if self.connected and self.producer:
                # Add timestamp if not present
                if "timestamp" not in event:
                    event["timestamp"] = datetime.utcnow().isoformat()
                
                await self.producer.send(topic, value=event, key=key)
                # logger.debug(f"Sent event to topic {topic}: {event}")
            else:
                # Log event locally when Kafka is not available
                logger.info(f"[LOCAL] Topic: {topic}, Event: {json.dumps(event, indent=2)}")
                
        except Exception as e:
            logger.error(f"Failed to send event to Kafka: {e}")
            # Fallback to local logging
            logger.info(f"[FALLBACK] Topic: {topic}, Event: {json.dumps(event, indent=2)}")
    
    async def send_sensor_event(self, sensor_id: str, sensor_type: str, value: str, location: str, metadata: Optional[Dict] = None):
        """Send sensor event to appropriate Kafka topic"""
        event = {
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "value": value,
            "location": location,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        topic_map = {
            "motion": "sensor.motion.detected",
            "tamper": "sensor.tamper.triggered",
            "door": "sensor.door.changed"
        }
        
        topic = topic_map.get(sensor_type, "sensor.general")
        await self.send_event(topic, event, key=sensor_id)
    
    async def send_camera_event(self, camera_id: str, event_type: str, image_url: Optional[str] = None, metadata: Optional[Dict] = None):
        """Send camera event to Kafka"""
        event = {
            "camera_id": camera_id,
            "event_type": event_type,
            "image_url": image_url,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        await self.send_event("camera.frame.stream", event, key=camera_id)
    
    async def send_system_health(self, health_data: Dict[str, Any]):
        """Send system health data to Kafka"""
        event = {
            "type": "health_update",
            "data": health_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_event("system.health", event)
    
    def is_connected(self) -> bool:
        """Check if Kafka producer is connected"""
        return self.connected