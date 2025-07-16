from fastapi import APIRouter, HTTPException
from ..services.sensors_service import start_sensor_streaming
from ..models import SensorInfo
import logging
import asyncio

router = APIRouter()

# Import the global mqtt_listener from state (not main)
from ..state import mqtt_listener

@router.post("/start")
async def start_sensors_stream():
    await start_sensor_streaming()
    return {"status": "streaming"}

@router.get("")
async def get_sensors():
    """
    List all sensors and their current state.
    """
    global mqtt_listener
    if not mqtt_listener:
        raise HTTPException(status_code=503, detail="MQTT listener not available")
    sensors = await mqtt_listener.list_sensors()
    return sensors

@router.get("/{sensor_id}")
async def get_sensor(sensor_id: str):
    global mqtt_listener
    if not mqtt_listener:
        raise HTTPException(status_code=503, detail="MQTT listener not available")
    sensors = await mqtt_listener.list_sensors()
    sensor = next((s for s in sensors if s.sensor_id == sensor_id), None)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor

@router.post("/{sensor_id}/calibrate")
async def calibrate_sensor(sensor_id: str):
    global mqtt_listener
    if not mqtt_listener:
        raise HTTPException(status_code=503, detail="MQTT listener not available")
    try:
        result = await mqtt_listener.calibrate_sensor(sensor_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 