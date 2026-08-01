# Dashboard Design Prompts

Prompts used during the design and implementation of the KubeSight Grafana dashboard.

---

## Production Dashboard Layout

```
Design the panel layout for a Grafana production dashboard for KubeSight.

Requirements:
- Dashboard title: "KubeSight Production Dashboard"
- Refresh interval: 30s
- Time range: last 1 hour

Row 1: Overview (stat panels)
- Total requests (API)
- Error rate
- p99 latency
- Active pods

Row 2: HTTP Traffic (time series)
- API request rate by endpoint
- Frontend request rate
- 5xx error rate over time

Row 3: Latency (time series + gauge)
- API p50 / p95 / p99 latency
- Frontend p99 latency

Row 4: Redis (time series + stat)
- Redis ops/sec by type
- Redis success vs error rate
- Total visit counter

Row 5: Infrastructure (time series)
- Pod CPU usage (% of limits)
- Pod memory usage (% of limits)
- Pod restart count

Provide panel IDs, PromQL queries, and visualization types for each panel.
```

---

## Grafana Panel JSON Templates

```
Provide the Grafana 10.x JSON definition for:

1. A Time Series panel showing:
   Title: "API Request Rate"
   Query: rate(api_http_requests_total[5m])
   Legend: {{method}} {{endpoint}} - {{http_status}}
   Unit: req/s
   
2. A Stat panel showing:
   Title: "p99 Latency"
   Query: histogram_quantile(0.99, rate(api_http_request_duration_seconds_bucket[5m]))
   Unit: seconds
   Thresholds: green < 0.1s, yellow < 0.5s, red >= 0.5s

3. A Gauge panel showing:
   Title: "Error Rate"
   Query: rate(api_http_requests_total{http_status=~"5.."}[5m]) / rate(api_http_requests_total[5m]) * 100
   Unit: percent
   Thresholds: green < 1%, yellow < 5%, red >= 5%
```

---

## Dashboard JSON Export Format

```
Explain the Grafana dashboard JSON export format.

I need to:
1. Export an existing dashboard as JSON
2. Embed it in a Kubernetes ConfigMap
3. Have it auto-provisioned by the Grafana sidecar

Questions:
1. Which fields should be removed from the exported JSON before embedding?
   (e.g., id, uid, version — explain why)
2. How to handle the datasource reference to use the default Prometheus source?
3. What is the correct ConfigMap structure for the sidecar to detect it?
4. How to validate the JSON is valid Grafana format before embedding?
```

---

## Alerting Annotations on Dashboard

```
Add Prometheus/AlertManager alert annotations to the KubeSight Grafana dashboard.

Requirements:
- Show when HighCPU, HighMemory, and PodRestarts alerts fired
- Display as vertical lines on time series panels
- Show alert name and description in the tooltip

Provide:
1. The annotations configuration block in dashboard JSON
2. The PromQL query to fetch alert events
3. How to filter annotations to KubeSight-specific alerts only
```

---

## Dashboard Variable Chaining

```
Add chained template variables to the KubeSight Grafana dashboard:

1. $cluster – all available clusters (if multi-cluster)
2. $namespace – namespaces filtered by cluster
3. $pod – pods filtered by namespace

Use label_values() queries with proper filters.
Show how to use these variables in PromQL:

rate(container_cpu_user_seconds_total{
  cluster="$cluster",
  namespace="$namespace",
  pod=~"$pod"
}[5m])
```
