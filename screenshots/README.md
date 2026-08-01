# Screenshots

This folder contains screenshots of the KubeSight production observability platform.

---

## Required Screenshots

After deploying KubeSight, capture the following screenshots to complete the project portfolio:

---

### 1. Grafana Production Dashboard

**Filename**: `grafana-dashboard.png`

**How to capture**:
```bash
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring
# Open http://localhost:3000 → Dashboards → KubeSight Production Dashboard
```

**What to show**:
- All dashboard panels visible (HTTP rate, latency, Redis ops, pod resources)
- Metrics actively updating (generate traffic first)
- Time range: last 1 hour

---

### 2. Prometheus Scrape Targets

**Filename**: `prometheus-targets.png`

**How to capture**:
```bash
kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring
# Open http://localhost:9090/targets
```

**What to show**:
- kubesight-api and kubesight-frontend targets showing `UP` state
- Scrape interval and last scrape time visible

---

### 3. Prometheus Metrics Explorer

**Filename**: `prometheus-metrics.png`

**How to capture**:
```bash
# Open http://localhost:9090/graph
# Enter query: rate(api_http_requests_total[5m])
# Click Execute → Graph tab
```

**What to show**:
- KubeSight custom metrics in the query editor
- Graph showing request rate over time

---

### 4. Helm Deployment Output

**Filename**: `helm-deploy.png`

**How to capture**:
```bash
helm install kubesight ./kubesight-chart \
  --namespace kubesight \
  --create-namespace \
  -f ./kubesight-chart/values-production.yaml
```

**What to show**:
- Successful `helm install` output
- NOTES.txt output displayed
- Release name, namespace, and status visible

---

### 5. Kubernetes Pods Running

**Filename**: `pods-running.png`

**How to capture**:
```bash
kubectl get pods -n kubesight
kubectl get pods -n monitoring
```

**What to show**:
- All KubeSight pods in `Running` state (API, Frontend, Redis)
- All monitoring pods in `Running` state (Prometheus, Grafana, AlertManager)
- `READY 1/1` for all pods

---

### 6. Architecture Diagram

**Filename**: `architecture.png`

**How to capture**:
- Export the Mermaid diagram from `README.md` as a PNG
- Use https://mermaid.live or the GitHub Mermaid renderer

**What to show**:
- Full system architecture including all components
- Connection flows between Frontend, API, Redis, Prometheus, Grafana

---

### 7. HPA in Action (Optional)

**Filename**: `hpa-scaling.png`

**How to capture**:
```bash
# Generate load first
for i in {1..100}; do curl http://localhost:5000/simulate/cpu & done

# Watch HPA scale
kubectl get hpa -n kubesight -w
```

**What to show**:
- HPA showing current CPU% and REPLICAS increasing

---

### 8. AlertManager (Optional)

**Filename**: `alertmanager.png`

**How to capture**:
```bash
kubectl port-forward svc/kube-prometheus-stack-alertmanager 9093:9093 -n monitoring
# Open http://localhost:9093
# Trigger an alert: curl http://localhost:5000/simulate/cpu
```

**What to show**:
- Active alerts visible in AlertManager UI

---

## Generate Traffic for Screenshots

Before taking screenshots, generate some traffic to populate the dashboards:

```bash
# Port-forward the API
kubectl port-forward svc/kubesight-api 5000:5000 -n kubesight &

# Generate 50 requests
for i in $(seq 1 50); do
  curl -s http://localhost:5000/ > /dev/null
  curl -s http://localhost:5000/health > /dev/null
done

# Trigger some errors and slow requests
curl http://localhost:5000/simulate/slow
curl http://localhost:5000/simulate/error
```

Wait ~60 seconds for Prometheus to scrape the metrics, then take screenshots.
