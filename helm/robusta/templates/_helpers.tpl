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
  - sink_name: slack_sink
    sink_type: slack
    params:
      api_key: {{ .Values.slackApiKey }}
      slack_channel: {{ required "A valid .Values.slackChannel entry is required!" .Values.slackChannel }}
  {{- end }}
  {{- if .Values.robustaApiKey }}
  - sink_name: robusta_ui_sink
    sink_type: robusta
    params:
      token: {{ .Values.robustaApiKey }}
  {{- end }}
{{- end }}
global_config:
{{- if or .Values.slackApiKey .Values.robustaApiKey }}
  sinks:
  {{- if .Values.slackApiKey }}
  - slack_sink
  {{- end }}
  {{- if .Values.robustaApiKey }}
  - robusta_ui_sink
  {{- end }}
{{- end }}
  cluster_name: {{ required "A valid .Values.clusterName entry is required!" .Values.clusterName }}
  {{- if .Values.clusterZone }}
  cluster_zone: {{ .Values.clusterZone }}
  {{- end }}
  {{- if .Values.grafanaUrl }}
  grafana_url: {{ .Values.grafanaUrl }}
  {{- end }}
  {{- if .Values.grafanaApiKey }}
  grafana_api_key: {{ .Values.grafanaApiKey }}
  {{- end }}
  {{- if .Values.grafanaDashboardUid }}
  grafana_dashboard_uid: {{ .Values.grafanaDashboardUid }}
  {{- end }}
  {{- if .Values.prometheusUrl }}
  prometheus_url: {{ .Values.prometheusUrl }}
  {{- end }}
active_playbooks:
{{ toYaml .Values.playbooks | indent 2 }}
{{ end }}
