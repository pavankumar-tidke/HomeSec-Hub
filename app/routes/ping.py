from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import asyncio
import logging
from ..services.ping_service_simple import PingService
from ..config import config

logger = logging.getLogger(__name__)
router = APIRouter()

# Global service instance
ping_service = None

def get_ping_service() -> PingService:
    """Get or create ping service instance"""
    global ping_service
    if ping_service is None:
        ping_service = PingService()
    return ping_service

# @router.get("/")
@router.get("")
async def get_ping_info() -> Dict[str, Any]:
    """
    Get ping information for hub connectivity
    
    Returns:
        Dict containing ping information including:
        - Hub to app-backend ping
        - App-backend to hub ping
        - Network latency measurements
        - MQTT device ping (real latency and status)
    """
    try:
        service = get_ping_service()
        ping_data = await service.get_ping_info()
        
        logger.info("Ping information retrieved successfully")
        return {
            "status": "success",
            "timestamp": ping_data.get("timestamp"),
            **{k: v for k, v in ping_data.items() if k != "timestamp"}
        }
        
    except Exception as e:
        logger.error(f"Failed to get ping info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ping info: {str(e)}"
        )

@router.get("/test")
async def test_ping() -> Dict[str, Any]:
    """
    Test ping connectivity to external services
    """
    try:
        service = get_ping_service()
        test_results = await service.test_ping_connectivity()
        
        return {
            "status": "success",
            "data": test_results
        }
        
    except Exception as e:
        logger.error(f"Ping test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ping test failed: {str(e)}"
        ) 