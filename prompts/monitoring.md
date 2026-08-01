# Monitoring & Observability Prompts

Prompts used during the design and implementation of the KubeSight observability stack.

---

## Observability Stack Design

```
Design a complete observability stack for a production Kubernetes application
using the kube-prometheus-stack (Prometheus Operator + Grafana + AlertManager).

Application: KubeSight (Python Flask API + Frontend + Redis)
Cluster: Kind (local), EKS/GKE ready

Requirements:
1. Metrics collection via ServiceMonitors (CRD)
2. Custom application metrics (Counters, Histograms)
3. Alerting rules via PrometheusRules (CRD)
4. Grafana dashboard auto-provisioning
5. AlertManager for alert routing

Describe:
- Component installation order
- Namespace layout
- Label conventions for Prometheus discovery
- How ServiceMonitors connect to Prometheus
```

---

## kube-prometheus-stack Installation

```
Provide the correct helm install command for kube-prometheus-stack with:
1. Grafana sidecar enabled for dashboard auto-provisioning
2. Dashboard sidecar label set to "grafana_dashboard"
3. AlertManager enabled
4. Prometheus retention: 7 days
5. Install into the monitoring namespace

Also explain what each flag does and why it's needed.
```

---

## JSON Structured Logging in Flask

```
Implement structured JSON logging in a Python Flask application.

Requirements:
- All logs must be JSON format (for log aggregation tools)
- Include fields: timestamp, service, request_id, endpoint, status, duration, level, message
- Generate or extract X-Request-ID from request headers
- Propagate request_id to outgoing HTTP calls
- Use before_request / after_request hooks
- Handle teardown_request for exception logging
- No None values in log output (omit null fields)

Service name: "api"
```

---

## Health Check Endpoints

```
Design health check endpoints for a Kubernetes-deployed Flask application.

Requirements:
1. GET /health
   - Returns HTTP 200 if healthy, 503 if unhealthy
   - Checks Redis connection (ping)
   - Returns JSON with: status, service, timestamp, message, redis.status

2. GET /version
   - Returns JSON with: service, version, commit, environment, timestamp
   - Reads VERSION, COMMIT_SHA, ENVIRONMENT from environment variables

These endpoints are used by Kubernetes liveness and readiness probes.
Ensure the health endpoint does NOT update metrics (avoid probe noise).
```

---

## Simulation Endpoints for Alert Testing

```
Create Flask endpoints to simulate failure scenarios for testing Prometheus alerts:

1. GET /simulate/error
   - Raises a Python exception (triggers 500 response)
   - Used to test error rate alerts

2. GET /simulate/slow
   - Sleeps for 2 seconds before responding
   - Used to test latency alerts

3. GET /simulate/cpu
   - Runs a CPU-intensive loop for 1.5 seconds
   - Used to test HighCPU alerts

4. GET /simulate/redis-down
   - Simulates a Redis connection failure
   - Returns 500 with JSON error response
   - Updates redis_operations_total{status="error"} metric

All endpoints should return consistent JSON format and log the simulation.
```

---

## Probe Configuration

```
Configure Kubernetes startup, liveness, and readiness probes for a Flask
application that:
- Takes up to 30 seconds to start (including Redis connection)
- Has a /health endpoint returning 200/503
- Should be killed and restarted after 3 consecutive health failures
- Should not receive traffic until healthy

Provide:
- startupProbe configuration (allows slow startup)
- livenessProbe configuration (kills and restarts unhealthy pod)
- readinessProbe configuration (removes from Service endpoints)

Explain the difference between all three probe types.
```

---

## PodDisruptionBudget

```
Explain PodDisruptionBudgets in Kubernetes and configure one for KubeSight.

Requirements:
- Dev: minAvailable: 1
- Production: minAvailable: 2

Explain:
- What disruptions does PDB protect against?
- What is the difference between minAvailable and maxUnavailable?
- Why should you NOT set both simultaneously?
- How does PDB interact with HPA and rolling updates?
```
