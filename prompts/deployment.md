# Deployment Prompts

Prompts used during the deployment, configuration, and automation of KubeSight.

---

## Kind Cluster Configuration

```
Create a Kind cluster configuration for local Kubernetes development.

Requirements:
- 1 control-plane node
- Label the node ingress-ready=true (required for NGINX ingress controller)
- Direct port mappings on the control-plane node:
    containerPort: 80  → hostPort: 80  (HTTP ingress)
    containerPort: 443 → hostPort: 443 (HTTPS ingress)
- No worker nodes (single-node cluster for local dev)

Provide:
- kind-cluster-config.yaml using kind.x-k8s.io/v1alpha4
- The kind create cluster command with --config and --name flags

Note: topology spread constraints by zone will not function on a single-node
cluster since no zone labels exist on the node.
```

---

## Docker Compose Local Development

```
Create docker-compose.yml for local development (no Kubernetes).

Services:
1. redis: image redis:7-alpine
   - Expose port 6379
   - Named volume redis_data mounted at /data

2. api: build from ./app/api
   - Expose port 5000:5000
   - Environment: REDIS_HOST=redis, REDIS_PORT=6379
   - depends_on: redis

3. frontend: build from ./app/frontend
   - Expose port 5001:5000
   - Environment: API_SERVICE_HOST=api, API_SERVICE_PORT=5000
   - depends_on: api

Use docker compose v2 syntax (no version key at top).
Named volumes section at bottom: redis_data.
```

---

## Dockerfile Best Practices

```
Create a production Dockerfile for a Python Flask application.

Requirements:
1. Base image: python:3.11-slim
2. Create non-root user: groupadd -r appuser && useradd -r -g appuser appuser
3. WORKDIR /app
4. Copy requirements.txt first (layer caching), then pip install --no-cache-dir
5. Copy application source
6. chown -R appuser:appuser /app
7. Switch to: USER appuser
8. EXPOSE 5000
9. CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

.dockerignore should exclude:
__pycache__, *.pyc, .venv, .env, .pytest_cache, *.log,
Dockerfile, docker-compose.yml, README.md
```

---

## GitHub Actions Helm CI

```
Create .github/workflows/helm-lint.yml for Helm chart validation.

Trigger: push and pull_request on main and develop branches,
only when paths kubesight-chart/** or the workflow file itself change.

Job 1 — helm-lint:
  runs-on: ubuntu-latest
  steps: checkout (actions/checkout@v4), install Helm (azure/setup-helm@v4, version 3.14.0),
  then run helm lint against:
  - ./kubesight-chart (default values)
  - ./kubesight-chart -f values-dev.yaml
  - ./kubesight-chart -f values-production.yaml

Job 2 — helm-template (needs: helm-lint):
  Same setup, then:
  - helm template with default, dev, and production values
  - Verify key resources are present in the production render by grepping for:
    Deployment, Service, ServiceMonitor, PrometheusRule, grafana_dashboard,
    HorizontalPodAutoscaler, PodDisruptionBudget, NetworkPolicy

Fail the workflow if any step exits non-zero.
```

---

## Zero-Downtime Deployment Strategy

```
Configure zero-downtime deployments for KubeSight.

Deployment strategy in values.yaml:
  deploymentStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 25%
      maxSurge: 25%

Combined with:
- readinessProbe: new pods receive traffic only after /health returns 200
- PDB minAvailable: 2 (production) — prevents draining too many pods at once
- terminationGracePeriodSeconds: 30 — Kubernetes waits 30s for in-flight requests
  before sending SIGKILL after SIGTERM

How rolling update works with readiness probes:
1. New pod starts, startupProbe runs (up to 155s grace period)
2. Once startup passes, readinessProbe runs every 5s
3. Pod is added to Service endpoints only when readinessProbe passes
4. Old pod receives SIGTERM, finishes current requests within 30s, then exits
```

---

## Kubernetes RBAC for KubeSight

```
Create minimal RBAC for KubeSight.

Templates needed:
1. serviceaccount.yaml — conditional on .Values.serviceAccount.create
2. role.yaml — conditional on .Values.rbac.create
   Kind: Role (namespace-scoped, not ClusterRole)
   rules: currently empty — extend with get/watch/list on pods and services
   if the application needs to introspect cluster state
3. rolebinding.yaml — conditional on .Values.rbac.create
   Binds the Role to the ServiceAccount in .Release.Namespace

Why Role not ClusterRole:
KubeSight pods only need access within their own namespace. ClusterRole would
grant permissions across all namespaces, violating least-privilege.
```
