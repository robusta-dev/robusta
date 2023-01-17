from typing import Dict, Type

from robusta.core.sinks.datadog import DataDogSink, DataDogSinkConfigWrapper
from robusta.core.sinks.discord import DiscordSink, DiscordSinkConfigWrapper
from robusta.core.sinks.jira import JiraSink, JiraSinkConfigWrapper
from robusta.core.sinks.kafka import KafkaSink, KafkaSinkConfigWrapper
from robusta.core.sinks.mattermost import MattermostSink, MattermostSinkConfigWrapper
from robusta.core.sinks.msteams import MsTeamsSink, MsTeamsSinkConfigWrapper
from robusta.core.sinks.opsgenie import OpsGenieSink, OpsGenieSinkConfigWrapper
from robusta.core.sinks.pagerduty import PagerdutyConfigWrapper, PagerdutySink
from robusta.core.sinks.robusta import RobustaSink, RobustaSinkConfigWrapper
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.sink_config import SinkConfigBase
from robusta.core.sinks.slack import SlackSink, SlackSinkConfigWrapper
from robusta.core.sinks.telegram import TelegramSink, TelegramSinkConfigWrapper
from robusta.core.sinks.victorops import VictoropsConfigWrapper, VictoropsSink
from robusta.core.sinks.webex import WebexSink, WebexSinkConfigWrapper
from robusta.core.sinks.webhook import WebhookSink, WebhookSinkConfigWrapper


class SinkFactory:
    __sink_config_mapping: Dict[Type[SinkConfigBase], Type[SinkBase]] = {
        SlackSinkConfigWrapper: SlackSink,
        RobustaSinkConfigWrapper: RobustaSink,
        MsTeamsSinkConfigWrapper: MsTeamsSink,
        KafkaSinkConfigWrapper: KafkaSink,
        DataDogSinkConfigWrapper: DataDogSink,
        DiscordSinkConfigWrapper: DiscordSink,
        OpsGenieSinkConfigWrapper: OpsGenieSink,
        TelegramSinkConfigWrapper: TelegramSink,
        WebhookSinkConfigWrapper: WebhookSink,
        VictoropsConfigWrapper: VictoropsSink,
        PagerdutyConfigWrapper: PagerdutySink,
        MattermostSinkConfigWrapper: MattermostSink,
        WebexSinkConfigWrapper: WebexSink,
        JiraSinkConfigWrapper: JiraSink,
    }

    @classmethod
    def create_sink(cls, sink_config: SinkConfigBase, registry) -> SinkBase:
        SinkClass = cls.__sink_config_mapping.get(type(sink_config))
        if SinkClass is None:
            raise Exception(f"Sink not supported {type(sink_config)}")
        return SinkClass(sink_config, registry)
