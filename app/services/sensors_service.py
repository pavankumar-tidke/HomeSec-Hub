import asyncio
import json
import logging
from aiokafka import AIOKafkaProducer
from ..config import config

logger = logging.getLogger(__name__)

async def start_sensor_streaming():
    producer = AIOKafkaProducer(bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    try:
        for _ in range(config.SENSOR_STREAM_COUNT):
            data = {
                "sensor_id": "sensor1",
                "value": 42,  # Replace with real sensor data
                "timestamp": asyncio.get_event_loop().time()
            }
            await producer.send_and_wait(config.SENSOR_DATA_TOPIC, json.dumps(data).encode())
            logger.info(f"Sent sensor data: {data}")
            await asyncio.sleep(config.SENSOR_STREAM_INTERVAL)
    finally:
        await producer.stop() 