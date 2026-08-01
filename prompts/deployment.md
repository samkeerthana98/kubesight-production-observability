# Deployment Prompts

Prompts used during the deployment, configuration, and automation of KubeSight.

---

## Kind Cluster Configuration

```
Create a Kind cluster configuration for local Kubernetes development.

Requirements:
- 1 control-plane node
- 2 worker nodes
- Port mappings: 80 → 30080, 443 → 30443 (for ingress)
- Extra port mapping for NodePort services
- Label worker nodes for topology spread constraints:
    topology.kubernetes.io/zone: zone-a / zone-b

Provide the kind-cluster-config.yaml file and the kind create cluster command.
```

---

## Docker Compose Local Development

```
Create a docker-compose.yml for local development of KubeSight.

Services:
1. redis: redis:7-alpine
   - Expose port 6379
   - Named volume for persistence

2. api: build from ./app/api
   - Expose port 5000
   - Set env vars: REDIS_HOST=redis, REDIS_PORT=6379
   - Depends on redis

3. frontend: build from ./app/frontend
   - Expose port 5001 → 5000
   - Set env vars: API_SERVICE_HOST=api, API_SERVICE_PORT=5000
   - Depends on api

Use docker compose v2 syntax (no version key).
```

---

## Dockerfile Best Practices

```
Review and improve this Dockerfile for a Python Flask application:

FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]

Apply best practices:
1. Use slim base image
2. Create and use a non-root user (appuser, UID 1000)
3. Copy requirements.txt before source code (layer caching)
4. Use --no-cache-dir for pip
5. Use gunicorn instead of python app.py
6. Add .dockerignore recommendations
```

---

## GitHub Actions Helm CI

```
Create a GitHub Actions workflow for Helm chart validation.

Filename: .github/workflows/helm-lint.yml

Requirements:
- Trigger on: push and pull_request to main and develop branches
- Jobs:
  1. helm-lint: checkout, install helm, run helm lint
  2. helm-template: run helm template and validate output
  3. Fail the workflow if any step fails

Use the latest stable versions of:
- actions/checkout
- azure/setup-helm

Run lint against: ./kubesight-chart
Run template against: ./kubesight-chart with default values
```

---

## Helm Install kube-prometheus-stack

```
Provide the complete helm install command for kube-prometheus-stack with:
- Namespace: monitoring
- Grafana sidecar dashboards enabled
- Dashboard label: grafana_dashboard
- Persistent storage for Prometheus (10Gi)
- Persistent storage for Grafana (5Gi)
- AlertManager enabled
- Node exporter enabled

Also provide:
- How to get the Grafana admin password
- How to verify all pods are Running
- How to access Prometheus, Grafana, AlertManager UIs
```

---

## Zero-Downtime Deployment Strategy

```
Explain and configure a zero-downtime deployment strategy for KubeSight.

Requirements:
1. RollingUpdate with maxUnavailable: 25%, maxSurge: 25%
2. PodDisruptionBudget minAvailable: 2 (production)
3. Readiness probe must pass before traffic is sent to new pods
4. terminationGracePeriodSeconds: 30 for graceful shutdown
5. SIGTERM handler in Flask (if needed)

Explain:
- How RollingUpdate interacts with readiness probes
- Why maxUnavailable and maxSurge are both needed
- What happens when a deployment is paused mid-rollout
- How to rollback if the new version is unhealthy
```

---

## Kubernetes RBAC for KubeSight

```
Create the minimal RBAC configuration for KubeSight.

Requirements:
- ServiceAccount: kubesight
- Role (not ClusterRole) – namespace-scoped
  - Resources: pods, services
  - Verbs: get, watch, list
- RoleBinding: bind the Role to the ServiceAccount

Wrap in Helm conditionals:
- {{- if .Values.serviceAccount.create }} for ServiceAccount
- {{- if .Values.rbac.create }} for Role and RoleBinding

Explain why ClusterRole is not needed for this use case.
```
