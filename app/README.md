# Flask Health Check Web Application

A simple Flask web application with a modern UI that provides health check endpoints for Kubernetes readiness and liveness probes.

## Features

- 🌐 Clean, modern web interface
- ✅ Readiness probe endpoint (`/healthz`)
- ❤️ Liveness probe endpoint (`/failcheck`)
- 🔄 Toggle endpoints for testing health states
- 📱 Responsive design
- ⏰ Real-time status updates

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Health Check Endpoints

### Readiness Probe - `/healthz`
- **Purpose**: Indicates if the application is ready to serve traffic
- **Success Response**: HTTP 200 with JSON status
- **Failure Response**: HTTP 503 with JSON status
- **Test Toggle**: `/toggle-readiness`

### Liveness Probe - `/failcheck`
- **Purpose**: Indicates if the application is alive and healthy
- **Success Response**: HTTP 200 with JSON status  
- **Failure Response**: HTTP 500 with JSON status
- **Test Toggle**: `/toggle-liveness`

## Example Health Check Responses

### Healthy Readiness Response
```json
{
  "status": "ready",
  "timestamp": "2025-09-23T10:30:00.123456",
  "message": "Application is ready to serve traffic"
}
```

### Healthy Liveness Response
```json
{
  "status": "alive", 
  "timestamp": "2025-09-23T10:30:00.123456",
  "message": "Application is alive and healthy"
}
```

## Configuration

The application can be configured using environment variables:

- `PORT`: Server port (default: 5000)

## Docker Support

To run with Docker:

```bash
# Build the image
docker build -t flask-health-app .

# Run the container
docker run -p 5000:5000 flask-health-app
```

## Kubernetes Integration

Use these endpoints in your Kubernetes deployment:

```yaml
livenessProbe:
  httpGet:
    path: /failcheck
    port: 5000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /healthz
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 5
```
