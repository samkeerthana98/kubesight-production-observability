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

What is implemented:

- **RollingUpdate deployments** with configurable maxSurge/maxUnavailable
- **Pod Disruption Budgets** on API, Frontend, and Redis
- **Horizontal Pod Autoscaler** (CPU-based) for API and Frontend
- **Custom Prometheus metrics** (Counters, Histograms) exposed from both services
- **ServiceMonitor CRDs** for automatic Prometheus scraping
- **PrometheusRule alerts** — HighCPU, HighMemory, PodRestarts (enabled in production)
- **Grafana dashboard auto-provisioning** via ConfigMap + Grafana sidecar
- **NetworkPolicy** — frontend open to all, API only from frontend, Redis only from API (production)
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

    subgraph "namespace: kubesight"
        Frontend["🖥️ Frontend\n(Flask / Gunicorn)\nPort 5000"]
        API["⚙️ API Service\n(Flask / Gunicorn)\nPort 5000"]
        Redis["🗄️ Redis 7-Alpine\nPort 6379 / PVC"]
        SMApi["ServiceMonitor – api"]
        SMFrontend["ServiceMonitor – frontend"]
        PRules["PrometheusRule\n(HighCPU / HighMemory / PodRestarts)"]
    end

    subgraph "namespace: monitoring"
        Prometheus["📊 Prometheus\n(kube-prometheus-stack)"]
        Grafana["📈 Grafana\n(dashboard auto-provisioned)"]
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

> ServiceMonitors and PrometheusRule are deployed in the `kubesight` namespace as part of the Helm release. The Grafana dashboard ConfigMap is deployed to the `monitoring` namespace for sidecar detection.

---

## Technology Stack

| Category | Technology |
|---|---|
| **Container Runtime** | Docker |
| **Orchestration** | Kubernetes (Kind for local dev) |
| **Package Manager** | Helm 3 |
| **API / Frontend** | Python 3.11, Flask 3.0, Gunicorn |
| **Cache / Storage** | Redis 7 (Alpine), PVC-backed |
| **Metrics** | Prometheus via kube-prometheus-stack, prometheus_client (Python) |
| **Visualization** | Grafana 10 (auto-provisioned) |
| **CI/CD** | GitHub Actions (comprehensive security + validation pipeline) |
| **Local Dev** | Docker Compose |

---

## Project Structure

```
kubesight-production-observability/
├── .github/workflows/
│   └── helm-lint.yml              # Helm lint + template validation (3 envs)
├── app/
│   ├── api/                       # Flask API: metrics, Redis, health, simulate/*
│   └── frontend/                  # Flask Frontend: calls API, page view metrics
├── kubesight-chart/
│   ├── Chart.yaml
│   ├── values.yaml                # Shared chart defaults and common configuration
│   ├── values-dev.yaml            # Dev overrides (1 replica, minimal resources)
│   ├── values-kind.yaml           # Kind/local ingress profile (HTTP, no TLS redirect)
│   ├── values-production.yaml     # Production: 3 replicas, HPA, PDB, NetworkPolicy, TLS ingress
│   ├── grafana-dashboard.json     # Dashboard JSON (embedded into ConfigMap)
│   └── templates/                 # 20 Helm templates
│       ├── api-deployment.yaml    # Probes, security context, rolling update
│       ├── frontend-deployment.yaml
│       ├── redis-deployment.yaml
│       ├── hpa.yaml               # CPU-based HPA for API + Frontend
│       ├── pdb.yaml               # PDB for API, Frontend, Redis
│       ├── networkpolicy.yaml     # open→frontend, frontend→api, api→redis
│       ├── servicemonitor.yaml    # Prometheus scraping CRDs
│       ├── prometheusrule.yaml    # Alert rules (production)
│       ├── grafana-dashboard-configmap.yaml
│       └── ...services, ingress, rbac, secret, configmap
├── kubernetes/
│   └── kind-cluster-config.yaml  # Single control-plane, port 80/443 mapped
├── docs/                          # Architecture, Deployment, Monitoring, Metrics
├── prompts/                       # AI prompts used during development
├── screenshots/
└── docker-compose.yml
```

