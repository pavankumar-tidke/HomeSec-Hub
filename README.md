# Smart Home Security Hub Backend

## Overview
This is the Raspberry Pi-based edge intelligence layer for the distributed home security system. It provides real-time monitoring, event processing, and control capabilities for cameras, sensors, and security devices.

## Architecture

### Modular Structure
```
hub-backend/
├── app/
│   ├── config.py              # Configuration management
│   ├── main.py                # FastAPI application entry point
│   ├── models.py              # Data models and schemas
│   ├── health.py              # Health monitoring service
│   ├── camera_controller.py   # Camera management
│   ├── mqtt_listener.py       # MQTT event processing
│   ├── kafka_producer.py      # Event streaming
│   ├── routes/                # Modular API routes
│   │   ├── __init__.py
│   │   ├── healthcheck.py     # Health check endpoints
│   │   ├── ping.py           # Ping/connectivity endpoints
│   │   └── arm.py            # System arm/disarm endpoints
│   └── services/              # Business logic services
│       ├── __init__.py
│       ├── healthcheck_service.py
│       ├── ping_service.py
│       └── arm_service.py
├── requirements.txt
└── start.py
```

## Configuration

The system uses a centralized configuration file (`app/config.py`) with environment variable support:

### Key Configuration Options
- **Server**: Host, port, debug mode
- **MQTT**: Broker settings, credentials
- **Kafka**: Bootstrap servers, client ID
- **Camera**: Timeout, retry attempts, capture path
- **Health**: Check intervals, temperature thresholds
- **System**: Arm timeout, sensor calibration
- **Network**: Ping timeout, ping count

### Environment Variables
```bash
# Server Configuration
HUB_HOST=0.0.0.0
HUB_PORT=5000
HUB_DEBUG=False

# MQTT Configuration
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# Health Monitoring
HEALTH_CHECK_INTERVAL=60
TEMPERATURE_WARNING_THRESHOLD=70.0
TEMPERATURE_CRITICAL_THRESHOLD=80.0

# Network Configuration
PING_TIMEOUT=5
PING_COUNT=3
```

## API Endpoints

### Health Check Endpoints
- `POST /api/healthcheck` - Comprehensive system health check
- `GET /api/healthcheck/status` - Current health status

### Ping Endpoints
- `GET /api/ping` - Network connectivity and latency information
- `GET /api/ping/test` - Test ping connectivity to various endpoints

### Arm/Disarm Endpoints
- `POST /api/arm` - Arm or disarm the security system
- `GET /api/arm/status` - Get current arm status
- `POST /api/arm/toggle` - Toggle current arm status

### Legacy Endpoints
- `GET /health` - Basic health check
- `GET /config` - Get current configuration
- `POST /system/arm` - Legacy arm endpoint
- `POST /system/disarm` - Legacy disarm endpoint

## Features

### Health Monitoring
- **Network Status**: Internet connectivity, network speed, interface status
- **Temperature Monitoring**: CPU temperature with warning/critical thresholds
- **Sensor Status**: Motion sensors, touch sensors, door sensors
- **Camera Status**: All connected cameras with resolution and last capture info
- **System Resources**: CPU, memory, disk usage
- **Service Status**: MQTT, Kafka, camera controller, health monitor

### Ping/Connectivity
- **App Backend Ping**: Latency to app-backend server
- **Internet Connectivity**: Ping to external services (8.8.8.8)
- **Local Network**: Active network interfaces and connectivity
- **Latency Measurements**: Average latency calculations

### System Arm/Disarm
- **State Management**: Track armed/disarmed state with timestamps
- **Sensor Control**: Enable/disable all security sensors
- **Motion Detection**: Enable/disable motion detection
- **Tamper Detection**: Enable/disable tamper detection
- **Camera Monitoring**: Enable/disable camera monitoring
- **Notifications**: Send arm/disarm notifications
- **Event Logging**: Log all arm/disarm events

## Setup and Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   export HUB_HOST=0.0.0.0
   export HUB_PORT=5000
   export MQTT_BROKER=localhost
   ```

3. **Run the Application**:
   ```bash
   python start.py
   ```

## Development

### Adding New Routes
1. Create a new route file in `app/routes/`
2. Create corresponding service in `app/services/`
3. Import and include the router in `main.py`

### Adding New Configuration
1. Add configuration variables to `app/config.py`
2. Use environment variables for external configuration
3. Update the `to_dict()` method for API responses

### Testing
```bash
# Test health check
curl -X POST http://localhost:5000/api/healthcheck

# Test ping
curl http://localhost:5000/api/ping

# Test arm system
curl -X POST http://localhost:5000/api/arm \
  -H "Content-Type: application/json" \
  -d '{"arm": true}'
```

## Integration with App-Backend

The hub-backend provides the following endpoints that the app-backend can call:

1. **Health Check**: `POST /api/healthcheck` - Returns comprehensive system status
2. **Ping Info**: `GET /api/ping` - Returns network connectivity information
3. **Arm System**: `POST /api/arm` - Arms or disarms the security system

## Monitoring and Logging

- **Log Level**: Configurable via `LOG_LEVEL` environment variable
- **Health Monitoring**: Automatic health checks every 60 seconds (configurable)
- **Event Logging**: All arm/disarm events are logged with timestamps
- **Error Handling**: Comprehensive error handling with detailed logging

## Scalability Features

- **Modular Architecture**: Separate routes, services, and configuration
- **Async Operations**: All I/O operations are asynchronous
- **Configuration Management**: Centralized configuration with environment variable support
- **Service Separation**: Business logic separated from API routes
- **Error Isolation**: Individual service failures don't affect other services