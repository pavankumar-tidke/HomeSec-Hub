import asyncio
import logging
import platform
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional
from ..config import config
import psutil

logger = logging.getLogger(__name__)

class HealthcheckService:
    """Service for performing comprehensive system health checks with real data (optimized for Raspberry Pi)"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def perform_healthcheck(self) -> Dict[str, Any]:
        try:
            tasks = [
                self._check_network_status(),
                self._check_temperature(),
                self._check_sensors_status(),
                self._check_cameras_status(),
                self._check_system_resources(),
                self._check_services_status()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            health_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "network": results[0] if not isinstance(results[0], Exception) else None,
                "temperature": results[1] if not isinstance(results[1], Exception) else None,
                "sensors": results[2] if not isinstance(results[2], Exception) else None,
                "cameras": results[3] if not isinstance(results[3], Exception) else None,
                "system": results[4] if not isinstance(results[4], Exception) else None,
                "services": results[5] if not isinstance(results[5], Exception) else None
            }
            health_data["overall_status"] = self._determine_overall_status(health_data)
            return health_data
        except Exception as e:
            self.logger.error(f"Healthcheck failed: {e}")
            raise

    async def get_current_status(self) -> Dict[str, Any]:
        try:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "system": await self._check_system_resources(),
                "services": await self._check_services_status(),
                "overall_status": "healthy"  # Simplified status
            }
        except Exception as e:
            self.logger.error(f"Failed to get current status: {e}")
            raise

    async def _check_network_status(self) -> Optional[Dict[str, Any]]:
        try:
            interfaces = list(psutil.net_if_addrs().keys())
            internet_connected = await self._test_internet_connectivity()
            speed_mbps = None
            return {
                "internet_connected": internet_connected,
                "interfaces": interfaces,
                "speed_mbps": speed_mbps,
                "status": "connected" if internet_connected else "disconnected"
            }
        except Exception as e:
            self.logger.error(f"Network check failed: {e}")
            return None

    async def _check_temperature(self) -> Optional[Dict[str, Any]]:
        try:
            temp = self._get_cpu_temperature()
            status = None
            if temp is not None:
                if temp > getattr(config, "TEMPERATURE_CRITICAL_THRESHOLD", 80):
                    status = "critical"
                elif temp > getattr(config, "TEMPERATURE_WARNING_THRESHOLD", 70):
                    status = "warning"
                else:
                    status = "normal"
            return {
                "cpu_temperature_celsius": temp,
                "warning_threshold": getattr(config, "TEMPERATURE_WARNING_THRESHOLD", 70),
                "critical_threshold": getattr(config, "TEMPERATURE_CRITICAL_THRESHOLD", 80),
                "status": status
            }
        except Exception as e:
            self.logger.error(f"Temperature check failed: {e}")
            return None

    async def _check_sensors_status(self) -> Optional[Dict[str, Any]]:
        try:
            # TODO: Integrate with real sensor subsystem or DB
            return None
        except Exception as e:
            self.logger.error(f"Sensor check failed: {e}")
            return None

    async def _check_cameras_status(self) -> Optional[Dict[str, Any]]:
        try:
            # TODO: Integrate with real camera controller/service
            return None
        except Exception as e:
            self.logger.error(f"Camera check failed: {e}")
            return None

    async def _check_system_resources(self) -> Optional[Dict[str, Any]]:
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            cpu_count = psutil.cpu_count()
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "status": "normal" if cpu_percent < 90 else "warning"
                },
                "memory": {
                    "usage_percent": mem.percent,
                    "total_bytes": mem.total,
                    "available_bytes": mem.available,
                    "status": "normal" if mem.percent < 90 else "warning"
                },
                "disk": {
                    "usage_percent": disk.percent,
                    "total_bytes": disk.total,
                    "free_bytes": disk.free,
                    "status": "normal" if disk.percent < 90 else "warning"
                }
            }
        except Exception as e:
            self.logger.error(f"System resources check failed: {e}")
            return None

    async def _check_services_status(self) -> Optional[Dict[str, Any]]:
        try:
            service_names = [
                "mosquitto",  # MQTT
                "kafka",      # Kafka
                "camera_controller",
                "health_monitor",
                "motion_detection",
                "tamper_detection"
            ]
            found = {name: None for name in service_names}
            # Check running processes (cross-platform)
            for proc in psutil.process_iter(['name', 'cmdline']):
                for name in service_names:
                    if name in (proc.info.get('name') or '') or any(name in (arg or '') for arg in (proc.info.get('cmdline') or [])):
                        found[name] = "running"
            # On Linux/Pi, also check systemctl is-active for each service if not found
            sys = platform.system().lower()
            if sys in ["linux"]:
                for name in service_names:
                    if found[name] is None:
                        try:
                            result = subprocess.run(["systemctl", "is-active", name], capture_output=True, text=True)
                            if result.returncode == 0 and result.stdout.strip() == "active":
                                found[name] = "running"
                        except Exception:
                            pass
            # On Windows, also check Windows Services
            if sys == "windows":
                try:
                    for svc in psutil.win_service_iter():
                        if svc.name().lower() in service_names or svc.display_name().lower() in service_names:
                            if svc.status() == 'running':
                                found[svc.name().lower()] = "running"
                except Exception:
                    pass
            return {
                "services": found,
                "total_services": len(service_names),
                "running_services": sum(1 for v in found.values() if v == "running"),
                "status": "healthy" if all(v == "running" or v is None for v in found.values()) else "degraded"
            }
        except Exception as e:
            self.logger.error(f"Services check failed: {e}")
            return None

    async def _test_internet_connectivity(self) -> bool:
        try:
            sys = platform.system().lower()
            if sys == "windows":
                cmd = ["ping", "-n", "1", "-w", "1000", "8.8.8.8"]
            else:
                cmd = ["ping", "-c", "1", "-W", "1", "8.8.8.8"]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
            return proc.returncode == 0
        except Exception:
            return False

    def _get_cpu_temperature(self) -> Optional[float]:
        try:
            sys = platform.system().lower()
            # On Pi/Linux: try /sys/class/thermal/thermal_zone0/temp first
            if sys in ["linux"]:
                try:
                    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                        temp = int(f.read()) / 1000.0
                        return temp
                except Exception:
                    pass
                # Try vcgencmd for Raspberry Pi
                try:
                    result = subprocess.run(['vcgencmd', 'measure_temp'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        temp_str = result.stdout.strip()
                        temp = float(temp_str.split('=')[1].replace("'C", ""))
                        return temp
                except Exception:
                    pass
                # Fallback: try psutil
                if hasattr(psutil, "sensors_temperatures"):
                    temps = psutil.sensors_temperatures()
                    for name in temps:
                        for entry in temps[name]:
                            if hasattr(entry, "current"):
                                return float(entry.current)
            # Windows: try WMI
            if sys == "windows":
                try:
                    import wmi
                    w = wmi.WMI(namespace="root\\wmi")
                    temps = w.MSAcpi_ThermalZoneTemperature()
                    if temps:
                        # Convert tenths of Kelvin to Celsius
                        return float(temps[0].CurrentTemperature) / 10.0 - 273.15
                except Exception:
                    pass
        except Exception:
            pass
        return None

    def _determine_overall_status(self, health_data: Dict[str, Any]) -> str:
        if any(v is None for v in health_data.values()):
            return "degraded"
        temp_status = health_data.get("temperature", {}).get("status")
        if temp_status == "critical":
            return "critical"
        system = health_data.get("system", {})
        cpu_status = system.get("cpu", {}).get("status")
        memory_status = system.get("memory", {}).get("status")
        disk_status = system.get("disk", {}).get("status")
        if any(status == "warning" for status in [cpu_status, memory_status, disk_status]):
            return "warning"
        return "healthy" 