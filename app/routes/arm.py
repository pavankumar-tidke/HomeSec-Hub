from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import asyncio
import logging
from pydantic import BaseModel
from ..services.arm_service import set_arm_state, get_arm_state, ArmService
from ..config import config

logger = logging.getLogger(__name__)
router = APIRouter()

# Request model
class ArmRequest(BaseModel):
    arm: bool

# Global service instance
arm_service = None

def get_arm_service() -> ArmService:
    """Get or create arm service instance"""
    global arm_service
    if arm_service is None:
        arm_service = ArmService()
    return arm_service

@router.post("/")
async def arm_system(request: ArmRequest) -> Dict[str, Any]:
    """
    Arm or disarm the security system
    
    Args:
        request: ArmRequest containing boolean arm state
        
    Returns:
        Dict containing arm operation result
    """
    try:
        await set_arm_state(request.arm)
        
        return {
            "status": "success",
            "armed": request.arm,
            "timestamp": result.get("timestamp"),
            "data": result
        }
        
    except Exception as e:
        action = "arm" if request.arm else "disarm"
        logger.error(f"System {action} failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"System {action} failed: {str(e)}"
        )

@router.get("/status")
async def get_arm_status() -> Dict[str, Any]:
    """
    Get current system arm status
    """
    try:
        status = await get_arm_state()
        
        return {
            "status": "success",
            "data": status
        }
        
    except Exception as e:
        logger.error(f"Failed to get arm status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get arm status: {str(e)}"
        )

@router.post("/toggle")
async def toggle_arm_status() -> Dict[str, Any]:
    """
    Toggle the current arm status (arm if disarmed, disarm if armed)
    """
    try:
        service = get_arm_service()
        current_status = await service.get_arm_status()
        new_arm_state = not current_status.get("armed", False)
        
        if new_arm_state:
            result = await service.arm_system()
            logger.info("System armed via toggle")
        else:
            result = await service.disarm_system()
            logger.info("System disarmed via toggle")
        
        return {
            "status": "success",
            "armed": new_arm_state,
            "timestamp": result.get("timestamp"),
            "data": result
        }
        
    except Exception as e:
        logger.error(f"System toggle failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"System toggle failed: {str(e)}"
        ) 