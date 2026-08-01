# Helm Chart Prompts

Prompts used during the development and debugging of the KubeSight Helm chart.

---

## Chart Structure Design

```
Design a production-grade Helm chart for a Python Flask microservices application
with the following components:
- API service (Flask + Gunicorn)
- Frontend service (Flask + Gunicorn)
- Redis (cache + counter)

Requirements:
- Multi-environment values (dev, production)
- HPA with CPU-based autoscaling
- PodDisruptionBudget
- NetworkPolicy
- RBAC (Role, RoleBinding, ServiceAccount)
- Topology spread constraints
- RollingUpdate deployment strategy
- Startup, liveness, and readiness probes
- Helm tests

Use Helm best practices and Kubernetes 1.28+ API versions.
```

---

## Values File Structure

```
Create a structured values.yaml for the KubeSight Helm chart with:
- Global image settings (registry, tag, pullPolicy)
- Per-component overrides (api, frontend, redis)
- Resource requests and limits
- Probe configuration (liveness, readiness, startup)
- Autoscaling configuration
- Monitoring section (serviceMonitor, prometheusRule)
- Grafana dashboard section
- Ingress configuration with TLS
- NetworkPolicy toggle
- PDB configuration
- Topology spread constraints

Ensure values are sensible defaults for a development environment.
```

---

## Production Values Override

```
Create a values-production.yaml that overrides the default values with:
- replicaCount: 3
- HPA enabled (min: 3, max: 10, targetCPU: 70%)
- PDB minAvailable: 2
- NetworkPolicy enabled
- PrometheusRule enabled
- Redis PVC: 10Gi
- Ingress enabled with nginx class and TLS
- Higher CPU/memory limits
- priorityClassName: high-priority

Follow Kubernetes production best practices.
```

---

## Helm Helper Templates

```
Create _helpers.tpl for the KubeSight Helm chart with these named templates:
- kubesight.name
- kubesight.fullname
- kubesight.chart
- kubesight.labels (standard Helm labels)
- kubesight.selectorLabels
- kubesight.serviceAccountName
- kubesight.includeConfigMap (sha256sum for checksum annotation)
- kubesight.includeSecret (sha256sum for checksum annotation)

Include the Helm license header.
```

---

## Deployment Template

```
Create an api-deployment.yaml Helm template with:
- RollingUpdate strategy from values
- Topology spread constraints (conditional)
- Non-root security context (runAsUser: 1000)
- Environment variables from ConfigMap and Secret
- Redis connection env vars from the fullname helper
- Startup + liveness + readiness probes (all from values)
- Checksum annotations for ConfigMap and Secret (force restart on config change)
- Conditional lifecycle hooks
- Conditional APM agent comments
- initContainers, hostAliases from values
- terminationGracePeriodSeconds from values
```

---

## Helm Lint Debugging

```
The following helm lint error appears:
[ERROR] templates/: <error message here>

Analyze the error and provide the fix. The chart is for a production
Kubernetes application with ServiceMonitor CRDs from prometheus-operator.
Consider that CRD types (monitoring.coreos.com/v1) may not be available
during lint and require --set flags or schema validation workarounds.
```

---

## Helm Test Templates

```
Create Helm test files for the KubeSight chart:
- api-deployment_test.yaml: validate API deployment has correct image, probes, env vars
- frontend-deployment_test.yaml: same for frontend
- api-service_test.yaml: validate service port and selector
- frontend-service_test.yaml: same for frontend
- redis-service_test.yaml: validate redis service
- pdb_test.yaml: validate PDB minAvailable
- configmap_test.yaml: validate required keys exist
- secret_test.yaml: validate required keys exist
- ingress_test.yaml: validate ingress host (requires ingress-values.yaml override)

Use helm-unittest framework (helm.sh/chart-testing).
```
