# Grafana Dashboard Guide

## Overview

KubeSight includes a production-ready Grafana dashboard that is **automatically provisioned** when deployed. No manual import is required.

The dashboard uses the Grafana sidecar container pattern: a ConfigMap containing the dashboard JSON is detected by the sidecar and loaded into Grafana automatically.

---

## How Auto-Provisioning Works

1. The Helm chart creates a `ConfigMap` in the `monitoring` namespace
2. The ConfigMap contains the full dashboard JSON (`grafana-dashboard.json`)
3. The ConfigMap has the label `grafana_dashboard: "1"`
4. The Grafana sidecar container (`grafana-sc-dashboard`) watches for ConfigMaps with this label
5. When detected, the sidecar copies the JSON into Grafana's dashboard provisioning path
6. Grafana automatically loads the dashboard — no restart or manual import required

### ConfigMap Template

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kubesight-grafana-dashboard
  namespace: monitoring          # Must match Grafana's namespace
  labels:
    grafana_dashboard: "1"       # Required label for sidecar detection
data:
  kubesight-production-dashboard.json: |
    { ... dashboard JSON ... }
```

---

## Accessing the Dashboard

### Step 1 – Port-forward Grafana

```bash
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring
```

### Step 2 – Open Grafana

- URL: http://localhost:3000
- Username: `admin`
- Password: `prom-operator`

### Step 3 – Navigate to the Dashboard

Dashboards → Browse → KubeSight Production Dashboard

---

## Dashboard Panels

### HTTP Traffic

| Panel | Metric | Type |
|---|---|---|
| API Request Rate | `rate(api_http_requests_total[5m])` | Time Series |
| Frontend Request Rate | `rate(frontend_http_requests_total[5m])` | Time Series |
| API Error Rate (5xx) | `rate(api_http_requests_total{http_status=~"5.."}[5m])` | Time Series |
| Total Requests | `sum(api_http_requests_total)` | Stat |

### Latency

| Panel | Metric | Type |
|---|---|---|
| API p50 Latency | `histogram_quantile(0.50, rate(api_http_request_duration_seconds_bucket[5m]))` | Gauge |
| API p95 Latency | `histogram_quantile(0.95, rate(api_http_request_duration_seconds_bucket[5m]))` | Gauge |
| API p99 Latency | `histogram_quantile(0.99, rate(api_http_request_duration_seconds_bucket[5m]))` | Gauge |
| Frontend p99 Latency | `histogram_quantile(0.99, rate(frontend_http_request_duration_seconds_bucket[5m]))` | Time Series |

### Redis

| Panel | Metric | Type |
|---|---|---|
| Redis Operations | `rate(redis_operations_total[5m])` | Time Series |
| Redis Success Rate | `rate(redis_operations_total{status="success"}[5m])` | Time Series |
| Redis Error Rate | `rate(redis_operations_total{status="error"}[5m])` | Stat |
| Total Visit Count | `redis_operations_total{operation="incr",key="visits"}` | Stat |

### Page Views

| Panel | Metric | Type |
|---|---|---|
| Page Views Rate | `rate(frontend_page_views_total[5m])` | Time Series |
| Page Views by Page | `sum by (page) (rate(frontend_page_views_total[5m]))` | Bar Chart |

### Infrastructure

| Panel | Metric | Type |
|---|---|---|
| Pod CPU Usage | `rate(container_cpu_user_seconds_total{namespace="kubesight"}[1m])` | Time Series |
| Pod Memory Usage | `container_memory_working_set_bytes{namespace="kubesight"}` | Time Series |
| Pod Restart Count | `kube_pod_container_status_restarts_total{namespace="kubesight"}` | Stat |
| Available Replicas | `kube_deployment_status_replicas_available{namespace="kubesight"}` | Stat |

---

## Dashboard Variables

The dashboard includes template variables for filtering:

| Variable | Description |
|---|---|
| `$namespace` | Filter by Kubernetes namespace |
| `$service` | Filter by service (api / frontend) |
| `$interval` | Aggregation interval (1m, 5m, 15m) |

---

## Dashboard JSON File

The dashboard definition is stored at:

```
kubesight-chart/grafana-dashboard.json
```

This file is embedded into the ConfigMap by the Helm template using `.Files.Get`:

```yaml
# kubesight-chart/templates/grafana-dashboard-configmap.yaml
data:
  kubesight-production-dashboard.json: |
{{ .Files.Get "grafana-dashboard.json" | indent 4 }}
```

---

## Manually Importing the Dashboard

If auto-provisioning does not work, you can manually import:

1. Open Grafana → Dashboards → Import
2. Upload the file: `kubesight-chart/grafana-dashboard.json`
3. Select Prometheus as the datasource
4. Click Import

---

## Troubleshooting Dashboard Issues

See [Troubleshooting.md](./Troubleshooting.md) for common Grafana dashboard issues and fixes.

Key checks:

```bash
# Verify ConfigMap exists with correct label
kubectl get configmap -n monitoring | grep grafana
kubectl get configmap kubesight-grafana-dashboard -n monitoring -o yaml | grep grafana_dashboard

# Check sidecar logs
kubectl logs -n monitoring -l app.kubernetes.io/name=grafana -c grafana-sc-dashboard
```