---

## Features

### Application

| Feature | Detail |
|---|---|
| API endpoints | `/` (visit counter), `/health`, `/version`, `/metrics` |
| Frontend endpoints | `/` (HTML page), `/health`, `/version`, `/metrics` |
| Simulation endpoints | `/simulate/error`, `/simulate/slow`, `/simulate/cpu`, `/simulate/redis-down` |
| Redis counter | `INCR visits` on every `GET /` |
| JSON logging | Structured JSON logs with per-request IDs on both services |
| Non-root containers | `runAsUser: 1000`, `runAsNonRoot: true` |

### Helm Chart

| Feature | Status |
|---|---|
| 20 templates | ✅ api, frontend, redis (deploy + svc + pvc), ingress, hpa, pdb, networkpolicy, serviceaccount, role, rolebinding, configmap, secret, servicemonitor, prometheusrule, grafana-dashboard-configmap |
| Multi-env values | ✅ default / dev / kind / production |
| RollingUpdate strategy | ✅ configurable maxSurge/maxUnavailable |
| Startup + liveness + readiness probes | ✅ on API and Frontend (hit `/health`) |
| HPA (CPU) | ✅ API + Frontend, enabled in production |
| PDB | ✅ API + Frontend + Redis |
| NetworkPolicy | ✅ enabled in production |
| Topology spread constraints | ✅ configurable via values |
| Helm unit tests | ✅ `kubesight-chart/tests/` + connection test hook |

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

