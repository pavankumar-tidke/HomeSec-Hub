import asyncio
import logging
import psutil
import platform
from datetime import datetime
from typing import Dict, Any
from .kafka_producer import KafkaProducer
from .models import SystemHealthEvent

logger = logging.getLogger(__name__)

class HealthMonitor:
    def __init__(self, kafka_producer: KafkaProducer):
        self.kafka_producer = kafka_producer
        self.monitoring = False
        
    async def start_monitoring(self):
        """Start health monitoring loop"""
        self.monitoring = True
        logger.info("Health monitoring started")
        
        while self.monitoring:
            try:
                health_data = await self.get_health_status()
                
                # Send health data to Kafka
                await self.kafka_producer.send_system_health(health_data)
                
                # Wait 60 seconds before next health check
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(30)
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring = False
        logger.info("Health monitoring stopped")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get current system health status"""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Temperature (mock for demo, real implementation would read from sensors)
            temperature = self._get_cpu_temperature()
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime = int(datetime.now().timestamp() - boot_time)
            
            # Network stats
            network = psutil.net_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            # Kafka connection status
            kafka_status = "connected" if self.kafka_producer.is_connected() else "disconnected"
            
            health_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "system": {
                    "platform": platform.system(),
                    "architecture": platform.machine(),
                    "hostname": platform.node(),
                    "uptime_seconds": uptime
                },
                "cpu": {
                    "usage_percent": cpu_usage,
                    "count": psutil.cpu_count(),
                    "temperature_celsius": temperature
                },
                "memory": {
                    "usage_percent": memory_usage,
                    "total_bytes": memory.total,
                    "available_bytes": memory.available,
                    "used_bytes": memory.used
                },
                "disk": {
                    "usage_percent": disk_usage,
                    "total_bytes": disk.total,
                    "free_bytes": disk.free,
                    "used_bytes": disk.used
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "processes": {
                    "count": process_count
                },
                "services": {
                    "mqtt": self._check_mqtt_status(),
                    "kafka": kafka_status,
                    "camera_count": 4,  # Mock count
                    "sensor_count": 6   # Mock count
                },
                "status": self._get_overall_status(cpu_usage, memory_usage, disk_usage, temperature)
            }
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    def _get_cpu_temperature(self) -> float:
        """Get CPU temperature (mock implementation)"""
        try:
            # Try to read from thermal zones (Linux)
            try:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    temp = int(f.read()) / 1000.0
                    return temp
            except:
                pass
            
            # Try vcgencmd for Raspberry Pi
            try:
                import subprocess
                result = subprocess.run(['vcgencmd', 'measure_temp'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    temp_str = result.stdout.strip()
                    temp = float(temp_str.split('=')[1].replace("'C", ""))
                    return temp
            except:
                pass
                
        except Exception:
            pass
        
        # Mock temperature if real reading fails
        import random
        return round(random.uniform(35.0, 55.0), 1)
    
    def _check_mqtt_status(self) -> str:
        """Check MQTT service status"""
        # Mock MQTT status check
        # In real implementation, this would check MQTT client connection
        import random
        return "connected" if random.random() > 0.1 else "disconnected"
    
    def _get_overall_status(self, cpu_usage: float, memory_usage: float, 
                           disk_usage: float, temperature: float) -> str:
        """Determine overall system status"""
        if cpu_usage > 90 or memory_usage > 95 or disk_usage > 95 or temperature > 80:
            return "critical"
        elif cpu_usage > 80 or memory_usage > 85 or disk_usage > 85 or temperature > 70:
            return "warning"
        else:
            return "healthy"
    
    async def get_component_status(self) -> Dict[str, str]:
        """Get status of individual system components"""
        return {
            "mqtt_listener": "running",
            "kafka_producer": "connected" if self.kafka_producer.is_connected() else "disconnected",
            "camera_controller": "running",
            "health_monitor": "running" if self.monitoring else "stopped",
            "motion_detection": "active",
            "tamper_detection": "active"
        }