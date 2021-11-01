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
  {{- if .Values.global_config }}
  {{- range $k, $v := .Values.global_config }}
  {{- if $v }}
  {{ $k }}: {{ $v }}
  {{- end }}
  {{- end }}
  {{- end }}
active_playbooks:
{{ toYaml .Values.playbooks | indent 2 }}
{{ end }}
