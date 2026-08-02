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
- HPA with CPU-based autoscaling (autoscaling/v2)
- PodDisruptionBudget (policy/v1)
- NetworkPolicy (ingress-only rules per component)
- RBAC (ServiceAccount, Role, RoleBinding)
- Topology spread constraints (zone-aware, configurable via values)
- RollingUpdate deployment strategy
- Startup, liveness, and readiness probes on API and Frontend
- Helm unit tests (helm-unittest framework)
- Helm test connection hook

Use Helm best practices and Kubernetes 1.28+ API versions.
```

---

## Values File Structure

```
Create a structured values.yaml for the KubeSight Helm chart with:
- replicaCount (global)
- Per-component image, service port, resources, probes (api / frontend / redis)
- Probe sub-keys: liveness, readiness, startup (initialDelaySeconds, periodSeconds,
  timeoutSeconds, successThreshold, failureThreshold)
- Autoscaling section (enabled, minReplicas, maxReplicas, targetCPUUtilizationPercentage)
- Monitoring section (serviceMonitor.enabled/interval/scrapeTimeout, prometheusRule.enabled)
- grafanaDashboard section (enabled, namespace)
- Ingress section (enabled, className, annotations, hosts, tls, backend)
- NetworkPolicy toggle (enabled)
- PDB section (enabled, minAvailable)
- Topology spread constraints section (enabled, maxSkew, topologyKey, whenUnsatisfiable)
- Deployment strategy section (type, rollingUpdate.maxUnavailable/maxSurge)
- common env vars block (VERBOSE, VERSION, COMMIT_SHA, ENVIRONMENT)
- secret block (JWT_SECRET, REDIS_PASSWORD)
- RBAC section (create)
- testConnection section (enabled)

Defaults should be suitable for a development environment (1 replica, HPA off,
NetworkPolicy off, PrometheusRule off).
```

---

## Production Values Override

```
Create values-production.yaml that overrides defaults with:
- replicaCount: 3
- HPA enabled (minReplicas: 3, maxReplicas: 10, targetCPUUtilizationPercentage: 70)
- PDB minAvailable: 2
- NetworkPolicy enabled
- PrometheusRule enabled
- Redis PVC size: 10Gi
- Ingress enabled with className: nginx and TLS
  (use secretName, not secretId, in the tls block)
- CPU limit: 1000m, memory limit: 1Gi
- priorityClassName: high-priority
- ENVIRONMENT: production

Follow Kubernetes production best practices.
```

---

## Helm Helper Templates

```
Create _helpers.tpl for the KubeSight Helm chart with:
- kubesight.name
- kubesight.fullname (supports fullnameOverride and nameOverride)
- kubesight.chart
- kubesight.labels (helm.sh/chart, app.kubernetes.io/name, instance, version, managed-by)
- kubesight.selectorLabels (name + instance only)
- kubesight.serviceAccountName

For checksum annotations (to force pod restart on config change), use:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
  checksum/secret: {{ include (print $.Template.BasePath "/secret.yaml") . | sha256sum }}

Note: .Files.Get cannot read files inside the templates/ directory.
Use include + print $.Template.BasePath instead.
```

---

## Deployment Template

```
Create api-deployment.yaml Helm template with:
- RollingUpdate strategy from .Values.deploymentStrategy
- Non-root security context: runAsNonRoot: true, runAsUser: 1000 (container level)
- podSecurityContext from .Values.podSecurityContext (fsGroup: 2000)
- Environment variables: loop over .Values.api.env, then hardcoded REDIS_HOST
  (built with printf "%s-redis" (include "kubesight.fullname" $)) and REDIS_PORT
- envFrom: configMapRef and secretRef using fullname helper
- Startup + liveness + readiness probes all pointing to /health
- All probe fields (initialDelaySeconds, periodSeconds, timeoutSeconds,
  successThreshold, failureThreshold) driven from .Values.api.probes.*
- Conditional lifecycle hooks (.Values.api.lifecycle.enabled)
- initContainers, hostAliases, tolerations, affinity from values (with)
- topologySpreadConstraints block conditional on .Values.topologySpreadConstraints.enabled
- terminationGracePeriodSeconds from values
- Checksum annotations on pod template metadata

Important: priorityClassName and dnsPolicy belong inside spec.template.spec
(the pod spec), not inside spec (the Deployment spec).
```

---

## YAML Indentation Issues Found

```
The following YAML indentation bugs were found in the KubeSight Helm templates
and had to be debugged:

1. api-deployment.yaml / redis-deployment.yaml:
   priorityClassName and dnsPolicy were placed at spec level of the Deployment.
   They belong inside spec.template.spec (pod spec).
   Wrong:
     spec:
       priorityClassName: ...
       dnsPolicy: ...
       strategy: ...
   Correct:
     spec:
       strategy: ...
       template:
         spec:
           priorityClassName: ...
           dnsPolicy: ...

2. _helpers.tpl checksum helpers:
   kubesight.includeConfigMap used .Files.Get on the templates/ path.
   Helm does not allow .Files.Get to read files from templates/.
   Wrong: {{ .Files.Get (printf "%s/configmap.yaml" .Path) | sha256sum }}
   Correct: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}

3. values-production.yaml ingress TLS:
   Used secretId instead of the correct Kubernetes field secretName.
   Wrong:  - secretId: kubesight-tls
   Correct: - secretName: kubesight-tls

Explain each bug, why it causes a silent failure or incorrect render,
and provide the corrected YAML.
```

---

## Helm Test Templates

```
Create Helm unit test files for the KubeSight chart using helm-unittest.

Test files needed:
- api-deployment_test.yaml: kind, name, labels, replicas, selector, image, port
- frontend-deployment_test.yaml: same as api
- redis-deployment_test.yaml: kind, name, labels, replicas, image (redis:7-alpine), port 6379
- api-service_test.yaml: kind, name, port 5000, targetPort 5000
- frontend-service_test.yaml: kind, name, port 5000, targetPort 5000
- redis-service_test.yaml: kind, name, port 6379, targetPort 6379
- pdb_test.yaml: three documents (api, frontend, redis) using documentIndex
- secret_test.yaml: stringData.JWT_SECRET and stringData.REDIS_PASSWORD using set:
- configmap_test.yaml: kind and name
- ingress_test.yaml: uses separate ingress-values.yaml, validates host, path, TLS secretName

Each suite sets release.name: test-release and uses the templates: list.
```
