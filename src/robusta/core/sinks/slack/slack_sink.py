from robusta.core.model.env_vars import ROBUSTA_UI_DOMAIN
from robusta.core.reporting.base import Finding, FindingStatus
from robusta.core.sinks.sink_base import NotificationGroup, NotificationSummary, SinkBase
from robusta.core.sinks.slack.slack_sink_params import SlackSinkConfigWrapper, SlackSinkParams
from robusta.integrations import slack as slack_module


class SlackSink(SinkBase):
    params: SlackSinkParams

    def __init__(self, sink_config: SlackSinkConfigWrapper, registry):
        super().__init__(sink_config.slack_sink, registry)
        self.slack_channel = sink_config.slack_sink.slack_channel
        self.api_key = sink_config.slack_sink.api_key
        self.slack_sender = slack_module.SlackSender(
            self.api_key, self.account_id, self.cluster_name, self.signing_key, self.slack_channel
        )

    def write_finding(self, finding: Finding, platform_enabled: bool) -> None:
        if self.grouping_enabled:
            self.handle_notification_grouping(finding, platform_enabled)
        else:
            self.slack_sender.send_finding_to_slack(finding, self.params, platform_enabled)

    def handle_notification_grouping(self, finding: Finding, platform_enabled: bool) -> None:
        # There is a lock over the whole of the method:
        # 1) to prevent concurrent modifications to group accounting data structures
        # 2) to make sure two threads with identical group_key don't create
        #    two identical messages (of which one would eventually be orphaned and
        #    the other one used as a thread header).
        # TODO: this could probably be refined to a more granular locking strategy.
        with self.finding_group_lock:
            investigate_uri = self.get_timeline_uri(self.account_id, self.cluster_name)
            finding_data = finding.attribute_map
            # The top level entity name (the owner of the pod etc)
            finding_data["workload"] = finding.service.name if finding.service else None
            finding_data["cluster"] = self.cluster_name
            resolved = finding.title.startswith("[RESOLVED]")

            # 1. Notification accounting
            group_key, group_header = self.get_group_key_and_header(
                finding_data, self.params.grouping.group_by
            )

            if self.grouping_summary_mode:
                summary_key, _ = self.get_group_key_and_header(
                    finding_data, self.params.grouping.notification_mode.summary.by
                )
                notification_summary = self.summaries[group_key]
                notification_summary.register_notification(
                    summary_key, resolved, self.params.grouping.interval
                )
                slack_thread_ts = self.slack_sender.send_or_update_summary_message(
                    group_header,
                    self.summary_header,
                    notification_summary.summary_table,
                    self.params,
                    platform_enabled,
                    summary_start=notification_summary.start_ts,
                    threaded=self.params.grouping.notification_mode.summary.threaded,
                    msg_ts=notification_summary.message_id,
                    investigate_uri=investigate_uri,
                    grouping_interval=self.params.grouping.interval,
                )
                notification_summary.message_id = slack_thread_ts
                should_send_notification = self.params.grouping.notification_mode.summary.threaded
            else:
                should_send_notification = self.groups[group_key].register_notification(
                    self.params.grouping.interval,
                    self.params.grouping.notification_mode.regular.ignore_first
                )
                slack_thread_ts = None
            if should_send_notification:
                self.slack_sender.send_finding_to_slack(
                    finding, self.params, platform_enabled, thread_ts=slack_thread_ts
                )


    def get_timeline_uri(self, account_id: str, cluster_name: str) -> str:
        return f"{ROBUSTA_UI_DOMAIN}/graphs?account_id={account_id}&cluster={cluster_name}"
