# Troubleshooting Guide

## Quick Diagnostics

```bash
# Check all pods in kubesight namespace
kubectl get pods -n kubesight

# Check all pods in monitoring namespace
kubectl get pods -n monitoring

# Describe a failing pod
kubectl describe pod <pod-name> -n kubesight

# View pod logs
kubectl logs <pod-name> -n kubesight

# View previous pod logs (after crash)
kubectl logs <pod-name> -n kubesight --previous

# Check events
kubectl get events -n kubesight --sort-by='.lastTimestamp'
```

---

## Common Issues

### Pods Stuck in `Pending` State

**Symptoms**: Pods show `Pending` status and never start.

**Diagnosis**:
```bash
kubectl describe pod <pod-name> -n kubesight
# Look for "Events" section at the bottom
```

**Common causes**:
- Insufficient CPU or memory on the node
- PVC not bound (check storage class)
- Node selector / toleration mismatch

**Fix for PVC issue**:
```bash
kubectl get pvc -n kubesight
kubectl describe pvc kubesight-redis -n kubesight
```

If using Kind without a default storage class:
```bash
kubectl get storageclass
```

---

### Pods in `CrashLoopBackOff`

**Symptoms**: Pod starts, crashes, and keeps restarting.

**Diagnosis**:
```bash
kubectl logs <pod-name> -n kubesight --previous
```

**Common causes**:
- Redis not ready when API starts (transient — usually self-heals)
- Wrong Redis hostname in environment variables
- Missing secrets

**Check environment variables**:
```bash
kubectl exec -it <api-pod> -n kubesight -- env | grep REDIS
```

**Expected values**:
```
REDIS_HOST=kubesight-redis
REDIS_PORT=6379
```

---

### Prometheus Not Scraping KubeSight Metrics

**Symptoms**: Targets missing in Prometheus → Status → Targets.

**Diagnosis**:
```bash
kubectl get servicemonitors -n kubesight
kubectl describe servicemonitor kubesight-api -n kubesight
```

**Most common cause**: Missing `release: kube-prometheus-stack` label on the ServiceMonitor.

Verify the label exists:
```bash
kubectl get servicemonitor kubesight-api -n kubesight -o yaml | grep release
```

Expected:
```yaml
labels:
  release: kube-prometheus-stack
```

**Also check**: Prometheus `serviceMonitorSelector` setting:
```bash
kubectl get prometheus -n monitoring -o yaml | grep -A5 serviceMonitorSelector
```

---

### Grafana Dashboard Not Loading

**Symptoms**: KubeSight dashboard is not visible in Grafana.

**Diagnosis**:
```bash
# Check if the ConfigMap was created
kubectl get configmap -n monitoring | grep grafana-dashboard

# Check ConfigMap labels
kubectl get configmap kubesight-grafana-dashboard -n monitoring -o yaml | grep grafana_dashboard
```

**Required label**:
```yaml
labels:
  grafana_dashboard: "1"
```

**Check the Grafana sidecar logs**:
```bash
kubectl logs -n monitoring -l app.kubernetes.io/name=grafana -c grafana-sc-dashboard
```

**Also verify**: The ConfigMap must be in the same namespace as Grafana (`monitoring`). Check `values.yaml`:
```yaml
grafanaDashboard:
  enabled: true
  namespace: monitoring  # Must match Grafana's namespace
```

---

### HPA Not Scaling

**Symptoms**: HPA shows `<unknown>/80%` for CPU metrics.

**Diagnosis**:
```bash
kubectl get hpa -n kubesight
kubectl describe hpa kubesight -n kubesight
```

**Most common cause**: Metrics Server is not installed.

Install Metrics Server on Kind:
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch for Kind (disables TLS verification)
kubectl patch deployment metrics-server \
  -n kube-system \
  --type='json' \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
```

Verify:
```bash
kubectl top nodes
kubectl top pods -n kubesight
```

---

### Helm Lint Errors

**Symptoms**: `helm lint` fails or `helm template` produces errors.

**Diagnosis**:
```bash
helm lint ./kubesight-chart
helm template kubesight ./kubesight-chart --debug 2>&1 | head -50
```

**Common causes**:
- YAML indentation errors in templates
- Missing required values
- Invalid Kubernetes API versions

**Validate with specific values file**:
```bash
helm template kubesight ./kubesight-chart -f ./kubesight-chart/values-production.yaml
```

---

### Frontend Cannot Reach API

**Symptoms**: Frontend shows "Error calling API" message.

**Diagnosis**:
```bash
# Check frontend environment variables
kubectl exec -it <frontend-pod> -n kubesight -- env | grep API

# Test API connectivity from frontend pod
kubectl exec -it <frontend-pod> -n kubesight -- wget -qO- http://kubesight-api:5000/health
```

**Expected**: `API_SERVICE_HOST=kubesight-api`, `API_SERVICE_PORT=5000`

**If NetworkPolicy is enabled** (production), verify the policy allows frontend → api traffic:
```bash
kubectl get networkpolicy -n kubesight
kubectl describe networkpolicy kubesight-kubesight-api -n kubesight
```

---

### Redis Connection Errors in API Logs

**Symptoms**: API logs show Redis connection failures.

**Diagnosis**:
```bash
# Check Redis pod status
kubectl get pods -n kubesight -l app.kubernetes.io/component=redis

# Check Redis logs
kubectl logs -n kubesight -l app.kubernetes.io/component=redis

# Test Redis from API pod
kubectl exec -it <api-pod> -n kubesight -- python3 -c "import redis; r=redis.Redis(host='kubesight-redis', port=6379); print(r.ping())"
```

---

## Useful Commands Reference

```bash
# Port-forward all services at once (run each in separate terminal)
kubectl port-forward svc/kubesight-frontend 5001:5000 -n kubesight
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring
kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring
kubectl port-forward svc/kube-prometheus-stack-alertmanager 9093:9093 -n monitoring

# Follow logs for all pods in namespace
kubectl logs -f -l app.kubernetes.io/name=kubesight -n kubesight --all-containers

# Check resource usage
kubectl top pods -n kubesight
kubectl top nodes

# Check Helm release status
helm status kubesight -n kubesight
helm history kubesight -n kubesight

# Rollback to previous release
helm rollback kubesight -n kubesight
```
