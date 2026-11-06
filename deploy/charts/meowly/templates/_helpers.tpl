{{/*
Chart name, truncated to the 63-char label limit.
*/}}
{{- define "meowly.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Release-scoped base name. When the release name already contains the chart name it is used
as is, so `helm install meowly ...` yields `meowly-api`, `meowly-controller` and friends.
*/}}
{{- define "meowly.fullname" -}}
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

{{- define "meowly.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Name of one component: (dict "root" $ "component" "api") -> meowly-api.
*/}}
{{- define "meowly.componentName" -}}
{{- printf "%s-%s" (include "meowly.fullname" .root) .component | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Immutable selector labels of a component. Takes (dict "root" $ "component" "...").
*/}}
{{- define "meowly.selectorLabels" -}}
app.kubernetes.io/name: {{ include "meowly.name" .root }}
app.kubernetes.io/instance: {{ .root.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{/*
Labels shared by every resource of a component. Takes (dict "root" $ "component" "...").
*/}}
{{- define "meowly.componentLabels" -}}
helm.sh/chart: {{ include "meowly.chart" .root }}
{{ include "meowly.selectorLabels" . }}
app.kubernetes.io/part-of: meowly
{{- with .root.Chart.AppVersion }}
app.kubernetes.io/version: {{ . | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .root.Release.Service }}
{{- end }}

{{/*
Chart-wide labels (for resources that belong to no component, e.g. the CRD).
*/}}
{{- define "meowly.labels" -}}
helm.sh/chart: {{ include "meowly.chart" . }}
app.kubernetes.io/name: {{ include "meowly.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/part-of: meowly
{{- with .Chart.AppVersion }}
app.kubernetes.io/version: {{ . | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Image reference: (dict "root" $ "image" .Values.api.image). Empty tag falls back to appVersion.
*/}}
{{- define "meowly.image" -}}
{{- printf "%s:%s" .image.repository (default .root.Chart.AppVersion .image.tag) }}
{{- end }}

{{/*
ServiceAccount names.
*/}}
{{- define "meowly.workerServiceAccountName" -}}
{{- default (include "meowly.componentName" (dict "root" . "component" "worker")) .Values.worker.serviceAccount.name }}
{{- end }}

{{/*
Name of the Secret holding the database URL (api) .
*/}}
{{- define "meowly.databaseSecretName" -}}
{{- default (include "meowly.componentName" (dict "root" . "component" "api")) .Values.api.database.existingSecret }}
{{- end }}

{{- define "meowly.databaseSecretKey" -}}
{{- if .Values.api.database.existingSecret }}{{ .Values.api.database.existingSecretKey }}{{ else }}database-url{{ end }}
{{- end }}

{{/*
Seconds a pod may take to stop: preStop sleep + graceful shutdown + 5s of slack.
*/}}
{{- define "meowly.terminationGracePeriodSeconds" -}}
{{- add (int .Values.api.preStop.sleepSeconds) (int .Values.api.shutdown.timeoutSeconds) 5 }}
{{- end }}
