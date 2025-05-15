from robusta.core.sinks.slack.preview.slack_sink_preview_params import SlackSinkPreviewConfigWrapper, SlackSinkPreviewParams
from robusta.core.sinks.slack.slack_sink import SlackSink


class SlackSinkPreview(SlackSink):
    params: SlackSinkPreviewParams

    def __init__(self, sink_config: SlackSinkPreviewConfigWrapper, registry):
        super().__init__(sink_config, registry, is_preview=True)

