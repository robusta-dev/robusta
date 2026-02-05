{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "robusta.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- .Release.Name | trunc 63 }}
{{- end }}
{{- end }}

{{ define "robusta.configfile" -}}
playbook_repos:
{{ toYaml .Values.playbookRepos | indent 2 }}

{{- if and (eq (len .Values.sinksConfig) 0) (and (not .Values.slackApiKey) (not .Values.robustaApiKey)) }}
{{- fail "At least one sink must be defined!" }}
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

{{/*
Determine if this is a Robusta SaaS environment.
Returns "true" if ROBUSTA_UI_DOMAIN is not set OR ends with ".robusta.dev"
*/}}
{{- define "robusta.isSaasEnvironment" -}}
{{- $robustaUiDomain := "" -}}
{{- range .Values.runner.additional_env_vars -}}
  {{- if eq .name "ROBUSTA_UI_DOMAIN" -}}
    {{- $robustaUiDomain = .value -}}
  {{- end -}}
{{- end -}}
{{- if or (eq $robustaUiDomain "") (hasSuffix ".robusta.dev" $robustaUiDomain) -}}
true
{{- else -}}
false
{{- end -}}
{{- end -}}

{{/*
Determine the Sentry DSN value.
Returns the user-provided value if set, otherwise returns the default SaaS DSN if in a SaaS environment, otherwise returns empty string.
*/}}
{{- define "robusta.sentryDsn" -}}
{{- if .Values.runner.sentry_dsn -}}
{{ .Values.runner.sentry_dsn }}
{{- else if eq (include "robusta.isSaasEnvironment" .) "true" -}}
https://18ac614b2d7fbbb3c7a7789b946506e1@o4510692373299200.ingest.de.sentry.io/4510707940982864
{{- else -}}
{{- end -}}
{{- end -}}
