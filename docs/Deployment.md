# Deployment Guide

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Docker | 20.x+ | [docs.docker.com](https://docs.docker.com/get-docker/) |
| kubectl | 1.28+ | [kubernetes.io](https://kubernetes.io/docs/tasks/tools/) |
| Helm | 3.x | [helm.sh](https://helm.sh/docs/intro/install/) |
| Kind | 0.20+ | [kind.sigs.k8s.io](https://kind.sigs.k8s.io/docs/user/quick-start/) |

---

## Option 1 – Local Development with Docker Compose

The fastest way to run KubeSight locally without Kubernetes.

```bash
# Clone the repository
git clone https://github.com/samkeerthana98/kubesight-production-observability.git
cd kubesight-production-observability

# Start all services
docker compose up --build

# Stop services
docker compose down
```

Services:

| Service | URL |
|---|---|
| Frontend | http://localhost:5001 |
| API | http://localhost:5000 |
| Redis | localhost:6379 |

---

## Option 2 – Kubernetes with Helm

### Step 1 – Create a Kind Cluster

```bash
kind create cluster \
  --config kubernetes/kind-cluster-config.yaml \
  --name kubesight
```

Verify the cluster:

```bash
kubectl cluster-info --context kind-kubesight
kubectl get nodes
```

### Step 2 – Install kube-prometheus-stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.sidecar.dashboards.enabled=true \
  --set grafana.sidecar.dashboards.label=grafana_dashboard \
  --wait
```

Verify installation:

```bash
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

### Step 3 – Build Docker Images (optional for Kind)

If using custom images, build and load them into Kind:

```bash
# Build images
docker build -t kubesight/api:latest ./app/api
docker build -t kubesight/frontend:latest ./app/frontend

# Load into Kind cluster
kind load docker-image kubesight/api:latest --name kubesight
kind load docker-image kubesight/frontend:latest --name kubesight
```

### Step 4 – Deploy KubeSight

#### Development Deployment

```bash
helm install kubesight ./kubesight-chart \
  --namespace kubesight \
  --create-namespace \
  -f ./kubesight-chart/values-dev.yaml \
  --wait
```

#### Production Deployment

```bash
helm install kubesight ./kubesight-chart \
  --namespace kubesight \
  --create-namespace \
  -f ./kubesight-chart/values-production.yaml \
  --wait
```

### Step 5 – Verify Deployment

```bash
# Check pods
kubectl get pods -n kubesight

# Check services
kubectl get svc -n kubesight

# Check ServiceMonitors
kubectl get servicemonitors -n kubesight

# Check PrometheusRules (production only)
kubectl get prometheusrules -n kubesight

# Run Helm tests
helm test kubesight -n kubesight
```

Expected pod output:

```
NAME                                    READY   STATUS    RESTARTS   AGE
kubesight-api-xxxxxxxxx-xxxxx           1/1     Running   0          2m
kubesight-frontend-xxxxxxxxx-xxxxx      1/1     Running   0          2m
kubesight-redis-xxxxxxxxx-xxxxx         1/1     Running   0          2m
```

### Step 6 – Access Services

```bash
# Frontend application
kubectl port-forward svc/kubesight-frontend 5001:5000 -n kubesight

# Grafana dashboard
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring

# Prometheus UI
kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring

# AlertManager UI
kubectl port-forward svc/kube-prometheus-stack-alertmanager 9093:9093 -n monitoring
```

| Service | URL | Credentials |
|---|---|---|
| Frontend | http://localhost:5001 | – |
| API | http://localhost:5000 | – |
| Grafana | http://localhost:3000 | admin / prom-operator |
| Prometheus | http://localhost:9090 | – |
| AlertManager | http://localhost:9093 | – |

---

## Upgrade and Rollback

### Upgrade

```bash
helm upgrade kubesight ./kubesight-chart \
  -n kubesight \
  -f ./kubesight-chart/values-production.yaml
```

### Check Upgrade History

```bash
helm history kubesight -n kubesight
```

### Rollback

```bash
# Rollback to previous revision
helm rollback kubesight -n kubesight

# Rollback to a specific revision
helm rollback kubesight 2 -n kubesight
```

---

## Uninstall

```bash
# Remove KubeSight
helm uninstall kubesight -n kubesight

# Remove kube-prometheus-stack
helm uninstall kube-prometheus-stack -n monitoring

# Delete namespaces
kubectl delete namespace kubesight
kubectl delete namespace monitoring

# Delete Kind cluster
kind delete cluster --name kubesight
```

---

## Environment Values Reference

| File | Purpose |
|---|---|
| `values.yaml` | Default development values |
| `values-dev.yaml` | Dev environment overrides (1 replica, minimal resources) |
| `values-production.yaml` | Production overrides (3 replicas, HPA, PDB, NetworkPolicy) |

See [docs/Monitoring.md](./Monitoring.md) for observability configuration details.
