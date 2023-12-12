import logging
import sys
from typing import Dict, Type

from robusta.core.sinks.datadog import DataDogSink, DataDogSinkConfigWrapper
from robusta.core.sinks.discord import DiscordSink, DiscordSinkConfigWrapper
from robusta.core.sinks.file.file_sink import FileSink
from robusta.core.sinks.file.file_sink_params import FileSinkConfigWrapper
from robusta.core.sinks.jira import JiraSink, JiraSinkConfigWrapper
from robusta.core.sinks.kafka import KafkaSink, KafkaSinkConfigWrapper
from robusta.core.sinks.mail.mail_sink import MailSink
from robusta.core.sinks.mail.mail_sink_params import MailSinkConfigWrapper
from robusta.core.sinks.mattermost import MattermostSink, MattermostSinkConfigWrapper
from robusta.core.sinks.msteams import MsTeamsSink, MsTeamsSinkConfigWrapper
from robusta.core.sinks.opsgenie import OpsGenieSink, OpsGenieSinkConfigWrapper
from robusta.core.sinks.pagerduty import PagerdutyConfigWrapper, PagerdutySink
from robusta.core.sinks.robusta import RobustaSink, RobustaSinkConfigWrapper
from robusta.core.sinks.rocketchat.rocketchat_sink import RocketchatSink
from robusta.core.sinks.rocketchat.rocketchat_sink_params import RocketchatSinkConfigWrapper
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.sink_config import SinkConfigBase
from robusta.core.sinks.slack import SlackSink, SlackSinkConfigWrapper
from robusta.core.sinks.telegram import TelegramSink, TelegramSinkConfigWrapper
from robusta.core.sinks.victorops import VictoropsConfigWrapper, VictoropsSink
from robusta.core.sinks.webex import WebexSink, WebexSinkConfigWrapper
from robusta.core.sinks.webhook import WebhookSink, WebhookSinkConfigWrapper
from robusta.core.sinks.yamessenger import YaMessengerSink, YaMessengerSinkConfigWrapper


class SinkFactory:
    __sink_config_mapping: Dict[Type[SinkConfigBase], Type[SinkBase]] = {
        SlackSinkConfigWrapper: SlackSink,
        RocketchatSinkConfigWrapper: RocketchatSink,
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
        YaMessengerSinkConfigWrapper: YaMessengerSink,
        JiraSinkConfigWrapper: JiraSink,
        FileSinkConfigWrapper: FileSink,
        MailSinkConfigWrapper: MailSink,
    }

    @classmethod
    def create_sink(cls, sink_config: SinkConfigBase, registry) -> SinkBase:
        SinkClass = cls.__sink_config_mapping.get(type(sink_config))
        if SinkClass is None:
            raise Exception(f"Sink not supported {type(sink_config)}")
        try:
            return SinkClass(sink_config, registry)
        except Exception:
            # In case a sink cannot be initialized (perhaps due to an ephemeral
            # problem like transient network error), terminate the runner process
            # as fast as possible. k8s should take care of restarting the relevant
            # pod then and hopefully make the runner functional.
            import os

            logging.exception(
                f"[{os.getpid()}] Could not initialize sink {type(sink_config)}, shutting down the runner"
            )
            sys.exit(1)
