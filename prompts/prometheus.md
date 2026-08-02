# Prometheus Prompts

Prompts used during the development of Prometheus metrics, ServiceMonitors, and PrometheusRules for KubeSight.

---

## Custom Prometheus Metrics in Flask

```
Add custom Prometheus metrics to a Python Flask application using before_request
/ after_request middleware.

API service metrics:
- Counter: api_http_requests_total — labels: method, endpoint, http_status
- Histogram: api_http_request_duration_seconds — labels: method, endpoint
- Counter: redis_operations_total — labels: operation, status, key

Frontend service metrics:
- Counter: frontend_http_requests_total — labels: method, endpoint, http_status
- Histogram: frontend_http_request_duration_seconds — labels: method, endpoint
- Counter: frontend_page_views_total — labels: page, http_status

Implementation:
- before_request: record g.start_time and generate/extract X-Request-ID
- after_request: compute duration, call .inc() on request counter,
  call .observe() on latency histogram, then return response
- Expose all metrics at GET /metrics using generate_latest()
- Use CONTENT_TYPE_LATEST as the response mimetype

Use prometheus_client Python library (version 0.19.0).
```

---

## ServiceMonitor CRD

```
Create a Kubernetes ServiceMonitor CRD (monitoring.coreos.com/v1) for the
KubeSight API and Frontend services as a single Helm template file.

Requirements:
- Two ServiceMonitors separated by ---: kubesight-api and kubesight-frontend
- selector matchLabels per monitor:
    app.kubernetes.io/name: kubesight
    app.kubernetes.io/component: api   (or frontend)
- namespaceSelector: matchNames: [{{ .Release.Namespace }}]
- endpoint: port: http, path: /metrics
- interval and scrapeTimeout from .Values.monitoring.serviceMonitor
- Hardcoded label: release: kube-prometheus-stack (required for Prometheus discovery)
- Wrap entire file in: {{- if .Values.monitoring.serviceMonitor.enabled }}

Note: ServiceMonitors are deployed in the kubesight namespace (the Helm release
namespace), not in the monitoring namespace. The release: kube-prometheus-stack
label is what tells Prometheus Operator to pick them up across namespaces.
```

---

## PrometheusRule CRD

```
Create a PrometheusRule CRD (monitoring.coreos.com/v1) for KubeSight with
three alert rules under group name: kubesight.rules

1. HighCPUUsage
   expr: 100 * (sum by (pod, container) (rate(container_cpu_user_seconds_total[1m]))
               / sum by (pod, container) (kube_pod_container_resource_limits_cpu_cores)) > 80
   for: 5m, severity: warning

2. HighMemoryUsage
   expr: 100 * (sum by (pod, container) (container_memory_working_set_bytes)
               / sum by (pod, container) (kube_pod_container_resource_limits_memory_bytes)) > 80
   for: 5m, severity: warning

3. PodRestarts
   expr: increase(kube_pod_container_status_restarts_total[5m]) > 0
   for: 0m (fires immediately), severity: warning

Include summary and description annotations on each rule.
Wrap in: {{- if .Values.monitoring.prometheusRule.enabled }}
```

---

## PromQL Queries for KubeSight

```
Write PromQL queries for the following use cases using KubeSight metric names:

1. API request rate per second (5m window)
   rate(api_http_requests_total[5m])

2. API error rate (5xx only)
   rate(api_http_requests_total{http_status=~"5.."}[5m])

3. API latency percentiles (p50, p95, p99)
   histogram_quantile(0.99, rate(api_http_request_duration_seconds_bucket[5m]))

4. Redis operation success vs error rate
   rate(redis_operations_total{status="success"}[5m])
   rate(redis_operations_total{status="error"}[5m])

5. Frontend page views rate
   rate(frontend_page_views_total[5m])

6. Pod CPU usage (namespace filter)
   rate(container_cpu_user_seconds_total{namespace="kubesight"}[1m])

7. Pod memory working set
   container_memory_working_set_bytes{namespace="kubesight"}

8. Pod restart count
   increase(kube_pod_container_status_restarts_total{namespace="kubesight"}[5m])
```

---

## Prometheus Service Discovery Debug

```
Prometheus is not discovering the KubeSight ServiceMonitor targets.
The ServiceMonitors exist in the kubesight namespace.

Debug steps:
1. Verify the ServiceMonitor has label: release: kube-prometheus-stack
   kubectl get servicemonitor kubesight-api -n kubesight -o yaml | grep release

2. Check what serviceMonitorSelector is set on the Prometheus CRD
   kubectl get prometheus -n monitoring -o yaml | grep -A5 serviceMonitorSelector

3. Verify the ServiceMonitor selector matches actual Service labels
   kubectl get svc kubesight-api -n kubesight --show-labels

4. Check Prometheus targets page at http://localhost:9090/targets

The kube-prometheus-stack Prometheus by default selects ServiceMonitors
with label release: kube-prometheus-stack. This label must be present
on the ServiceMonitor metadata, not just the Service.
```
