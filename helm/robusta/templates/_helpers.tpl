{{ define "robusta.configfile" -}}
playbook_repos:
{{ toYaml .Values.playbookRepos | indent 2 }}

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
active_playbooks:
{{- if .Values.playbooks }}
  {{- fail "The `playbooks` value is deprecated. Rename `playbooks`  to `customPlaybooks` and remove builtin playbooks which are now defined separately" -}}
{{- end }}

{{- if .Values.priorityBuiltinPlaybooks }}
{{ toYaml .Values.priorityBuiltinPlaybooks | indent 2 }}
{{- end }}

{{- if .Values.customPlaybooks }}
{{ toYaml .Values.customPlaybooks | indent 2 }}
{{- end }}

{{- if .Values.builtinPlaybooks }}
{{ toYaml .Values.builtinPlaybooks | indent 2 }}
{{- end }}

{{- if and .Values.enablePlatformPlaybooks .Values.platformPlaybooks }}
{{ toYaml .Values.platformPlaybooks | indent 2 }}
{{- end }}
{{ end }}
