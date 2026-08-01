# Prometheus Prompts

Prompts used during the development of Prometheus metrics, ServiceMonitors, and PrometheusRules for KubeSight.

---

## Custom Prometheus Metrics in Flask

```
Add custom Prometheus metrics to a Python Flask application.

Requirements:
- Counter: api_http_requests_total with labels [method, endpoint, http_status]
- Histogram: api_http_request_duration_seconds with labels [method, endpoint]
- Counter: redis_operations_total with labels [operation, status, key]

Use Flask before_request / after_request middleware to:
- Record request count on every response
- Record latency for every request
- Attach the request duration to the response

Use prometheus_client Python library.
Expose metrics at GET /metrics endpoint.
```

---

## ServiceMonitor CRD

```
Create a Kubernetes ServiceMonitor CRD (monitoring.coreos.com/v1) for the
KubeSight API and Frontend services.

Requirements:
- Two separate ServiceMonitors: kubesight-api and kubesight-frontend
- Selector matchLabels:
    app.kubernetes.io/name: kubesight
    app.kubernetes.io/component: api (or frontend)
- Scrape /metrics endpoint on port named "http"
- Interval: 30s, scrapeTimeout: 10s
- Include label: release: kube-prometheus-stack (required for Prometheus discovery)
- Namespace selector: match the release namespace

Wrap in Helm conditional: {{- if .Values.monitoring.serviceMonitor.enabled }}
```

---

## PrometheusRule CRD

```
Create a PrometheusRule CRD (monitoring.coreos.com/v1) for KubeSight with
three alert rules:

1. HighCPUUsage
   - Expression: CPU usage > 80% of resource limits
   - Duration: 5 minutes
   - Severity: warning

2. HighMemoryUsage
   - Expression: Memory working set > 80% of memory limits
   - Duration: 5 minutes
   - Severity: warning

3. PodRestarts
   - Expression: pod restart count increased in last 5 minutes
   - Duration: immediate (0m)
   - Severity: warning

Use proper kube-state-metrics and cAdvisor metric names.
Include summary and description annotations.
Wrap in Helm conditional: {{- if .Values.monitoring.prometheusRule.enabled }}
```

---

## PromQL Queries for KubeSight

```
Write PromQL queries for the following KubeSight metrics:

1. HTTP request rate per second (5m window)
2. HTTP error rate (5xx responses only)
3. p50, p95, p99 request latency
4. Redis operation success vs error rate
5. Pod CPU usage percentage vs limits
6. Pod memory usage percentage vs limits
7. Pod restart count in last 5 minutes
8. Available vs desired replicas

Include both API and Frontend service variants where applicable.
Use proper label selectors for the kubesight namespace.
```

---

## Prometheus Service Discovery Debug

```
Prometheus is not discovering the KubeSight ServiceMonitor targets.
The ServiceMonitors exist in the kubesight namespace.

Debug steps:
1. What label must the ServiceMonitor have for Prometheus to discover it?
2. How to check what serviceMonitorSelector is configured on the Prometheus CRD?
3. How to verify the ServiceMonitor selector matches the actual Service labels?
4. How to confirm Prometheus has loaded the scrape config?

The Prometheus stack was installed with:
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack
```

---

## Metrics Rate vs Instant Queries

```
Explain the difference between:
- rate() vs irate() for counters in Prometheus
- histogram_quantile() vs avg() for latency
- increase() vs delta() for counters

Give examples using:
- api_http_requests_total
- api_http_request_duration_seconds_bucket
- kube_pod_container_status_restarts_total
```