- Docker Desktop, kubectl, [Helm 3](https://helm.sh/docs/intro/install/), [Kind](https://kind.sigs.k8s.io/)

### Option A – Docker Compose (no Kubernetes)

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

# 3. Validate the chart
helm lint ./kubesight-chart

# 4. Deploy KubeSight on Kind (HTTP, no TLS redirect)
helm install kubesight ./kubesight-chart \
  --namespace kubesight --create-namespace \
  -f ./kubesight-chart/values-kind.yaml

# If the release already exists, upgrade instead
helm upgrade kubesight ./kubesight-chart \
  --namespace kubesight \
  -f ./kubesight-chart/values-kind.yaml

# 5. Verify
kubectl get pods -n kubesight
helm test kubesight -n kubesight

# 6. Access services
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring
kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring
```

Application: http://kubesight.example.com

Grafana: http://localhost:3000 — `admin / prom-operator`

For local Kind ingress testing, map `kubesight.example.com` to `127.0.0.1` in your hosts file and access the app over HTTP. The `values-kind.yaml` file intentionally disables ingress TLS and `ssl-redirect` so local requests do not get redirected to HTTPS.

If you previously deployed the release with autoscaling enabled, delete the old HPA resources or reinstall the release before switching to `values-kind.yaml`. Existing Redis PVCs may also prevent changing the requested storage size during upgrade if the underlying StorageClass does not support expansion.

---

## Monitoring

### ServiceMonitors

Both services expose `/metrics` and are scraped automatically every 30s. The `release: kube-prometheus-stack` label on each ServiceMonitor is required for Prometheus discovery.

### PrometheusRule Alerts (production only)

| Alert | Condition | Severity |
|---|---|---|
| `HighCPUUsage` | CPU > 80% of limit for 5m | warning |
| `HighMemoryUsage` | Memory working set > 80% of limit for 5m | warning |
| `PodRestarts` | Restart count increased in last 5m | warning |

### Grafana Dashboard

Auto-provisioned via ConfigMap with label `grafana_dashboard: "1"` in the `monitoring` namespace. Sidecar detects and loads it — no manual import needed.

Panels: HTTP request rate, latency (p50/p95/p99), Redis ops, error rate, pod CPU/memory.

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

The chart uses four values files for different purposes:

- `values.yaml` — shared chart defaults and common configuration used as the base for all environments
- `values-dev.yaml` — lightweight development profile for Kubernetes without production-only features
- `values-kind.yaml` — local Kind profile with ingress enabled over plain HTTP and TLS redirect disabled
- `values-production.yaml` — production profile with autoscaling, NetworkPolicy, PrometheusRule, and TLS-enabled ingress

| Feature | Dev | Kind | Production |
|---|---|---|---|
| Base file | `values-dev.yaml` | `values-kind.yaml` | `values-production.yaml` |
| Replicas | 1 | 1 | 3 |
| HPA | Disabled | Disabled | Enabled (3–10, target CPU 70%) |
| PDB | minAvailable: 1 | Uses chart defaults | minAvailable: 2 |
| NetworkPolicy | Disabled | Uses chart defaults | Enabled |
| PrometheusRule | Disabled | Uses chart defaults | Enabled |
| Redis PVC | 1Gi | Uses chart defaults | 10Gi |
| Ingress | Disabled | Enabled (nginx, HTTP only) | Enabled (nginx, TLS) |
| TLS redirect | Disabled | Disabled | Enabled |
| CPU limit | 500m | Uses chart defaults | 1000m |
| Memory limit | 512Mi | Uses chart defaults | 1Gi |

---

## Screenshots

| Screenshot | File |
|---|---|
| Grafana Dashboard | `screenshots/grafana-dashboard.png` |
| Prometheus Targets | `screenshots/prometheus-targets.png` |
| Prometheus Metrics | `screenshots/prometheus-metrics.png` |
| Helm Deploy + Pods | `screenshots/helm-deploy.png`, `screenshots/pods-running.png` |

---

## Future Improvements

- [ ] Push Docker images to ECR / Docker Hub via GitHub Actions
- [ ] Add OpenTelemetry tracing (Jaeger / Tempo)
- [ ] Configure AlertManager receivers (Slack / PagerDuty)
- [ ] Terraform module for EKS cluster provisioning
- [ ] Implement canary deployments with Argo Rollouts

---

## CI/CD Pipeline

The repository uses a comprehensive GitHub Actions CI/CD pipeline that validates all aspects of the application, including Helm charts, Docker images, security scanning, and Kubernetes manifests.

### Active GitHub Actions Checks

| Check | Purpose | Scope |
|-------|---------|-------|
| **Helm Lint** | Validates Helm chart syntax and best practices | All environments (default, dev, production) |
| **Helm Template Validation** | Ensures templates render correctly with all value files | Multi-environment validation |
| **Kubeconform Validation** | Validates rendered Kubernetes manifests against Kubernetes 1.28.0 API | Production manifests |
| **Trivy Filesystem Scan** | Scans repository files for HIGH/CRITICAL vulnerabilities | Full repository |
| **Trivy Docker Image Scan** | Scans built Docker images for HIGH/CRITICAL vulnerabilities | API and Frontend images |
| **Gitleaks Secret Detection** | Scans for leaked secrets and credentials | Full repository |
| **Kubesec Security Validation** | Validates Kubernetes manifests for security best practices | Production manifests |

### Pipeline Triggering

The CI/CD pipeline automatically triggers on:
- Push to `main` or `develop` branches
- Pull requests targeting `main` or `develop` branches
- Changes to Helm chart files, application code, or workflow configuration

---

## Docker Image Security

### Security Improvements

The Docker images have been hardened with comprehensive security measures:

| Security Measure | Implementation | Status |
|-----------------|----------------|--------|
| **Base Image** | Python 3.11-slim (latest stable) | ✅ Maintained |
| **OS Security Updates** | `apt-get update && apt-get upgrade -y` during build | ✅ Applied |
| **Python Dependencies** | setuptools >=78.1.1, wheel >=0.46.2 | ✅ Updated |
| **Non-root User** | Runs as UID 1000 with `runAsNonRoot: true` | ✅ Configured |
| **Trivy Scanning** | HIGH/CRITICAL severity blocking enabled | ✅ Active |

### Current Security Status

**Latest Trivy Scan Results:**
- **API Image**: 0 HIGH/CRITICAL vulnerabilities
- **Frontend Image**: 0 HIGH/CRITICAL vulnerabilities
- **Scan Frequency**: Every push and PR
- **Blocking Policy**: Pipeline fails on HIGH/CRITICAL findings

### Vulnerability Remediation

Recent security fixes included:
- Upgraded base image from `python:3.11.11-slim` to `python:3.11-slim`
- Added automated OS package updates during Docker build
- Upgraded setuptools from 65.5.1 to 84.0.0
- Upgraded wheel from 0.45.1 to 0.48.0
- Fixed Dockerfile ENV format warnings

---

## Production Validation

The platform has been validated through comprehensive production testing scenarios:

### Resilience Testing Results

| Test Scenario | Status | Details |
|--------------|--------|---------|
| **Pod Failure Recovery** | ✅ Verified | Pods automatically restarted with 0 downtime |
| **Redis Persistence** | ✅ Verified | Data persisted across pod restarts via PVC |
| **Rolling Restart** | ✅ Verified | Zero-downtime rolling updates with proper pod lifecycle |
| **Prometheus Scraping** | ✅ Verified | ServiceMonitors successfully scrape metrics every 30s |
| **Helm Upgrade/Rollback** | ✅ Verified | Both upgrade and rollback operations validated |
| **Production Template Validation** | ✅ Verified | Helm templates render correctly with production values |

### Production Configuration Validation

| Configuration | Production Setting | Validation Status |
|---------------|-------------------|-------------------|
| **Replicas** | 3 | ✅ Correct |
| **HPA** | Enabled (3-10 replicas, 70% CPU target) | ✅ Configured |
| **PDB** | minAvailable: 2 | ✅ Enforcing availability |
| **NetworkPolicy** | Enabled (strict traffic controls) | ✅ Security enforced |
| **PrometheusRule** | Enabled (HighCPU, HighMemory, PodRestarts) | ✅ Alerting active |
| **Ingress TLS** | Enabled with TLS redirect | ✅ Secure |
| **Resource Limits** | CPU: 1000m, Memory: 1Gi | ✅ Applied |

---

## Security & Production Readiness

### Security Checklist

- ✅ **Container Security**: Non-root containers, minimal base images, security scanning
- ✅ **Network Security**: NetworkPolicy-enforced traffic segmentation
- ✅ **Secrets Management**: Kubernetes Secrets for sensitive data
- ✅ **Image Scanning**: Trivy HIGH/CRITICAL blocking in CI/CD
- ✅ **Secret Detection**: Gitleaks scanning for leaked credentials
- ✅ **Vulnerability Management**: Automated dependency updates and scanning
- ✅ **RBAC**: Least-privilege service accounts and role bindings

### Production Readiness Checklist

- ✅ **High Availability**: RollingUpdate deployments, PDB, HPA
- ✅ **Observability**: Prometheus metrics, Grafana dashboards, alerting rules
- ✅ **Configuration Management**: Multi-environment Helm values
- ✅ **Resource Management**: CPU/memory limits and requests
- ✅ **Storage**: Persistent volumes for Redis data persistence
- ✅ **Ingress**: TLS-enabled ingress with proper routing
- ✅ **CI/CD**: Automated testing, validation, and deployment pipeline
- ✅ **Documentation**: Comprehensive README and inline documentation

---

## Continuous Integration

GitHub Actions validates the Helm chart on pushes and pull requests affecting `kubesight-chart/`, `app/`, or workflow files.
The workflow runs comprehensive validation including Helm lint/template validation, Kubernetes manifest validation, security scanning (Trivy, Gitleaks, Kubesec), and Docker image security scanning across all environments.

---

## License

MIT — see [LICENSE](./LICENSE)
