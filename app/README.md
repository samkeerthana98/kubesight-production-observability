# KubeSight Microservices (Phase 2) - Enhanced Observability

This directory contains the three services for the KubeSight application:
- Frontend (Flask)
- API (Flask) 
- Redis (using the official image)

All services have been enhanced with production-grade observability features including structured logging, Prometheus metrics, and incident simulation capabilities.

## Folder Structure

```
app/
├── frontend/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── api/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
└── docker-compose.yml   (for local testing)
```

## Observability Features Implemented

### 1. Structured JSON Logging
Both Flask services now use JSON-formatted logging with the following fields:
- `timestamp`: ISO 8601 timestamp in UTC
- `service`: Service name ("frontend" or "api")
- `request_id`: Unique ID for tracing requests across services
- `endpoint`: Flask endpoint being accessed
- `status`: HTTP status code of the response
- `duration`: Request processing time in seconds
- `level`: Log level (INFO, ERROR, WARNING)
- `message`: Log message

### 2. Prometheus Metrics
Each service exposes metrics at `/metrics` endpoint:

**Frontend Metrics:**
- `frontend_http_requests_total`: Counter of HTTP requests (method, endpoint, status)
- `frontend_http_request_duration_seconds`: Histogram of request latency (method, endpoint)
- `frontend_page_views_total`: Counter of page views (page, http_status)

**API Metrics:**
- `api_http_requests_total`: Counter of HTTP requests (method, endpoint, status)
- `api_http_request_duration_seconds`: Histogram of request latency (method, endpoint)
- `api_requests_total`: Counter of API requests (method, endpoint, status)
- `api_success_total`: Counter of successful requests (method, endpoint)
- `api_failed_total`: Counter of failed requests (method, endpoint)
- `redis_operations_total`: Counter of Redis operations (operation, status, key)

### 3. Incident Simulation Endpoints (API Service)
The API service includes endpoints for testing observability and alerting:
- `/simulate/error` - Returns 500 error
- `/simulate/slow` - Delays response by 2 seconds
- `/simulate/cpu` - Simulates CPU-intensive work for 1.5 seconds
- `/simulate/redis-down` - Simulates Redis connection failure

### 4. Distributed Tracing
Both services propagate `X-Request-ID` headers to enable tracing requests across service boundaries.

## Service Details

### Frontend Service (`app/frontend/`)
- **Port**: 5000 (mapped to 5001 in docker-compose)
- **Dependencies**: Flask, requests, prometheus_client, gunicorn
- **Function**: Serves a simple UI that displays a message from the API service
- **Endpoints**:
  - `GET /` - Returns HTML page with message from API
  - `GET /health` - Health check including API connectivity
  - `GET /metrics` - Prometheus metrics

### API Service (`app/api/`)
- **Port**: 5000 (mapped to 5000 in docker-compose)
- **Dependencies**: Flask, redis, prometheus_client, gunicorn
- **Function**: Provides REST API that interacts with Redis and includes observability features
- **Endpoints**:
  - `GET /` - Returns JSON with visit count from Redis
  - `GET /health` - Health check including Redis connectivity
  - `GET /metrics` - Prometheus metrics
  - **Incident Simulation**:
    - `GET /simulate/error` - Simulates error
    - `GET /simulate/slow` - Simulates slow response
    - `GET /simulate/cpu` - Simulates CPU load
    - `GET /simulate/redis-down` - Simulates Redis failure

### Redis Service
- **Image**: `redis:7-alpine`
- **Port**: 6379
- **Function**: In-memory data store used by the API service for visit counting

## Dependencies Explained

### Frontend Requirements (`frontend/requirements.txt`)
- `Flask==2.3.3`: Web framework
- `requests==2.31.0`: HTTP client for calling the API service
- `prometheus_client==0.19.0`: For exposing Prometheus metrics
- (Gunicorn is used in Dockerfile but not in requirements as it's installed via pip in Dockerfile)

### API Requirements (`api/requirements.txt`)
- `Flask==2.3.3`: Web framework
- `prometheus_client==0.19.0`: For exposing Prometheus metrics
- `redis==5.0.1`: Redis Python client
- (Gunicorn is used in Dockerfile but not in requirements as it's installed via pip in Dockerfile)

## How Services Communicate

### Frontend → API Communication
1. Frontend receives a request at `/`
2. Generates a request ID and includes it in `X-Request-ID` header
3. Makes HTTP GET request to `http://api:5000/` (using Docker service name)
4. Includes the request ID in headers for traceability
5. Processes API response and displays message in HTML
6. Logs the outgoing call with the request ID

### API → Redis Communication
1. API receives request (extracts or generates request ID)
2. On `/` endpoint: increments Redis key `visits` using `INCR` command
3. Handles Redis connection errors gracefully
4. Updates Redis operation metrics for monitoring
5. Returns visit count in JSON response

## Running Locally

### Prerequisites
- Docker and Docker Compose installed

### Build and Run
```bash
# Build all images
docker-compose build

# Start all services
docker-compose up

# Services will be available at:
# Frontend: http://localhost:5001
# API: http://localhost:5000
# Redis: localhost:6379 (not exposed externally by default)
```

### Testing Observability

1. **View Logs**: Docker-compose outputs structured JSON logs to stdout
2. **Check Metrics**:
   - Frontend: http://localhost:5001/metrics
   - API: http://localhost:5000/metrics
3. **Test Endpoints**:
   - Frontend UI: http://localhost:5001/
   - Health checks: http://localhost:5001/health and http://localhost:5000/health
   - Incident simulation: http://localhost:5000/simulate/error etc.

## Dockerfile Details

Both services use multi-stage Dockerfiles optimized for production:
- Base image: `python:3.11-slim` (minimal footprint)
- Non-root user: Runs as `appuser` for security
- Dependency installation: Uses `--no-cache-dir` to minimize image size
- Port exposure: Exposes port 5000
- Process management: Uses Gunicorn with 2 workers for production readiness

## Docker Compose Overview

The `docker-compose.yml` file defines:
- **redis**: Official Redis 7-alpine image with persistent volume
- **api**: Built from `./app/api`, depends on redis, exposes port 5000
- **frontend**: Built from `./app/frontend`, depends on api, exposes port 5001
- Environment variables configure service discovery (API_SERVICE_HOST, REDIS_HOST)

## Next Steps (Phase 3)

Upon completion of Phase 2, the next phase will involve:
1. Creating Kubernetes manifests for deployment
2. Installing Loki and Prometheus for log aggregation and metrics collection
3. Configuring Fluent Bit to collect and ship JSON logs to Loki
4. Setting up Grafana dashboards for visualization
5. Creating alerting rules based on the exposed metrics
6. Implementing distributed tracing with Jaeger or similar

STOP HERE - Do not proceed to Phase 3 without explicit confirmation.
