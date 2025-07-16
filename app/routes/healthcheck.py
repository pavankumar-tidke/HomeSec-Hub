from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import asyncio
import logging
from ..services.healthcheck_service_simple import HealthcheckService
from ..config import config

logger = logging.getLogger(__name__)
router = APIRouter()

# Global service instance
healthcheck_service = None

def get_healthcheck_service() -> HealthcheckService:
    """Get or create healthcheck service instance"""
    global healthcheck_service
    if healthcheck_service is None:
        healthcheck_service = HealthcheckService()
    return healthcheck_service

# @router.post("/")
@router.post("")
async def healthcheck() -> Dict[str, Any]:
    """
    Perform comprehensive system health check
    
    Returns:
        Dict containing system health information including:
        - Network status and speed
        - Temperature readings
        - Sensor status
        - Camera status
        - Overall system health
    """
    try:
        service = get_healthcheck_service()
        health_data = await service.perform_healthcheck()
        
        logger.info("Healthcheck completed successfully")
        return {
            "status": "success",
            "timestamp": health_data.get("timestamp"),
            "data": health_data
        }
        
    except Exception as e:
        logger.error(f"Healthcheck failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Healthcheck failed: {str(e)}"
        )

@router.get("/status")
async def get_health_status() -> Dict[str, Any]:
    """
    Get current health status without performing full check
    """
    try:
        service = get_healthcheck_service()
        status = await service.get_current_status()
        
        return {
            "status": "success",
            "data": status
        }
        
    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get health status: {str(e)}"
        ) 