{{/*
Expand the name of the chart.
*/}}
{{- define "robusta.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "robusta.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{ define "robusta.configfile" -}}
playbook_repos:
{{ toYaml .Values.playbookRepos | indent 2 }}

{{- if and (eq (len .Values.sinksConfig) 0) (and (not .Values.slackApiKey) (not .Values.robustaApiKey)) }}
{{- fail "At least one sink must be defined!" }}
{{- end }}

{{- range .Values.sinksConfig }}
  {{- if .robusta_sink }}
    {{- if $.Values.disableCloudRouting }}
      {{- fail "You cannot set `disableCloudRouting: true` when the Robusta UI sink (robusta_sink) is enabled, as this flag breaks the UI's behavior.\nPlease remove `disableCloudRouting: true` to continue installing." -}}
    {{- end }}
  {{- end }}
{{- end }}

{{- if or .Values.slackApiKey .Values.robustaApiKey }}
{{- /* support old values files, prior to chart version 0.8.9 */}}
sinks_config:
{{- if .Values.slackApiKey }}
- slack_sink:
    name: slack sink
    api_key: {{ .Values.slackApiKey }}
    slack_channel: {{ required "A valid .Values.slackChannel entry is required!" .Values.slackChannel }}
{{- end }}
{{- if .Values.robustaApiKey }}
- robusta_sink:
    name: robusta_ui_sink
    token: {{ .Values.robustaApiKey }}
{{- end }}

{{ else }}
sinks_config:
{{ toYaml .Values.sinksConfig }}
{{- end }}

global_config:
  cluster_name: {{ required "A valid .Values.clusterName entry is required!" .Values.clusterName }}
  {{- if .Values.clusterZone }}
  cluster_zone: {{ .Values.clusterZone }}
  {{- end }}
  {{- if .Values.globalConfig }}
{{ toYaml .Values.globalConfig | indent 2 }}
  {{- end }}

alert_relabel:
{{ toYaml  .Values.alertRelabel | indent 2 }}

light_actions:
{{ toYaml  .Values.lightActions | indent 2 }}

active_playbooks:
{{- if .Values.playbooks }}
  {{- fail "The `playbooks` value is deprecated. Rename `playbooks`  to `customPlaybooks` and remove builtin playbooks which are now defined separately" -}}
{{- end }}

{{- $disabledPlaybooks := .Values.disabledPlaybooks }}

{{- $priorityPlaybooks := .Values.priorityBuiltinPlaybooks }}
{{- $enabledPriorityPlaybooks := list }}
{{- range $myplaybook := $priorityPlaybooks }}
{{- if or ( not (hasKey $myplaybook "name") ) (not (has $myplaybook.name $disabledPlaybooks)) }}
{{- $enabledPriorityPlaybooks = append $enabledPriorityPlaybooks $myplaybook }}
{{- end }}
{{- end }}

{{- if $enabledPriorityPlaybooks }}
{{ toYaml $enabledPriorityPlaybooks | indent 2 }}
{{- end }}

{{- if .Values.customPlaybooks }}
{{ toYaml .Values.customPlaybooks | indent 2 }}
{{- if .Values.namedCustomPlaybooks }}
{{- range $i, $val := .Values.namedCustomPlaybooks }}
  {{ toYaml $val | nindent 2 }}
{{ end -}}
{{- end }}
{{- end }}

{{- $builtinPlaybooks := .Values.builtinPlaybooks }}
{{- $enabledBuiltinPlaybooks := list }}
{{- range $myplaybook := $builtinPlaybooks }}
{{- if or ( not (hasKey $myplaybook "name") ) (not (has $myplaybook.name $disabledPlaybooks)) }}
{{- $enabledBuiltinPlaybooks = append $enabledBuiltinPlaybooks $myplaybook }}
{{- end }}
{{- end }}

{{- if $enabledBuiltinPlaybooks }}
{{ toYaml $enabledBuiltinPlaybooks | indent 2 }}
{{- end }}

{{- if and .Values.enablePlatformPlaybooks .Values.platformPlaybooks }}

{{- $platformPlaybooks := .Values.platformPlaybooks }}
{{- $enabledPlatformPlaybooks := list }}
{{- range $myplaybook := $platformPlaybooks }}
{{- if or ( not (hasKey $myplaybook "name") ) (not (has $myplaybook.name $disabledPlaybooks)) }}
{{- $enabledPlatformPlaybooks = append $enabledPlatformPlaybooks $myplaybook }}
{{- end }}
{{- end }}

{{- if $enabledPlatformPlaybooks }}
{{ toYaml $enabledPlatformPlaybooks | indent 2 }}
{{- end }}

{{- end }}
{{ end }}
