{{/*
Expand the name of the chart.
*/}}
{{- define "graphsql.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "graphsql.fullname" -}}
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

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "graphsql.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "graphsql.labels" -}}
helm.sh/chart: {{ include "graphsql.chart" . }}
{{ include "graphsql.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "graphsql.selectorLabels" -}}
app.kubernetes.io/name: {{ include "graphsql.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "graphsql.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "graphsql.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the configmap to use
*/}}
{{- define "graphsql.configMapName" -}}
{{- if .Values.configMap.name }}
{{- .Values.configMap.name }}
{{- else }}
{{- include "graphsql.fullname" . }}-config
{{- end }}
{{- end }}

{{/*
Create the name of the secret to use
*/}}
{{- define "graphsql.secretName" -}}
{{- if .Values.secret.name }}
{{- .Values.secret.name }}
{{- else }}
{{- include "graphsql.fullname" . }}-secret
{{- end }}
{{- end }}

{{/*
Create database URL from components
*/}}
{{- define "graphsql.databaseUrl" -}}
{{- if .Values.database.host }}
{{- if eq .Values.database.type "postgres" }}
postgresql://{{ .Values.database.user }}:{{ .Values.database.password }}@{{ .Values.database.host }}:{{ .Values.database.port }}/{{ .Values.database.name }}
{{- else if eq .Values.database.type "mysql" }}
mysql+pymysql://{{ .Values.database.user }}:{{ .Values.database.password }}@{{ .Values.database.host }}:{{ .Values.database.port }}/{{ .Values.database.name }}
{{- else }}
{{ .Values.database.url }}
{{- end }}
{{- else }}
{{ .Values.database.url }}
{{- end }}
{{- end }}
