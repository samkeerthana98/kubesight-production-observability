# Monitoring Guide

## Overview

KubeSight uses the **kube-prometheus-stack** for full Kubernetes observability. The stack includes:

- **Prometheus Operator** – manages Prometheus and AlertManager as Kubernetes CRDs
- **Prometheus** – scrapes metrics from ServiceMonitors and evaluates alert rules
- **Grafana** – visualizes metrics with auto-provisioned dashboards
- **AlertManager** – routes and deduplicates alerts

---

## ServiceMonitors

KubeSight deploys two `ServiceMonitor` CRDs in the `kubesight` namespace. These tell the Prometheus Operator where to scrape application metrics.

### kubesight-api ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kubesight-api
  labels:
    release: kube-prometheus-stack   # Required for Prometheus to discover
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: kubesight
      app.kubernetes.io/component: api
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
```

### kubesight-frontend ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kubesight-frontend
  labels:
    release: kube-prometheus-stack   # Required for Prometheus to discover
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: kubesight
      app.kubernetes.io/component: frontend
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
```

> **Important**: The `release: kube-prometheus-stack` label is required for Prometheus to discover the ServiceMonitor. This must match the Prometheus `serviceMonitorSelector` configuration.

Verify ServiceMonitors are discovered:

```bash
kubectl get servicemonitors -n kubesight
kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring
# Navigate to http://localhost:9090/targets
```

---

## PrometheusRules (Alerting)

PrometheusRules are enabled in the production values file:

```yaml
# values-production.yaml
monitoring:
  prometheusRule:
    enabled: true
```

### Configured Alert Rules

| Alert | Condition | Duration | Severity |
|---|---|---|---|
| `HighCPUUsage` | CPU usage > 80% of limit | 5 minutes | warning |
| `HighMemoryUsage` | Memory usage > 80% of limit | 5 minutes | warning |
| `PodRestarts` | Pod restart count increased | Immediate | warning |

### HighCPUUsage Rule

```yaml
alert: HighCPUUsage
expr: |
  100 * (sum by (pod, container) (rate(container_cpu_user_seconds_total[1m]))
         /
         sum by (pod, container) (kube_pod_container_resource_limits_cpu_cores)) > 80
for: 5m
labels:
  severity: warning
annotations:
  summary: "High CPU usage detected"
  description: "CPU usage is above 80% for more than 5 minutes."
```

### HighMemoryUsage Rule

```yaml
alert: HighMemoryUsage
expr: |
  100 * (sum by (pod, container) (container_memory_working_set_bytes)
         /
         sum by (pod, container) (kube_pod_container_resource_limits_memory_bytes)) > 80
for: 5m
labels:
  severity: warning
annotations:
  summary: "High memory usage detected"
  description: "Memory usage is above 80% for more than 5 minutes."
```

### PodRestarts Rule

```yaml
alert: PodRestarts
expr: increase(kube_pod_container_status_restarts_total[5m]) > 0
for: 0m
labels:
  severity: warning
annotations:
  summary: "Pod has restarted"
  description: "The pod has restarted, which may indicate instability."
```

---

## Testing Alerting Rules

Use the built-in simulation endpoints to trigger real alerts:

```bash
# Trigger a slow response (latency spike)
curl http://localhost:5000/simulate/slow

# Trigger CPU load
curl http://localhost:5000/simulate/cpu

# Trigger a 500 error
curl http://localhost:5000/simulate/error

# Simulate Redis failure
curl http://localhost:5000/simulate/redis-down
```

Check firing alerts:

```bash
kubectl port-forward svc/kube-prometheus-stack-alertmanager 9093:9093 -n monitoring
# Open http://localhost:9093
```

---

## Prometheus Queries (PromQL)

Useful PromQL queries for investigating KubeSight metrics:

```promql
# API request rate (requests/second)
rate(api_http_requests_total[5m])

# Frontend request rate
rate(frontend_http_requests_total[5m])

# API p99 request latency
histogram_quantile(0.99, rate(api_http_request_duration_seconds_bucket[5m]))

# Redis operation success rate
rate(redis_operations_total{status="success"}[5m])

# Error rate (5xx responses)
rate(api_http_requests_total{http_status=~"5.."}[5m])

# Pod CPU usage
rate(container_cpu_user_seconds_total{namespace="kubesight"}[1m])

# Pod memory usage
container_memory_working_set_bytes{namespace="kubesight"}
```

---

## Grafana Dashboard

The Grafana dashboard is **auto-provisioned** via a ConfigMap in the `monitoring` namespace. The Grafana sidecar container detects ConfigMaps with the label `grafana_dashboard: "1"` and automatically loads them.

Enable the dashboard (on by default):

```yaml
# values.yaml
grafanaDashboard:
  enabled: true
  namespace: monitoring
```

Access Grafana:

```bash
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring
```

- URL: http://localhost:3000
- Username: `admin`
- Password: `prom-operator`

Navigate to: Dashboards → KubeSight Production Dashboard

---

## Monitoring Configuration Reference

```yaml
# values.yaml monitoring section
monitoring:
  serviceMonitor:
    enabled: true        # Deploy ServiceMonitors for api + frontend
    interval: 30s        # Scrape interval
    scrapeTimeout: 10s   # Scrape timeout

  prometheusRule:
    enabled: false       # Set true in production values

grafanaDashboard:
  enabled: true          # Auto-provision Grafana dashboard
  namespace: monitoring  # Must match Grafana's namespace
```
