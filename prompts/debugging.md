# Debugging Prompts

Prompts used to debug issues encountered during KubeSight development.

---

## YAML Bug: priorityClassName and dnsPolicy at Wrong Level

```
In api-deployment.yaml and redis-deployment.yaml, priorityClassName and
dnsPolicy were placed at the Deployment spec level instead of the pod spec level.

This is a silent bug — the Deployment renders without error but the fields
are ignored by Kubernetes because they are not valid at spec level.

Wrong (at Deployment spec level):
  spec:
    replicas: 1
    priorityClassName: high-priority   ← wrong level
    dnsPolicy: ClusterFirst            ← wrong level
    strategy:
      ...

Correct (inside spec.template.spec — the pod spec):
  spec:
    replicas: 1
    strategy:
      ...
    template:
      spec:
        priorityClassName: high-priority   ← correct
        dnsPolicy: ClusterFirst            ← correct
        containers:
          ...

Fix: Move both fields inside the template.spec block and wrap in Helm conditionals.
```

---

## YAML Bug: Checksum Annotation Using .Files.Get on templates/

```
The _helpers.tpl checksum helpers used .Files.Get to read ConfigMap and Secret
template files, which does not work — Helm blocks .Files.Get from accessing
the templates/ directory.

Wrong:
  {{- define "kubesight.includeConfigMap" -}}
  {{ .Files.Get (printf "%s/configmap.yaml" .Path) | sha256sum }}
  {{- end }}

.Path is also empty in this context, so this reads nothing and returns
a static hash that never changes between upgrades.

Correct approach using include + print:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
  checksum/secret: {{ include (print $.Template.BasePath "/secret.yaml") . | sha256sum }}

This renders the actual template content and hashes it, so pods restart
automatically when ConfigMap or Secret values change on helm upgrade.
```

---

## YAML Bug: Wrong TLS Key in Production Values

```
values-production.yaml used secretId in the ingress TLS block, but Kubernetes
expects secretName.

Wrong:
  tls:
    - secretId: kubesight-tls    ← not a valid Kubernetes field
      hosts:
        - kubesight.example.com

Correct:
  tls:
    - secretName: kubesight-tls   ← correct Kubernetes field
      hosts:
        - kubesight.example.com

The ingress template uses {{- toYaml .Values.ingress.tls | nindent 4 }} which
passes through the values block as-is. If secretId is used, the rendered
Ingress YAML will contain an unknown field that Kubernetes silently ignores,
meaning TLS termination never activates.
```

---

## Prometheus Not Discovering ServiceMonitors

```
Prometheus is not discovering KubeSight ServiceMonitor targets.

Setup:
- kube-prometheus-stack installed in monitoring namespace
- ServiceMonitors deployed in kubesight namespace via Helm

Debug steps:
1. Verify ServiceMonitor has the required label:
   kubectl get servicemonitor kubesight-api -n kubesight -o yaml | grep release
   Expected: release: kube-prometheus-stack

2. Check Prometheus serviceMonitorSelector:
   kubectl get prometheus -n monitoring -o yaml | grep -A5 serviceMonitorSelector

3. Verify Service labels match ServiceMonitor selector:
   kubectl get svc kubesight-api -n kubesight --show-labels

4. Check targets in Prometheus UI:
   kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring
   http://localhost:9090/targets

Root cause: the release: kube-prometheus-stack label was missing from
the ServiceMonitor metadata. Added as a hardcoded label in servicemonitor.yaml.
```

---

## Grafana Dashboard Not Auto-Provisioning

```
The Grafana dashboard ConfigMap was created but the dashboard did not appear.

Debug steps:
1. Confirm ConfigMap exists in the monitoring namespace (not kubesight):
   kubectl get configmap -n monitoring | grep grafana-dashboard

2. Confirm the label is exactly grafana_dashboard: "1":
   kubectl get configmap kubesight-grafana-dashboard -n monitoring -o yaml | grep grafana_dashboard

3. Check Grafana sidecar container logs:
   kubectl logs -n monitoring -l app.kubernetes.io/name=grafana -c grafana-sc-dashboard

4. Verify kube-prometheus-stack was installed with sidecar flags:
   --set grafana.sidecar.dashboards.enabled=true
   --set grafana.sidecar.dashboards.label=grafana_dashboard

Root cause: The ConfigMap was created in the kubesight namespace instead of
monitoring. Fixed by setting grafanaDashboard.namespace: monitoring in values.yaml
and using namespace: {{ .Values.grafanaDashboard.namespace }} in the template.
```

---

## HPA Shows Unknown Metrics

```
HPA shows <unknown>/70% for CPU on Kind cluster.

Debug:
1. kubectl describe hpa kubesight-api -n kubesight
   Shows: "unable to fetch metrics from resource metrics API"

2. Check if Metrics Server is installed:
   kubectl get deployment metrics-server -n kube-system

Fix — install Metrics Server with Kind-specific flag:
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

kubectl patch deployment metrics-server -n kube-system \
  --type='json' \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'

Kind uses self-signed kubelet certificates, so --kubelet-insecure-tls is required.

Verify:
kubectl top pods -n kubesight
kubectl get hpa -n kubesight
```

---

## NetworkPolicy Blocking Frontend → API Traffic

```
After enabling NetworkPolicy in production, the Frontend pod could not reach
the API. Frontend logs showed: "Error calling API: ConnectionRefusedError"

Debug:
1. Check NetworkPolicy rules:
   kubectl get networkpolicy -n kubesight
   kubectl describe networkpolicy kubesight-api -n kubesight

2. Verify pod labels match the NetworkPolicy podSelector:
   kubectl get pods -n kubesight --show-labels

Root cause: The NetworkPolicy for the API only allows ingress from pods
with label app.kubernetes.io/component: frontend. The frontend pod had
this label set correctly but the NetworkPolicy selector was checking
app.kubernetes.io/instance as well.

Fix: Ensure all three NetworkPolicies in networkpolicy.yaml use consistent
matchLabels that match the actual pod labels set by the deployment templates.

NetworkPolicy flow:
- frontend: ingress from anywhere (from: [])
- api: ingress only from component=frontend pods
- redis: ingress only from component=api pods
```
