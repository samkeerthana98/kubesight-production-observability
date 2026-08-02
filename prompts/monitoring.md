# Monitoring & Observability Prompts

Prompts used during the design and implementation of the KubeSight observability stack.

---

## Observability Stack Design

```
Design a complete observability stack for a production Kubernetes application
using kube-prometheus-stack (Prometheus Operator + Grafana + AlertManager).

Application: KubeSight (Python Flask API + Frontend + Redis on Kind cluster)

Requirements:
1. Custom application metrics via prometheus_client (Counters, Histograms)
2. Automatic Prometheus scraping via ServiceMonitor CRDs
3. Alert rules via PrometheusRule CRDs
4. Grafana dashboard auto-provisioned via ConfigMap sidecar

Namespace layout:
- kubesight: application pods + ServiceMonitors + PrometheusRule (Helm release)
- monitoring: kube-prometheus-stack (Prometheus, Grafana, AlertManager) + Grafana dashboard ConfigMap

Label convention for Prometheus discovery:
  ServiceMonitor must have: release: kube-prometheus-stack
```

---

## kube-prometheus-stack Installation

```
Helm install command for kube-prometheus-stack:

helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.sidecar.dashboards.enabled=true \
  --set grafana.sidecar.dashboards.label=grafana_dashboard

Flags explained:
- grafana.sidecar.dashboards.enabled=true: starts the sidecar container that
  watches for ConfigMaps and auto-provisions dashboards
- grafana.sidecar.dashboards.label=grafana_dashboard: label key the sidecar
  watches for (must match the label on the KubeSight dashboard ConfigMap)
```

---

## JSON Structured Logging in Flask

```
Implement structured JSON logging in a Python Flask application.

Requirements:
- Custom logging.Formatter subclass (JsonFormatter) that outputs JSON strings
- Fields: timestamp, service, request_id, endpoint, status, duration, level, message
- Use has_request_context() to safely access Flask g outside request context
- Generate or extract X-Request-ID from request headers in before_request
  Store as g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
- Log in after_request (duration, status code)
- Log in teardown_request for exception cases
- Strip None values from log output dict before json.dumps

Service names: "api" and "frontend" as the service field.
```

---

## Health Check Endpoints

```
Implement GET /health for Kubernetes liveness and readiness probes.

API /health:
- Calls redis_client.ping()
- Returns 200 + JSON {status: "healthy", redis: {status: "connected"}}
  if ping succeeds
- Returns 503 + JSON {status: "unhealthy", redis: {status: "...", error: "..."}}
  if ping fails or redis_client is None
- Updates redis_operations_total{operation="ping"} metric

Frontend /health:
- Calls API /health via requests.get with timeout=2
- Returns 200 if API is reachable, otherwise returns unhealthy
- Cascading: frontend healthy = API healthy = Redis healthy

Both services also expose GET /version returning:
{service, version, commit, environment, timestamp} from env vars.
```

---

## Simulation Endpoints for Alert Testing

```
Create these simulation endpoints on the Flask API service:

GET /simulate/error
  raise Exception("This is a simulated error for testing")
  The global error handler returns 500 JSON.

GET /simulate/slow
  time.sleep(2)
  Return 200 JSON after delay.

GET /simulate/cpu
  Busy loop for 1.5 seconds: while time.time() - start < 1.5: [x*x for x in range(1000)]
  Return 200 JSON.

GET /simulate/redis-down
  Explicitly raise redis.ConnectionError("Redis connection failed - simulated")
  Call update_redis_metrics("ping", "error", "connection")
  Return 500 JSON {status: "error", error: "Redis unavailable"}

All endpoints return consistent JSON and log the simulation event.
```

---

## Probe Configuration

```
Configure Kubernetes startup, liveness, and readiness probes for Flask
services using GET /health:

startupProbe:
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 30   # allows up to 155s startup time
  (kills pod if still failing after 30 attempts)

livenessProbe:
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3
  (kills and restarts pod after 3 consecutive failures)

readinessProbe:
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 3
  (removes pod from Service endpoints when unhealthy)

All probe fields (timeoutSeconds, successThreshold, failureThreshold) are
driven from .Values.api.probes.* and .Values.frontend.probes.* in values.yaml.
```
