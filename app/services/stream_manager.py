import subprocess
import os
from typing import Optional

STREAM_DIR = "/tmp/hls"
MJPEG_DIR = "/tmp/mjpeg"

os.makedirs(STREAM_DIR, exist_ok=True)
os.makedirs(MJPEG_DIR, exist_ok=True)

def start_stream(cam_id, cam_type, device_index=None, rtsp_url=None, audio_device=None, format='hls', rtmp_url=None):
    """
    Start a streaming process for the given camera and format.
    format: 'hls', 'rtmp', 'mjpeg'
    """
    playlist = os.path.join(STREAM_DIR, f"{cam_id}.m3u8")
    if format == 'hls' and os.path.exists(playlist):
        return
    
    if cam_type == "usb":
        # device_index may be a device path (str) or int
        if isinstance(device_index, str):
            video_input = device_index
        elif isinstance(device_index, int):
            video_input = f"/dev/video{device_index}"
        else:
            return
        video_args = ["-f", "v4l2", "-i", video_input]
        audio_args = []
        if audio_device:
            audio_args = ["-f", "alsa", "-i", audio_device]
    elif cam_type == "picamera":
        # For Pi Camera, fallback to testsrc for now
        video_args = ["-f", "lavfi", "-i", "testsrc=size=640x360:rate=30"]
        audio_args = []
    elif cam_type == "rtsp":
        video_args = ["-i", rtsp_url]
        audio_args = []
    else:
        return

    if format == 'hls':
        ffmpeg_cmd = [
            "ffmpeg", *video_args, *audio_args,
            "-vf", "scale=640:360", "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
        ]
        if audio_args:
            ffmpeg_cmd += ["-c:a", "aac", "-ar", "44100", "-ac", "2"]
        ffmpeg_cmd += [
            "-f", "hls", "-hls_time", "2", "-hls_list_size", "5", "-hls_flags", "delete_segments",
            playlist
        ]
    elif format == 'rtmp':
        if not rtmp_url:
            return
        ffmpeg_cmd = [
            "ffmpeg", *video_args, *audio_args,
            "-vf", "scale=640:360", "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
        ]
        if audio_args:
            ffmpeg_cmd += ["-c:a", "aac", "-ar", "44100", "-ac", "2"]
        ffmpeg_cmd += [
            "-f", "flv", rtmp_url
        ]
    elif format == 'mjpeg':
        # MJPEG stub (video only)
        return  # Not implemented
    else:
        return
    subprocess.Popen(ffmpeg_cmd)

def start_hls_stream(cam_id, cam_type, device_index=None, rtsp_url=None, audio_device=None):
    start_stream(cam_id, cam_type, device_index, rtsp_url, audio_device, format='hls')

def get_playlist_path(cam_id):
    return os.path.join(STREAM_DIR, f"{cam_id}.m3u8")

def get_mjpeg_url(cam_id):
    return f"/mjpeg/{cam_id}"

def start_mjpeg_stream(cam_id, cam_type, device_index=None):
    # This is a stub; real implementation would use threading and a Flask/FastAPI StreamingResponse
    pass 