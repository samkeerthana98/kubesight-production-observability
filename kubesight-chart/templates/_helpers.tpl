{{- /*
Copyright The Helm Authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/ -}}

{{- define "kubesight.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "kubesight.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end }}
{{- end }}

{{- define "kubesight.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "kubesight.labels" -}}
helm.sh/chart: {{ include "kubesight.chart" . }}
app.kubernetes.io/name: {{ include "kubesight.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.Version }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- if .Values.podLabels }}
{{- toYaml .Values.podLabels | nindent 4 }}
{{- end }}
{{- end }}

{{- define "kubesight.selectorLabels" -}}
app.kubernetes.io/name: {{ include "kubesight.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "kubesight.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "kubesight.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{- define "kubesight.includeConfigMap" -}}
{{ .Files.Get (printf "%s/configmap.yaml" .Path) | sha256sum }}
{{- end }}

{{- define "kubesight.includeSecret" -}}
{{ .Files.Get (printf "%s/secret.yaml" .Path) | sha256sum }}
{{- end }}