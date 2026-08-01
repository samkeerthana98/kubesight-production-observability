import os
import logging
import time
import uuid
from flask import Flask, Response, jsonify, render_template_string, request, g, has_request_context
import requests
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from datetime import datetime
from werkzeug.exceptions import HTTPException

# Configuration
API_SERVICE_HOST = os.environ.get('API_SERVICE_HOST', 'api')
API_SERVICE_PORT = int(os.environ.get('API_SERVICE_PORT', 5000))
API_URL = f"http://{API_SERVICE_HOST}:{API_SERVICE_PORT}"
VERSION = os.environ.get('VERSION', '1.0.0')
COMMIT_SHA = os.environ.get('COMMIT_SHA', 'local')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

# Service name for logging
SERVICE_NAME = "frontend"

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

import json
logger = logging.getLogger(SERVICE_NAME)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.handlers = [handler]

# Flask app
app = Flask(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'frontend_http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'http_status']
)
REQUEST_LATENCY = Histogram(
    'frontend_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

# Business metrics
FRONTEND_PAGE_VIEWS_TOTAL = Counter(
    'frontend_page_views_total',
    'Total Frontend Page Views',
    ['page', 'http_status']
)

# Middleware to track requests
@app.before_request
def before_request():
    g.start_time = time.time()
    # Generate or extract request ID
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
    
    # Update business metrics
    if request.endpoint:
        FRONTEND_PAGE_VIEWS_TOTAL.labels(
            page=request.endpoint,
            http_status=response.status_code
        ).inc()
    
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

@app.errorhandler(Exception)
def handle_exception(e):
    """Global error handler to ensure all errors return JSON"""
    # Log the exception
    logger.error(f"Unhandled exception: {str(e)}", exc_info=True)

    if isinstance(e, HTTPException):
        # It's an HTTP exception (like 404, 405)
        response = jsonify({
            "status": "error",
            "service": SERVICE_NAME,
            "error": e.description,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        })
        response.status_code = e.code
        return response
    else:
        # It's a non-HTTP exception
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
    try:
        # Generate request ID for outgoing call to API
        outgoing_request_id = str(uuid.uuid4())
        headers = {'X-Request-ID': outgoing_request_id}
        
        # Call the API service
        api_response = requests.get(f"{API_URL}/", headers=headers, timeout=5)
        api_response.raise_for_status()
        data = api_response.json()
        message = data.get('message', 'No message from API')
        
        # Log outgoing call
        logger.info(
            f"Outgoing call to API successful",
            extra={
                'outgoing_request_id': outgoing_request_id,
                'status': api_response.status_code
            }
        )
    except Exception as e:
        logger.error(f"Error calling API: {e}")
        message = f"Error calling API: {e}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>KubeSight Frontend</title>
    </head>
    <body>
        <h1>KubeSight Frontend</h1>
        <p>Message from API: {message}</p>
        <ul>
            <li><a href="/health">Health Check</a></li>
            <li><a href="/metrics">Metrics</a></li>
        </ul>
    </body>
    </html>
    """
    return Response(html, mimetype='text/html')

@app.route('/health')
def health():
    logger.info("Health check requested")
    # Also check if we can reach the API
    try:
        outgoing_request_id = str(uuid.uuid4())
        headers = {'X-Request-ID': outgoing_request_id}
        api_health = requests.get(f"{API_URL}/health", headers=headers, timeout=2)
        api_health.raise_for_status()
        api_status = api_health.json()
        api_status['outgoing_request_id'] = outgoing_request_id
        api_reachable = True
    except Exception as e:
        api_status = {"error": str(e)}
        api_reachable = False

    # Determine overall status
    is_healthy = api_reachable

    health_data = {
        "status": "healthy" if is_healthy else "unhealthy",
        "service": SERVICE_NAME,
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "message": "API connection healthy" if is_healthy else "API connection unhealthy",
        "api": api_status
    }

    return jsonify(health_data)

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

if __name__ == '__main__':
    # Run on all interfaces, port 5000
    app.run(host='0.0.0.0', port=5000, debug=False)
