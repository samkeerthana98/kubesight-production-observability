# Prometheus Metrics Reference

## Overview

KubeSight exposes custom Prometheus metrics from both the API and Frontend services. Metrics are available at the `/metrics` endpoint on each service and are scraped automatically by Prometheus via ServiceMonitor CRDs.

---

## API Service Metrics

### `api_http_requests_total`

- **Type**: Counter
- **Description**: Total number of HTTP requests processed by the API service
- **Labels**:
  - `method` – HTTP method (GET, POST, etc.)
  - `endpoint` – Flask route name (e.g., `index`, `health`, `metrics`)
  - `http_status` – HTTP response status code (200, 500, etc.)

**Example PromQL**:
```promql
# Request rate per second
rate(api_http_requests_total[5m])

# Error rate (5xx)
rate(api_http_requests_total{http_status=~"5.."}[5m])

# Requests by endpoint
sum by (endpoint) (rate(api_http_requests_total[5m]))
```

---

### `api_http_request_duration_seconds`

- **Type**: Histogram
- **Description**: HTTP request latency in seconds for the API service
- **Labels**:
  - `method` – HTTP method
  - `endpoint` – Flask route name
- **Buckets**: Default Prometheus buckets (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)

**Example PromQL**:
```promql
# p50 latency
histogram_quantile(0.50, rate(api_http_request_duration_seconds_bucket[5m]))

# p95 latency
histogram_quantile(0.95, rate(api_http_request_duration_seconds_bucket[5m]))

# p99 latency
histogram_quantile(0.99, rate(api_http_request_duration_seconds_bucket[5m]))

# Average latency
rate(api_http_request_duration_seconds_sum[5m])
  / rate(api_http_request_duration_seconds_count[5m])
```

---

### `redis_operations_total`

- **Type**: Counter
- **Description**: Total number of Redis operations performed by the API service
- **Labels**:
  - `operation` – Redis command (e.g., `incr`, `ping`)
  - `status` – Result of the operation (`success`, `error`)
  - `key` – Redis key used (e.g., `visits`, `connection`)

**Example PromQL**:
```promql
# Redis success rate
rate(redis_operations_total{status="success"}[5m])

# Redis error rate
rate(redis_operations_total{status="error"}[5m])

# Total operations by type
sum by (operation) (rate(redis_operations_total[5m]))
```

---

## Frontend Service Metrics

### `frontend_http_requests_total`

- **Type**: Counter
- **Description**: Total number of HTTP requests processed by the Frontend service
- **Labels**:
  - `method` – HTTP method
  - `endpoint` – Flask route name
  - `http_status` – HTTP response status code

**Example PromQL**:
```promql
# Frontend request rate
rate(frontend_http_requests_total[5m])

# Frontend error rate
rate(frontend_http_requests_total{http_status=~"5.."}[5m])
```

---

### `frontend_http_request_duration_seconds`

- **Type**: Histogram
- **Description**: HTTP request latency in seconds for the Frontend service
- **Labels**:
  - `method` – HTTP method
  - `endpoint` – Flask route name

**Example PromQL**:
```promql
# Frontend p99 latency
histogram_quantile(0.99, rate(frontend_http_request_duration_seconds_bucket[5m]))
```

---

### `frontend_page_views_total`

- **Type**: Counter
- **Description**: Total number of page views tracked by the Frontend service
- **Labels**:
  - `page` – Flask endpoint name (page identifier)
  - `http_status` – HTTP response status code

**Example PromQL**:
```promql
# Page views per second
rate(frontend_page_views_total[5m])

# Page views by page
sum by (page) (rate(frontend_page_views_total[5m]))
```

---

## Kubernetes Infrastructure Metrics (from kube-prometheus-stack)

These are provided by kube-state-metrics and node-exporter (included in kube-prometheus-stack):

| Metric | Description |
|---|---|
| `kube_pod_container_status_restarts_total` | Total container restarts |
| `kube_pod_container_resource_limits_cpu_cores` | CPU limits per container |
| `kube_pod_container_resource_limits_memory_bytes` | Memory limits per container |
| `container_cpu_user_seconds_total` | CPU usage in user mode |
| `container_memory_working_set_bytes` | Working set memory |
| `kube_deployment_status_replicas_available` | Available replicas |
| `kube_deployment_status_replicas_ready` | Ready replicas |

---

## Accessing the /metrics Endpoint

```bash
# API metrics (via port-forward)
kubectl port-forward svc/kubesight-api 5000:5000 -n kubesight
curl http://localhost:5000/metrics

# Frontend metrics (via port-forward)
kubectl port-forward svc/kubesight-frontend 5001:5000 -n kubesight
curl http://localhost:5001/metrics
```

Sample output:

```
# HELP api_http_requests_total Total HTTP Requests
# TYPE api_http_requests_total counter
api_http_requests_total{endpoint="index",http_status="200",method="GET"} 42.0
api_http_requests_total{endpoint="health",http_status="200",method="GET"} 15.0
api_http_requests_total{endpoint="metrics",http_status="200",method="GET"} 8.0

# HELP api_http_request_duration_seconds HTTP request latency in seconds
# TYPE api_http_request_duration_seconds histogram
api_http_request_duration_seconds_bucket{endpoint="index",le="0.005",method="GET"} 0.0
api_http_request_duration_seconds_bucket{endpoint="index",le="0.01",method="GET"} 3.0
...

# HELP redis_operations_total Total Redis Operations
# TYPE redis_operations_total counter
redis_operations_total{key="visits",operation="incr",status="success"} 42.0
redis_operations_total{key="connection",operation="ping",status="success"} 15.0
```

---

## Grafana Dashboard Panels

The auto-provisioned Grafana dashboard includes panels for all the above metrics. See [Dashboard.md](./Dashboard.md) for details.
