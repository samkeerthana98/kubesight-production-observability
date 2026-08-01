# KubeSight – Production Kubernetes Observability Platform

> A production-grade Kubernetes observability platform demonstrating Helm packaging, Prometheus metrics, Grafana dashboards, and multi-environment deployments.

[![Helm Lint](https://github.com/samkeerthana98/kubesight-production-observability/actions/workflows/helm-lint.yml/badge.svg)](https://github.com/samkeerthana98/kubesight-production-observability/actions/workflows/helm-lint.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
![Kubernetes](https://img.shields.io/badge/Kubernetes-1.28+-326CE5?logo=kubernetes&logoColor=white)
![Helm](https://img.shields.io/badge/Helm-3.x-0F1689?logo=helm&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-2.x-E6522C?logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-10.x-F46800?logo=grafana&logoColor=white)

---

## Overview

KubeSight is a Kubernetes observability platform built from scratch to demonstrate end-to-end DevOps skills. It consists of a Python Flask microservices application (API + Frontend) backed by Redis, packaged as a production Helm chart, and integrated with **kube-prometheus-stack** (Prometheus + Grafana) for real-time observability.

What is actually implemented:

- **RollingUpdate deployments** with configurable maxSurge/maxUnavailable
- **Pod Disruption Budgets** on API, Frontend, and Redis
- **Horizontal Pod Autoscaler** (CPU-based) for API and Frontend
- **Custom Prometheus metrics** (Counters, Histograms) exposed from both services
- **ServiceMonitor CRDs** for automatic Prometheus scraping
- **PrometheusRule alerts** — HighCPU, HighMemory, PodRestarts (enabled in production)
- **Grafana dashboard auto-provisioning** via ConfigMap + Grafana sidecar
- **NetworkPolicy** restricting pod-to-pod traffic: frontend open to all, API only from frontend, Redis only from API (enabled in production)
- **Non-root containers** (UID 1000) with `runAsNonRoot: true`
- **JSON-structured logging** with per-request IDs on both services
- **Failure simulation endpoints** on the API for manual alert testing

---

## Architecture

```mermaid
graph TB
    subgraph "External"
        User["👤 User / Browser"]
        Ingress["🌐 NGINX Ingress\n(production only)"]
    end

    subgraph "Application Tier – namespace: kubesight"
        Frontend["🖥️ Frontend\n(Flask / Gunicorn)\nPort 5000"]
        API["⚙️ API Service\n(Flask / Gunicorn)\nPort 5000"]
        Redis["🗄️ Redis 7-Alpine\nPort 6379 / PVC"]
    end

    subgraph "Observability – namespace: monitoring"
        Prometheus["📊 Prometheus\n(kube-prometheus-stack)"]
        Grafana["📈 Grafana\n(dashboard auto-provisioned)"]
        SMApi["ServiceMonitor – api"]
        SMFrontend["ServiceMonitor – frontend"]
        PRules["PrometheusRule\n(HighCPU / HighMemory / PodRestarts)"]
        GrafanaCM["ConfigMap\n(grafana_dashboard: '1')"]
    end

    User -->|HTTP| Ingress
    Ingress --> Frontend
    Frontend -->|GET /| API
    API -->|INCR visits| Redis

    SMApi -->|scrape /metrics 30s| Prometheus
    SMFrontend -->|scrape /metrics 30s| Prometheus
    PRules -->|alert rules| Prometheus
    GrafanaCM -->|sidecar auto-provision| Grafana
    Prometheus -->|datasource| Grafana
```

---

## Technology Stack

| Category | Technology |
|---|---|
| **Container Runtime** | Docker |
| **Orchestration** | Kubernetes (Kind for local dev) |
| **Package Manager** | Helm 3 |
| **API Service** | Python 3.11, Flask 2.3, Gunicorn |
| **Frontend Service** | Python 3.11, Flask 2.3, Gunicorn |
| **Cache / Storage** | Redis 7 (Alpine), PVC-backed |
| **Metrics Collection** | Prometheus via kube-prometheus-stack |
| **Metrics Library** | prometheus_client (Python) |
| **Visualization** | Grafana 10 (auto-provisioned) |
| **Helm Validation** | GitHub Actions (helm lint + helm template) |
| **Local Dev** | Docker Compose |

---

## Project Structure

```
kubesight-production-observability/
├── .github/workflows/
│   └── helm-lint.yml              # Helm lint + template validation (3 envs)
├── app/
│   ├── api/
│   │   ├── app.py                 # Flask API: metrics, Redis, health, simulate/*
│   │   ├── Dockerfile             # Non-root (appuser), Gunicorn
│   │   └── requirements.txt
│   └── frontend/
│       ├── app.py                 # Flask Frontend: calls API, page view metrics
│       ├── Dockerfile
│       └── requirements.txt
├── kubesight-chart/
│   ├── Chart.yaml                 # v0.1.0
│   ├── values.yaml                # Default / dev values
│   ├── values-dev.yaml            # Dev overrides
│   ├── values-production.yaml     # Production: 3 replicas, HPA, PDB, NetworkPolicy
│   ├── grafana-dashboard.json     # Dashboard definition (embedded into ConfigMap)
│   └── templates/                 # 20+ Helm templates
│       ├── api-deployment.yaml    # Probes, security context, checksum annotations
│       ├── frontend-deployment.yaml
│       ├── redis-deployment.yaml
│       ├── hpa.yaml               # CPU-based HPA for API + Frontend
│       ├── pdb.yaml               # PDB for API, Frontend, Redis
│       ├── networkpolicy.yaml     # Ingress rules: open→frontend, frontend→api, api→redis
│       ├── servicemonitor.yaml    # Prometheus scraping CRDs
│       ├── prometheusrule.yaml    # Alert rules (production)
│       ├── grafana-dashboard-configmap.yaml
│       └── ...services, ingress, rbac, secret, configmap
├── kubernetes/
│   └── kind-cluster-config.yaml
├── docs/                          # Architecture, Deployment, Monitoring, Metrics…
├── prompts/                       # AI prompts used during development
├── screenshots/                   # Add after deploying (see screenshots/README.md)
└── docker-compose.yml
```

---

## Features

### Application

| Feature | Detail |
|---|---|
| API endpoints | `/` (visit counter), `/health`, `/version`, `/metrics` |
| Frontend endpoints | `/` (HTML page), `/health`, `/version`, `/metrics` |
| Simulation endpoints (API only) | `/simulate/error`, `/simulate/slow`, `/simulate/cpu`, `/simulate/redis-down` |
| Redis counter | `INCR visits` on every `GET /` request |
| JSON logging | Structured JSON logs with per-request IDs on both services |
| Non-root containers | `runAsUser: 1000`, `runAsNonRoot: true` on all pods |

### Helm Chart

| Feature | Status |
|---|---|
| 20+ templates | ✅ api, frontend, redis (deploy + svc + pvc), ingress, hpa, pdb, networkpolicy, serviceaccount, role, rolebinding, configmap, secret, servicemonitor, prometheusrule, grafana-dashboard-configmap |
| Multi-env values | ✅ default / dev / production |
| RollingUpdate strategy | ✅ configurable maxSurge/maxUnavailable |
| Startup + liveness + readiness probes | ✅ on API and Frontend (hit `/health`) |
| HPA (CPU) | ✅ API + Frontend, enabled in production |
| PDB | ✅ API + Frontend + Redis |
| NetworkPolicy | ✅ open→frontend, frontend→api, api→redis isolation, enabled in production |
| Topology spread constraints | ✅ template configurable via values (zone key) |
| Checksum annotations | ✅ pod restart on ConfigMap/Secret change |
| Helm tests | ✅ unit tests in `kubesight-chart/tests/`, connection test hook in `templates/tests/` |

### Observability

| Feature | Detail |
|---|---|
| ServiceMonitors | API + Frontend, scrape `/metrics` every 30s |
| PrometheusRules | HighCPUUsage, HighMemoryUsage, PodRestarts |
| Grafana dashboard | Auto-provisioned via ConfigMap sidecar, no manual import |
| Dashboard panels | Request rate, latency (p50/p95/p99), Redis ops, error rate, pod resources |

---

## Deployment

### Prerequisites

- Docker Desktop
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Helm 3](https://helm.sh/docs/intro/install/)
- [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/)

### Option A – Docker Compose (local, no Kubernetes)

```bash
git clone https://github.com/samkeerthana98/kubesight-production-observability.git
cd kubesight-production-observability
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5001 |
| API | http://localhost:5000 |

### Option B – Kubernetes with Helm

```bash
# 1. Create Kind cluster
kind create cluster --config kubernetes/kind-cluster-config.yaml --name kubesight

# 2. Install kube-prometheus-stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.sidecar.dashboards.enabled=true \
  --set grafana.sidecar.dashboards.label=grafana_dashboard

# 3. Deploy KubeSight (dev)
helm install kubesight ./kubesight-chart \
  --namespace kubesight --create-namespace \
  -f ./kubesight-chart/values-dev.yaml

# 4. Verify
kubectl get pods -n kubesight
helm test kubesight -n kubesight

# 5. Access services
kubectl port-forward svc/kubesight-frontend 5001:5000 -n kubesight
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring
kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring
```

Grafana: http://localhost:3000 — credentials `admin / prom-operator`

---

## Monitoring

### ServiceMonitors

Both services expose `/metrics` and are scraped automatically:

- `kubesight-api` — every 30s
- `kubesight-frontend` — every 30s

The `release: kube-prometheus-stack` label on each ServiceMonitor is required for Prometheus to discover them.

### PrometheusRule Alerts (enabled in production values)

| Alert | Condition | Severity |
|---|---|---|
| `HighCPUUsage` | CPU > 80% of limit for 5m | warning |
| `HighMemoryUsage` | Memory working set > 80% of limit for 5m | warning |
| `PodRestarts` | Restart count increased in last 5m | warning |

### Grafana Dashboard

Auto-provisioned via a ConfigMap with label `grafana_dashboard: "1"` deployed to the `monitoring` namespace. The Grafana sidecar detects it and loads it automatically.

Dashboard panels: HTTP request rate, latency percentiles (p50/p95/p99), Redis operation count, error rate, pod CPU/memory usage.

---

## Prometheus Metrics

### API Service

| Metric | Type | Labels |
|---|---|---|
| `api_http_requests_total` | Counter | method, endpoint, http_status |
| `api_http_request_duration_seconds` | Histogram | method, endpoint |
| `redis_operations_total` | Counter | operation, status, key |

### Frontend Service

| Metric | Type | Labels |
|---|---|---|
| `frontend_http_requests_total` | Counter | method, endpoint, http_status |
| `frontend_http_request_duration_seconds` | Histogram | method, endpoint |
| `frontend_page_views_total` | Counter | page, http_status |

---

## Multi-Environment Configuration

| Feature | Dev | Production |
|---|---|---|
| Replicas | 1 | 3 |
| HPA | Disabled | Enabled (3–10, target CPU 70%) |
| PDB | minAvailable: 1 | minAvailable: 2 |
| NetworkPolicy | Disabled | Enabled |
| PrometheusRule | Disabled | Enabled |
| Redis PVC | 1Gi | 10Gi |
| Ingress | Disabled | Enabled (nginx) |
| CPU limit | 500m | 1000m |
| Memory limit | 512Mi | 1Gi |

---

## Screenshots

Screenshots are not yet included. Deploy the project and capture them following the instructions in [`screenshots/README.md`](./screenshots/README.md).

Required: Grafana dashboard, Prometheus targets (`/targets`), `kubectl get pods` output, Helm deployment output.

---

## Resume Highlights

- Designed and deployed a **production Kubernetes observability platform** using Helm, Prometheus, and Grafana on a Kind cluster
- Authored a **20+ template Helm chart** with multi-environment values (dev/production), HPA, PDB, and NetworkPolicy
- Implemented **custom Prometheus metrics** (Counters, Histograms) in Python Flask and configured **ServiceMonitor CRDs** for automatic scraping via kube-prometheus-stack
- Built a **Grafana dashboard** (auto-provisioned via ConfigMap sidecar) displaying request rates, latency percentiles, Redis operation health, and pod resource utilization
- Configured **PrometheusRule alert rules** for HighCPU, HighMemory, and PodRestarts with severity labels
- Implemented **zero-downtime rolling deployments** with startup, liveness, and readiness probes, PodDisruptionBudgets, and checksum-based config-change restarts
- Applied **container security hardening**: non-root users (UID 1000) and NetworkPolicies
- Added a **GitHub Actions workflow** for automated Helm lint and template validation across all three environment value files on every push

---

## Future Improvements

- [ ] Push Docker images to ECR / Docker Hub via GitHub Actions
- [ ] Add OpenTelemetry tracing (Jaeger / Tempo)
- [ ] Configure AlertManager receivers (Slack / PagerDuty)
- [ ] Terraform module for EKS cluster provisioning
- [ ] Add Vault for secret management
- [ ] Implement canary deployments with Argo Rollouts
- [ ] Publish Helm chart to GitHub Pages as a chart repository

---

## License

MIT — see [LICENSE](./LICENSE)
