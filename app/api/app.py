import os
import logging
import time
import uuid
import json
from flask import Flask, Response, jsonify, request, g, has_request_context
from werkzeug.exceptions import HTTPException
import redis
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from datetime import datetime

# Configuration
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
VERSION = os.environ.get('VERSION', '1.0.0')
COMMIT_SHA = os.environ.get('COMMIT_SHA', 'local')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

# Service name for logging
SERVICE_NAME = "api"

# Logging setup - JSON format
class JsonFormatter(logging.Formatter):
    def format(self, record):
        # If we are in a request context, use g, otherwise use defaults
        if has_request_context():
            timestamp = getattr(g, 'timestamp', datetime.utcnow().isoformat() + 'Z')
            service = getattr(g, 'service', SERVICE_NAME)
            request_id = getattr(g, 'request_id', None)
            endpoint = getattr(g, 'endpoint', None)
            status = getattr(g, 'status', None)
            duration = getattr(g, 'duration', None)
        else:
            timestamp = datetime.utcnow().isoformat() + 'Z'
            service = SERVICE_NAME
            request_id = None
            endpoint = None
            status = None
            duration = None

        log_entry = {
            "timestamp": timestamp,
            "service": service,
            "request_id": request_id,
            "endpoint": endpoint,
            "status": status,
            "duration": duration,
            "level": record.levelname,
            "message": record.getMessage()
        }
        # Remove None values
        log_entry = {k: v for k, v in log_entry.items() if v is not None}
        return json.dumps(log_entry)

logger = logging.getLogger(SERVICE_NAME)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.handlers = [handler]

# Flask app
app = Flask(__name__)

# Redis connection
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, socket_connect_timeout=2)
    redis_client.ping()
    logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    # We'll let the app start but Redis operations will fail
    redis_client = None

# Prometheus metrics
REQUEST_COUNT = Counter(
    'api_http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'http_status']
)
REQUEST_LATENCY = Histogram(
    'api_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

REDIS_OPERATIONS_TOTAL = Counter(
    'redis_operations_total',
    'Total Redis Operations',
    ['operation', 'status', 'key']
)

# Middleware to track requests
@app.before_request
def before_request():
    g.start_time = time.time()
    # Extract or generate request ID (from header or new)
    g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    g.service = SERVICE_NAME
    g.endpoint = request.endpoint
    g.timestamp = datetime.utcnow().isoformat() + 'Z'

@app.after_request
def after_request(response):
    # Calculate duration
    g.duration = time.time() - g.start_time
    g.status = response.status_code

    # Update Prometheus metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint,
        http_status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.endpoint
    ).observe(g.duration)

    # Log the request
    logger.info(
        f"Request completed: {request.method} {request.path}",
        extra={
            'status': response.status_code,
            'duration': g.duration
        }
    )

    return response

@app.teardown_request
def teardown_request(exception=None):
    if exception:
        g.duration = time.time() - g.start_time
        g.status = 500
        logger.error(
            f"Request failed: {request.method} {request.path} - {str(exception)}",
            exc_info=True
        )

def update_redis_metrics(operation, status, key=None):
    """Update Redis operations metrics"""
    key_label = key if key else "unknown"
    REDIS_OPERATIONS_TOTAL.labels(
        operation=operation,
        status=status,
        key=key_label
    ).inc()

@app.errorhandler(Exception)
def handle_exception(e):
    """Global error handler to ensure all errors return JSON"""
    # Log the exception
    logger.error(f"Unhandled exception: {str(e)}", exc_info=True)

    # If it's an HTTPException, we want to return the same code but as JSON
    if isinstance(e, HTTPException):
        response = jsonify({
            "status": "error",
            "service": SERVICE_NAME,
            "error": e.description,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        })
        response.status_code = e.code
        return response

    # Otherwise, it's a non-HTTP exception, return 500
    response = jsonify({
        "status": "error",
        "service": SERVICE_NAME,
        "error": str(e),
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    })
    response.status_code = 500
    return response

