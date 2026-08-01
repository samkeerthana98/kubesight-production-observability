# Debugging Prompts

Prompts used to debug issues encountered during KubeSight development.

---

## Prometheus Not Discovering ServiceMonitors

```
Prometheus is not discovering my ServiceMonitor targets.

Setup:
- kube-prometheus-stack installed in the "monitoring" namespace
- ServiceMonitors deployed in the "kubesight" namespace
- Prometheus UI shows no targets for kubesight

Possible causes to investigate:
1. Missing or incorrect label on ServiceMonitor
2. Prometheus serviceMonitorSelector not matching
3. Namespace selector configuration
4. RBAC preventing cross-namespace scraping

Provide step-by-step debugging commands and the fix.
```

---

## Grafana Dashboard Not Auto-Provisioning

```
The KubeSight Grafana dashboard ConfigMap was created but the dashboard
does not appear in Grafana.

ConfigMap is in the monitoring namespace.
ConfigMap has label grafana_dashboard: "1".
kube-prometheus-stack sidecar is enabled.

Debug steps:
1. How to check if the sidecar container is running
2. How to view sidecar container logs
3. What to look for in the logs
4. How to verify the dashboard JSON is valid
5. Common causes for sidecar not detecting the ConfigMap
```

---

## HPA Shows Unknown Metrics

```
The KubeSight HPA shows <unknown>/80% for CPU metrics.

kubectl describe hpa kubesight -n kubesight shows:
"unable to fetch metrics from resource metrics API"

Debug:
1. What is missing in the cluster?
2. How to install Metrics Server on Kind?
3. Why does Kind require a special flag for Metrics Server?
4. How to verify Metrics Server is working?
5. How to verify HPA can now read CPU metrics?
```

---

## Pod CrashLoopBackOff – Redis Connection

```
The kubesight-api pod is in CrashLoopBackOff.
Logs show: "Failed to connect to Redis at redis:6379"

The Redis pod is Running.
The Redis service exists.

Debug:
1. How to verify the Redis service name and port
2. How to verify the REDIS_HOST env var in the API pod
3. How to test Redis connectivity from inside the API pod
4. Why would the API pod start before Redis is ready?
5. How to add a proper dependency wait (initContainer or probe)
```

---

## Helm Template Rendering Errors

```
helm lint ./kubesight-chart produces:

Error: template: kubesight/templates/servicemonitor.yaml:1:10: executing
"kubesight/templates/servicemonitor.yaml" at <.Values.monitoring.serviceMonitor.enabled>:
can't evaluate field monitoring in type interface {}

Possible causes:
1. Missing or malformed values.yaml key
2. Wrong indentation in values.yaml
3. Accessing a nested key that doesn't exist

Provide the correct values.yaml structure for:
monitoring:
  serviceMonitor:
    enabled: true
    interval: 30s
    scrapeTimeout: 10s
  prometheusRule:
    enabled: false
```

---

## checksum Annotation Not Triggering Pod Restart

```
I added checksum annotations to the api-deployment.yaml to trigger pod restarts
when ConfigMap or Secret changes. But pods are not restarting on helm upgrade.

Template:
annotations:
  checksum/config: {{ include "kubesight.includeConfigMap" . }}
  checksum/secret: {{ include "kubesight.includeSecret" . }}

The include templates use .Files.Get to read the files and compute sha256sum.

Debug:
1. What is the correct way to compute sha256sum of a ConfigMap template output?
2. Why does .Files.Get not work for templates/ directory?
3. What is the correct approach for computing checksums of rendered templates?
4. How to verify the annotation value changes between helm upgrades?
```

---

## NetworkPolicy Blocking Internal Traffic

```
After enabling NetworkPolicy in production, the Frontend pod cannot reach the API.
Error in frontend logs: "Error calling API: ConnectionRefusedError"

The NetworkPolicy is configured to restrict pod-to-pod traffic.

Debug:
1. How to inspect the current NetworkPolicy rules
2. What ingress/egress rules are needed for Frontend → API communication
3. What labels must pods have to match NetworkPolicy selectors
4. How to test connectivity between pods while debugging
5. How to temporarily disable NetworkPolicy for debugging
```
