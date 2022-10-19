from .sink_base import SinkBase
from .sink_config import SinkConfigBase
from .slack.slack_sink import SlackSink
from .datadog.datadog_sink import DataDogSink
from .kafka.kafka_sink import KafkaSink
from .msteams.msteams_sink import MsTeamsSink
from .robusta.robusta_sink import RobustaSink
from .slack.slack_sink_params import SlackSinkConfigWrapper
from .datadog.datadog_sink_params import DataDogSinkConfigWrapper
from .kafka.kafka_sink_params import KafkaSinkConfigWrapper
from .msteams.msteams_sink_params import MsTeamsSinkConfigWrapper
from .robusta.robusta_sink_params import RobustaSinkConfigWrapper
from .discord.discord_sink_params import DiscordSinkConfigWrapper
from .discord.discord_sink import DiscordSink
from .opsgenie.opsgenie_sink import OpsGenieSink
from .opsgenie.opsgenie_sink_params import OpsGenieSinkConfigWrapper
from .telegram.telegram_sink import TelegramSink
from .telegram.telegram_sink_params import TelegramSinkConfigWrapper
from .webhook.webhook_sink import WebhookSink
from .webhook.webhook_sink_params import WebhookSinkConfigWrapper
from .victorops.victorops_sink import VictoropsSink
from .victorops.victorops_sink_params import VictoropsConfigWrapper
from .pagerduty.pagerduty_sink import PagerdutySink
from .pagerduty.pagerduty_sink_params import PagerdutyConfigWrapper
from .mattermost.mattermost_sink import MattermostSink
from .mattermost.mattermost_sink_params import MattermostSinkConfigWrapper
from .webex.webex_sink import WebexSink
from .webex.webex_sink_params import WebexSinkConfigWrapper


class SinkFactory:
    @classmethod
    def create_sink(cls, sink_config: SinkConfigBase, registry) -> SinkBase:
        if isinstance(sink_config, SlackSinkConfigWrapper):
            return SlackSink(sink_config, registry)
        elif isinstance(sink_config, RobustaSinkConfigWrapper):
            return RobustaSink(sink_config, registry)
        elif isinstance(sink_config, MsTeamsSinkConfigWrapper):
            return MsTeamsSink(sink_config, registry)
        elif isinstance(sink_config, KafkaSinkConfigWrapper):
            return KafkaSink(sink_config, registry)
        elif isinstance(sink_config, DataDogSinkConfigWrapper):
            return DataDogSink(sink_config, registry)
        elif isinstance(sink_config, OpsGenieSinkConfigWrapper):
            return OpsGenieSink(sink_config, registry)
        elif isinstance(sink_config, TelegramSinkConfigWrapper):
            return TelegramSink(sink_config, registry)
        elif isinstance(sink_config, WebhookSinkConfigWrapper):
            return WebhookSink(sink_config, registry)
        elif isinstance(sink_config, VictoropsConfigWrapper):
            return VictoropsSink(sink_config, registry)
        elif isinstance(sink_config, PagerdutyConfigWrapper):
            return PagerdutySink(sink_config, registry)
        elif isinstance(sink_config, DiscordSinkConfigWrapper):
            return DiscordSink(sink_config, registry)
        elif isinstance(sink_config, MattermostSinkConfigWrapper):
            return MattermostSink(sink_config, registry)
        elif isinstance(sink_config, WebexSinkConfigWrapper):
            return WebexSink(sink_config, registry)
        else:
            raise Exception(f"Sink not supported {type(sink_config)}")
