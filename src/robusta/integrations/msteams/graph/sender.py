import logging

from robusta.core.reporting import Finding
from robusta.integrations.msteams.graph.graph_client import MsTeamsGraphClient
from robusta.integrations.msteams.graph.graph_msg import MsTeamsGraphMsg


class MsTeamsGraphSender:
    def __init__(
        self,
        client: MsTeamsGraphClient,
        account_id: str,
        cluster_name: str,
        prefer_redirect_to_platform: bool,
        send_files: bool,
    ):
        self.client = client
        self.account_id = account_id
        self.cluster_name = cluster_name
        self.prefer_redirect_to_platform = prefer_redirect_to_platform
        self.send_files = send_files

    def send_finding(self, finding: Finding, platform_enabled: bool, team_id: str, channel_id: str):
        msg = MsTeamsGraphMsg(self.prefer_redirect_to_platform)
        msg.write_title_and_desc(platform_enabled, finding, self.cluster_name, self.account_id)
        msg.write_enrichments(finding.enrichments, self.send_files)
        message = msg.build_message()

        response = self.client.post_channel_message(team_id, channel_id, message)
        if response.status_code in (400, 413) and "hostedContents" in message:
            logging.warning(
                f"Teams rejected finding {finding.title} with images ({response.status_code} "
                f"{self.client.error_message(response)}), sending it without them"
            )
            response = self.client.post_channel_message(team_id, channel_id, MsTeamsGraphMsg.without_images(message))

        if not response.ok:
            logging.error(
                f"Failed to send finding {finding.title} to Teams channel {channel_id} in team {team_id}: "
                f"{response.status_code} {self.client.error_message(response)}"
            )
