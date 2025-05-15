from robusta.core.sinks.slack.preview.slack_sink_preview_params import SlackSinkPreviewConfigWrapper, SlackSinkPreviewParams
from robusta.core.sinks.slack.slack_sink import SlackSink
from robusta.integrations import slack as slack_module


class SlackSinkPreview(SlackSink):
    params: SlackSinkPreviewParams

    def __init__(self, sink_config: SlackSinkPreviewConfigWrapper, registry):
        self.slack_sender = slack_module.SlackSender(
            self.api_key, self.account_id, self.cluster_name, self.signing_key, self.slack_channel, is_preview=True
        )
        super().__init__(sink_config.slack_sink, registry, self.slack_sender)

