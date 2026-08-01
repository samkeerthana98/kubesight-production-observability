# Grafana Dashboard Prompts

Prompts used during the creation and configuration of the KubeSight Grafana dashboard.

---

## Dashboard Design

```
Design a production Grafana dashboard for the KubeSight Kubernetes observability platform.

The dashboard should cover:
1. HTTP Traffic section
   - Request rate per service (API + Frontend)
   - Error rate (5xx)
   - Total requests (stat panel)

2. Latency section
   - p50, p95, p99 latency for API
   - p99 latency for Frontend
   - Latency heatmap

3. Redis section
   - Operations per second (by type)
   - Success vs error breakdown
   - Total visit counter (stat panel)

4. Page Views section
   - Page views rate
   - Views by page (bar chart)

5. Infrastructure section
   - Pod CPU usage (% of limits)
   - Pod memory usage (% of limits)
   - Pod restart count
   - Available vs desired replicas

Include template variables for: namespace, service, interval.
Use Grafana 10.x JSON model format.
```

---

## Grafana Dashboard Auto-Provisioning

```
Explain how to auto-provision a Grafana dashboard in Kubernetes using the
Grafana sidecar container pattern.

Requirements:
1. Create a Kubernetes ConfigMap in the monitoring namespace
2. Add the label grafana_dashboard: "1" to the ConfigMap
3. Store the dashboard JSON in the ConfigMap data
4. The Grafana sidecar container should detect and load it automatically

Provide:
- The Kubernetes ConfigMap YAML structure
- The required Grafana sidecar configuration in kube-prometheus-stack
- How to verify the dashboard was loaded

Note: The dashboard must be in the same namespace as Grafana.
```

---

## Grafana ConfigMap Helm Template

```
Create a Helm template (grafana-dashboard-configmap.yaml) that:
1. Is conditional: only rendered if .Values.grafanaDashboard.enabled is true
2. Creates a ConfigMap in .Values.grafanaDashboard.namespace (default: monitoring)
3. Loads the dashboard JSON from grafana-dashboard.json using .Files.Get
4. Indents the JSON correctly for YAML embedding (4 spaces)
5. Includes the label grafana_dashboard: "1" for sidecar detection
6. Includes standard Helm labels

Handle the case where grafanaDashboard.namespace may be different from the
release namespace (the dashboard ConfigMap must be in the monitoring namespace,
not the kubesight namespace).
```

---

## Dashboard Variables

```
Add Grafana template variables to the KubeSight dashboard:
1. $namespace – query label_values(kube_pod_info, namespace)
2. $service – query label_values(api_http_requests_total, job)
3. $interval – custom intervals: 1m, 5m, 15m, 30m, 1h

Show how to use these variables in PromQL queries, e.g.:
rate(api_http_requests_total{namespace=~"$namespace"}[$interval])
```

---

## Grafana Datasource Configuration

```
Explain how the Prometheus datasource is configured in kube-prometheus-stack.

Questions:
1. What is the default datasource name?
2. How to reference it in dashboard JSON?
3. How to verify the datasource is working in Grafana?
4. How to manually add a Prometheus datasource if it's missing?

The Prometheus service is in the monitoring namespace.
The internal URL is: http://kube-prometheus-stack-prometheus:9090
```

---

## Alert Annotations in Grafana

```
Configure Grafana alert annotations to display firing Prometheus alerts
directly on the KubeSight dashboard.

Requirements:
- Show AlertManager alerts as annotations on time series panels
- Filter to only KubeSight alerts (label: namespace="kubesight")
- Display alert name and description in the annotation tooltip

Provide the annotation configuration JSON for Grafana 10.x dashboard.
```
