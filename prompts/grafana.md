# Grafana Dashboard Prompts

Prompts used during the creation and configuration of the KubeSight Grafana dashboard.

---

## Dashboard Design

```
Design a production Grafana dashboard for the KubeSight Kubernetes observability platform.

Sections and panels:

1. HTTP Traffic
   - API request rate: rate(api_http_requests_total[5m])
   - Frontend request rate: rate(frontend_http_requests_total[5m])
   - API error rate (5xx): rate(api_http_requests_total{http_status=~"5.."}[5m])
   - Total requests (stat panel)

2. Latency
   - API p50/p95/p99: histogram_quantile(0.X, rate(api_http_request_duration_seconds_bucket[5m]))
   - Frontend p99 latency

3. Redis
   - Operations per second by type: rate(redis_operations_total[5m])
   - Success vs error breakdown
   - Total visit counter (stat panel from redis_operations_total{operation="incr",key="visits"})

4. Page Views
   - Page views rate: rate(frontend_page_views_total[5m])
   - Views by page (bar chart): sum by (page) (rate(frontend_page_views_total[5m]))

5. Infrastructure
   - Pod CPU: rate(container_cpu_user_seconds_total{namespace="kubesight"}[1m])
   - Pod memory: container_memory_working_set_bytes{namespace="kubesight"}
   - Pod restart count
   - Available replicas

Template variables: $namespace, $service, $interval (1m, 5m, 15m).
Use Grafana 10.x JSON model format.
```

---

## Grafana Dashboard Auto-Provisioning

```
Auto-provision a Grafana dashboard in Kubernetes using the sidecar pattern.

How it works:
1. Create a ConfigMap in the monitoring namespace containing dashboard JSON
2. Add label grafana_dashboard: "1" to the ConfigMap
3. The Grafana sidecar container (grafana-sc-dashboard) watches for ConfigMaps
   with this label and copies the JSON into Grafana's provisioning path
4. Grafana loads the dashboard automatically — no restart or manual import needed

kube-prometheus-stack install flags required:
  --set grafana.sidecar.dashboards.enabled=true
  --set grafana.sidecar.dashboards.label=grafana_dashboard

The ConfigMap must be in the same namespace as Grafana (monitoring).
The KubeSight Helm chart deploys it there via .Values.grafanaDashboard.namespace.
```

---

## Grafana ConfigMap Helm Template

```
Create grafana-dashboard-configmap.yaml Helm template that:
1. Is conditional: {{- if .Values.grafanaDashboard.enabled }}
2. Creates a ConfigMap in .Values.grafanaDashboard.namespace (default: monitoring)
   using: namespace: {{ .Values.grafanaDashboard.namespace | default .Release.Namespace }}
3. Loads dashboard JSON from grafana-dashboard.json using .Files.Get
   and indents it 4 spaces for valid YAML embedding
4. Includes label grafana_dashboard: "1" for sidecar detection
5. Includes standard Helm labels from kubesight.labels helper

The ConfigMap is intentionally in the monitoring namespace, not kubesight.
This is required for the Grafana sidecar to detect it.

data:
  kubesight-production-dashboard.json: |
{{ .Files.Get "grafana-dashboard.json" | indent 4 }}
```

---

## Grafana Datasource Configuration

```
The Prometheus datasource in kube-prometheus-stack is named "Prometheus" by default.
The internal cluster URL is: http://kube-prometheus-stack-prometheus:9090

In Grafana dashboard JSON, reference it as:
  "datasource": { "type": "prometheus", "uid": "prometheus" }

To verify the datasource:
  kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring
  Open http://localhost:3000 → Connections → Data Sources → Prometheus
  Click "Save & Test" to confirm connectivity.
```
