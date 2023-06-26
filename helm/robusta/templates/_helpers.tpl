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

light_actions:
{{ toYaml  .Values.lightActions | indent 2 }}

{{- /* 
legacy playbooks errors 
active_playbooks:
*/ -}}
{{- if .Values.playbooks }}
  {{- fail "The `playbooks` value is deprecated. Rename `playbooks`  to `customPlaybooks` and remove builtin playbooks which are now defined separately" -}}
{{- end }}

{{- if .Values.priorityBuiltinPlaybooks }}
  {{- fail "The `priorityBuiltinPlaybooks` value is deprecated. Use `playbooksMap` dictionary to create named playbooks `playbook_name: {...playbook_definition...} `  " -}}
{{- end }}

{{- if .Values.customPlaybooks }}
  {{- fail "The `customPlaybooks` value is deprecated. Use `playbooksMap` dictionary to create named playbooks `playbook_name: {...playbook_definition...} `  " -}}

{{- end }}

{{- if .Values.builtinPlaybooks }}
  {{- fail "The `builtinPlaybooks` value is deprecated. Use `playbooksMap` dictionary to create named playbooks `playbook_name: {...playbook_definition...} `  " -}}
{{- end }}

{{- if .Values.platformPlaybooks }}
  {{- fail "The `platformPlaybooks` value is deprecated. Use `platformPlaybooksMap` dictionary to create named playbooks `playbook_name: {...playbook_definition...} `  " -}}
{{- end }}

{{- $mergedPlaybooks := .Values.playbooksMap }} 

{{- if .Values.enablePlatformPlaybooks }} 
  {{- $mergedPlaybooks := mergeOverwrite $mergedPlaybooks .Values.platformPlaybooksMap }} 
{{ end }}

# playbook map, built at {{ now }}
playbooks_map:
{{ toYaml $mergedPlaybooks | indent 2 }}


{{ end }}
