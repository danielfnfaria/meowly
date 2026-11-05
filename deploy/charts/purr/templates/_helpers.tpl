{{/*
Chart name, truncated to the 63-char label limit.
*/}}
{{- define "purr.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Release-scoped base name. When the release name already contains the chart name it is used
as is, so `helm install purr ...` yields `purr-api`, `purr-controller` and friends.
*/}}
{{- define "purr.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "purr.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Name of one component: (dict "root" $ "component" "api") -> purr-api.
*/}}
{{- define "purr.componentName" -}}
{{- printf "%s-%s" (include "purr.fullname" .root) .component | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Immutable selector labels of a component. Takes (dict "root" $ "component" "...").
*/}}
{{- define "purr.selectorLabels" -}}
app.kubernetes.io/name: {{ include "purr.name" .root }}
app.kubernetes.io/instance: {{ .root.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{/*
Labels shared by every resource of a component. Takes (dict "root" $ "component" "...").
*/}}
{{- define "purr.componentLabels" -}}
helm.sh/chart: {{ include "purr.chart" .root }}
{{ include "purr.selectorLabels" . }}
app.kubernetes.io/part-of: purr
{{- with .root.Chart.AppVersion }}
app.kubernetes.io/version: {{ . | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .root.Release.Service }}
{{- end }}

{{/*
Chart-wide labels (for resources that belong to no component, e.g. the CRD).
*/}}
{{- define "purr.labels" -}}
helm.sh/chart: {{ include "purr.chart" . }}
app.kubernetes.io/name: {{ include "purr.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/part-of: purr
{{- with .Chart.AppVersion }}
app.kubernetes.io/version: {{ . | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Image reference: (dict "root" $ "image" .Values.api.image). Empty tag falls back to appVersion.
*/}}
{{- define "purr.image" -}}
{{- printf "%s:%s" .image.repository (default .root.Chart.AppVersion .image.tag) }}
{{- end }}

{{/*
ServiceAccount names.
*/}}
{{- define "purr.workerServiceAccountName" -}}
{{- default (include "purr.componentName" (dict "root" . "component" "worker")) .Values.worker.serviceAccount.name }}
{{- end }}

{{/*
Name of the Secret holding the database URL (api) .
*/}}
{{- define "purr.databaseSecretName" -}}
{{- default (include "purr.componentName" (dict "root" . "component" "api")) .Values.api.database.existingSecret }}
{{- end }}

{{- define "purr.databaseSecretKey" -}}
{{- if .Values.api.database.existingSecret }}{{ .Values.api.database.existingSecretKey }}{{ else }}database-url{{ end }}
{{- end }}

{{/*
Seconds a pod may take to stop: preStop sleep + graceful shutdown + 5s of slack.
*/}}
{{- define "purr.terminationGracePeriodSeconds" -}}
{{- add (int .Values.api.preStop.sleepSeconds) (int .Values.api.shutdown.timeoutSeconds) 5 }}
{{- end }}
