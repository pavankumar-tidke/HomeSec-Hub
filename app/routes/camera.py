from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from ..services.camera_manager import list_cameras
from ..services.stream_manager import start_stream, start_hls_stream, get_playlist_path, get_mjpeg_url, start_mjpeg_stream
import os
import logging


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("")
def get_cameras():
    return list_cameras()

@router.get("/{cam_id}/stream")
def stream_camera(cam_id: str, 
                 format: str = Query('hls', enum=['hls', 'rtmp', 'mjpeg']),
                 audio_device: str = Query(None, description="ALSA audio device, e.g. hw:1,0"),
                 rtmp_url: str = Query(None, description="RTMP output URL (for rtmp format)")
):
    """
    Stream camera in the requested format (hls, rtmp, mjpeg).
    - HLS: returns m3u8 playlist (browser playback)
    - RTMP: starts push to rtmp_url, returns status
    - MJPEG: not implemented
    """
    cams = list_cameras()
    cam = next((c for c in cams if c["id"] == cam_id), None)
    if not cam:
        raise HTTPException(404, "Camera not found")
    if format == 'hls':
        start_stream(cam_id, cam["type"], cam.get("device_index"), cam.get("url"), audio_device, format='hls')
        playlist = get_playlist_path(cam_id)
        if not os.path.exists(playlist):
            raise HTTPException(404, "Stream not ready")
        return FileResponse(playlist, media_type="application/vnd.apple.mpegurl")
    elif format == 'rtmp':
        if not rtmp_url:
            raise HTTPException(400, "rtmp_url is required for RTMP streaming")
        start_stream(cam_id, cam["type"], cam.get("device_index"), cam.get("url"), audio_device, format='rtmp', rtmp_url=rtmp_url)
        return JSONResponse({"status": "RTMP stream started", "rtmp_url": rtmp_url})
    elif format == 'mjpeg':
        return JSONResponse({"error": "MJPEG streaming not implemented yet"}, status_code=501)
    else:
        raise HTTPException(400, "Invalid format")

@router.get("/mjpeg/{cam_id}")
def mjpeg_stream(cam_id: str):
    cams = list_cameras()
    cam = next((c for c in cams if c["id"] == cam_id), None)
    if not cam:
        raise HTTPException(404, "Camera not found")
    # MJPEG streaming stub: return 501 Not Implemented for now
    return JSONResponse({"error": "MJPEG streaming not implemented yet"}, status_code=501) 