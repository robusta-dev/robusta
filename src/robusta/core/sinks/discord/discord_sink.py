import logging
from typing import Dict, Any

from robusta.core.reporting.base import Finding
from robusta.core.reporting.blocks import ButtonEvent
from robusta.core.sinks.discord.discord_sink_params import DiscordSinkConfigWrapper
from robusta.core.sinks.sink_base import SinkBase
from robusta.integrations.discord.sender import DiscordSender


class DiscordSink(SinkBase):
    def __init__(self, sink_config: DiscordSinkConfigWrapper, registry):
        super().__init__(sink_config.discord_sink, registry)

        self.url = sink_config.discord_sink.url
        self.bot_token = sink_config.discord_sink.bot_token
        self.application_id = sink_config.discord_sink.application_id
        self.sender = DiscordSender(
            self.url,
            self.account_id,
            self.cluster_name,
            self.params,
            bot_token=self.bot_token,
            application_id=self.application_id
        )

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.sender.send_finding_to_discord(finding, platform_enabled)

    def handle_button_event(self, event: ButtonEvent) -> bool:
        """Handle interactive button events from Discord."""
        try:
            return self.sender.handle_interaction(event)
        except Exception as e:
            logging.error(f"Failed to handle Discord button event: {e}", exc_info=True)
            return False

    def register_interaction_handler(self, interaction_id: str, handler: Any):
        """Register a handler for Discord interactions."""
        if hasattr(self.sender, 'register_interaction_handler'):
            self.sender.register_interaction_handler(interaction_id, handler)
