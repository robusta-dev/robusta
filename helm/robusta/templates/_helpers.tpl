{{ define "robusta.configfile" -}}
{{- if or .Values.playbook_sets }}
playbook_sets:
{{- range $playbook_set := .Values.playbook_sets }}
- {{ $playbook_set }}
{{- end }}
{{- end }}
{{- if or .Values.slackApiKey .Values.robustaApiKey }}
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

{{- if .Values.builtinPlaybooks }}
{{ toYaml .Values.builtinPlaybooks | indent 2 }}
{{- end }}

{{- if and .Values.robustaApiKey .Values.platformPlaybooks }}
{{ toYaml .Values.platformPlaybooks | indent 2 }}
{{- end }}

{{- if .Values.customPlaybooks }}
{{ toYaml .Values.customPlaybooks | indent 2 }}
{{- end }}
{{ end }}
