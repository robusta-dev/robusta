# Slack Message Templates

This directory contains the Jinja2 templates used to render Slack messages.

## How Templates Work

Slack messages are rendered using [Jinja2](https://jinja.palletsprojects.com/) templates. Each template produces one or more Slack Block Kit blocks in JSON format.

Templates are separated by double newlines (`\n\n`) to indicate separate blocks. Each block must be valid JSON that conforms to the [Slack Block Kit](https://api.slack.com/block-kit) format.

## Available Templates

- `header.j2`: The header section of alert notifications, including title and metadata

## Customizing Templates

Users can customize templates in the Robusta configuration by providing their own template content:

```yaml
sinks:
  slack:
    slack_sink:
      name: slack
      slack_channel: "#alerts"
      api_key: "${SLACK_TOKEN}"
      custom_templates:
        header.j2: |
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "{{ status_emoji }} *CUSTOM ALERT: {{ title }}*"
            }
          }

          {
            "type": "context",
            "elements": [
              {
                "type": "mrkdwn", 
                "text": ":bell: {{ alert_type }} on cluster {{ cluster_name }}"
              },
              {
                "type": "mrkdwn",
                "text": "{{ severity_emoji }} {{ severity }}"
              }
            ]
          }
```

## Template Variables

Each template has access to different variables. Here are the variables available in the `header.j2` template:

| Variable | Description |
|----------|-------------|
| `title` | The alert title |
| `status_text` | "Firing" or "Resolved" |
| `status_emoji` | "⚠️" (for firing) or "✅" (for resolved) |
| `severity` | Alert severity (e.g., "Warning", "Critical") |
| `severity_emoji` | Emoji for the severity level |
| `alert_type` | "Alert", "K8s Event", or "Notification" |
| `cluster_name` | The name of the cluster |
| `platform_enabled` | Boolean indicating if Robusta platform is enabled |
| `include_investigate_link` | Boolean indicating if investigate link should be included |
| `investigate_uri` | URI for investigation |
| `resource_text` | Resource identifier (e.g., "Pod/namespace/name") |
| `resource_emoji` | Emoji for the resource type |
| `finding` | The complete finding object as JSON |

## Fallback Behavior

If Jinja2 is not available, a built-in fallback implementation will be used that produces the same output as the default template.