@app.route('/')
def index():
    logger.info("Request received for '/'")
    # Store a counter in Redis and retrieve it
    visits = 0
    redis_status = "disconnected"
    
    if redis_client:
        try:
            visits = redis_client.incr('visits')
            redis_status = "connected"
            update_redis_metrics("incr", "success", "visits")
        except Exception as e:
            logger.error(f"Error incrementing Redis counter: {e}")
            redis_status = f"error: {e}"
            update_redis_metrics("incr", "error", "visits")
    else:
        redis_status = "not_initialized"
    
    message = f"Hello! This page has been visited {visits} times."
    
    response_data = {
        "message": message,
        "service": SERVICE_NAME,
        "visits": visits,
        "redis_status": redis_status,
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }
    
    return jsonify(response_data)

@app.route('/health')
def health():
    logger.info("Health check requested")
    # Check Redis connection
    redis_status = "disconnected"
    redis_error = None

    if redis_client:
        try:
            redis_client.ping()
            redis_status = "connected"
            update_redis_metrics("ping", "success", "connection")
        except Exception as e:
            redis_status = f"disconnected: {e}"
            redis_error = str(e)
            update_redis_metrics("ping", "error", "connection")
            logger.error(f"Redis health check failed: {e}")
    else:
        redis_status = "not_initialized"
        update_redis_metrics("ping", "error", "connection")

    # Determine overall status
    is_healthy = redis_status == "connected"

    health_data = {
        "status": "healthy" if is_healthy else "unhealthy",
        "service": SERVICE_NAME,
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "message": "Redis connection healthy" if is_healthy else "Redis connection unhealthy",
        "redis": {
            "status": redis_status,
            "error": redis_error
        }
    }

    status_code = 200 if is_healthy else 503
    return jsonify(health_data), status_code

@app.route('/metrics')
def metrics():
    logger.info("Metrics endpoint accessed")
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/version')
def version():
    version_data = {
        "service": SERVICE_NAME,
        "version": VERSION,
        "commit": COMMIT_SHA,
        "environment": ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }
    logger.info("Version endpoint accessed")
    return jsonify(version_data)

# Incident simulation endpoints
@app.route('/simulate/error')
def simulate_error():
    logger.error("Simulated error endpoint called")
    # Simulate an error
    raise Exception("This is a simulated error for testing")

@app.route('/simulate/slow')
def simulate_slow():
    logger.info("Simulated slow endpoint called")
    # Simulate slow response
    time.sleep(2)  # 2 seconds delay
    return jsonify({
        "message": "Slow response completed",
        "service": SERVICE_NAME,
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    })

@app.route('/simulate/cpu')
def simulate_cpu():
    logger.info("Simulated CPU load endpoint called")
    # Simulate CPU-intensive work
    start = time.time()
    while time.time() - start < 1.5:  # 1.5 seconds of CPU work
        # Perform some computation
        _ = [x * x for x in range(1000)]
    return jsonify({
        "message": "CPU simulation completed",
        "service": SERVICE_NAME,
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    })

@app.route('/simulate/redis-down')
def simulate_redis_down():
    logger.warning("Simulated Redis down endpoint called")
    # Simulate Redis failure by raising a connection error
    try:
        # Intentionalmente causar un fallo de conexión a Redis
        raise redis.ConnectionError("Redis connection failed - simulated")
    except redis.ConnectionError as e:
        logger.error(f"Redis connection failed: {e}")
        # Actualizar métricas de falla de Redis
        update_redis_metrics("ping", "error", "connection")
        # Retornar error 500 con formato consistente
        return jsonify({
            "status": "error",
            "service": SERVICE_NAME,
            "error": "Redis unavailable",
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }), 500
    except Exception as e:
        # Capturar cualquier otro error inesperado
        logger.error(f"Unexpected error in Redis simulation: {e}")
        return jsonify({
            "status": "error",
            "service": SERVICE_NAME,
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }), 500

if __name__ == '__main__':
    # Run the app on all interfaces for Docker
    app.run(host='0.0.0.0', port=5000, debug=False)
