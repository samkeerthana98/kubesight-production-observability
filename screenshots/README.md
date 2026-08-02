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

**Filename**: `heml-deploy.png`

**How to capture**:
```bash
helm install kubesight ./kubesight-chart \
  --namespace kubesight \
  --create-namespace \
  -f ./kubesight-chart/values-dev.yaml
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
- All monitoring pods in `Running` state (Prometheus, Grafana)
- `READY 1/1` for all pods

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
