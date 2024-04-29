import time
from typing import Tuple, Dict, List

from robusta.core.model.env_vars import ROBUSTA_UI_DOMAIN
from robusta.core.reporting.base import Finding, FindingStatus
from robusta.core.sinks.sink_base import SinkBase
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
        # There is a lock over the whole of the method to account:
        # 1) to prevent concurrent modifications to group accounting data structures
        # 2) to make sure two threads with identical group_key don't create
        #    two identical messages (of which one would eventually be orphaned and
        #    the other one used as a thread header).
        # TODO: this could probably be refined to a more granular locking strategy.
        with self.finding_group_lock:
            investigate_uri = self.get_timeline_uri(self.account_id, self.cluster_name)
            timestamp = time.time()
            finding_data = finding.attribute_map
            # The top level entity name (the owner of the pod etc)
            finding_data["workload"] = finding.service.name if finding.service else None
            finding_data["cluster"] = self.cluster_name
            status: FindingStatus = (
                FindingStatus.RESOLVED if finding.title.startswith("[RESOLVED]") else FindingStatus.FIRING
            )

            # 1. Notification accounting
            group_key, group_key_header = self.get_group_key_and_header(
                finding_data, self.params.grouping.group_by
            )
            if (
                group_key in self.finding_group_start_ts
                and timestamp - self.finding_group_start_ts[group_key] > self.params.grouping.interval
            ):
                self.reset_group_data(group_key)
            if group_key not in self.finding_group_start_ts:
                # Create a new group/thread
                self.finding_group_start_ts[group_key] = timestamp
                slack_thread_ts = None
            else:
                slack_thread_ts = self.finding_group_heads.get(group_key)
                self.finding_group_n_received[group_key] += 1
            if (
                not self.grouping_summary_mode
                and self.finding_group_n_received[group_key]
                < self.params.grouping.notification_mode.regular.ignore_first
            ):
                return

            if self.grouping_summary_mode:
                summary_key, summary_key_header = self.get_group_key_and_header(
                    finding_data, self.params.grouping.notification_mode.summary.by
                )

            # 2. Notification sending
            if self.grouping_summary_mode:
                idx = 0 if status == FindingStatus.FIRING else 1
                self.summary_table[group_key][summary_key][idx] += 1
                # Update the summary message
                slack_thread_ts = self.slack_sender.send_or_update_summary_message(
                    group_key_header,
                    self.summary_header,
                    self.summary_table[group_key],
                    self.params,
                    platform_enabled,
                    summary_start=self.finding_group_start_ts[group_key],
                    threaded=self.params.grouping.notification_mode.summary.threaded,
                    msg_ts=slack_thread_ts,
                    investigate_uri=investigate_uri,
                    grouping_interval=self.params.grouping.interval,
                )
                self.finding_group_heads[group_key] = slack_thread_ts
            else:
                # Regular mode - just send a normal Slack message.
                self.slack_sender.send_finding_to_slack(
                    finding, self.params, platform_enabled
                )

    def get_timeline_uri(self, account_id: str, cluster_name: str) -> str:
        return f"{ROBUSTA_UI_DOMAIN}/graphs?account_id={account_id}&cluster={cluster_name}"

    def get_group_key_and_header(self, finding_data: Dict, attributes: List) -> Tuple[Tuple[str], List[str]]:
        values = ()
        descriptions = []
        for attr in attributes:
            if isinstance(attr, str):
                if attr not in finding_data:
                    continue
                values += (finding_data.get(attr),)
                descriptions.append(
                    f"{'notification' if attr=='identifier' else attr}: {self.display_value(finding_data.get(attr))}"
                )
            elif isinstance(attr, dict):
                # This is typically labels and annotations
                top_level_attr_name = list(attr.keys())[0]
                values += tuple(
                    finding_data.get(top_level_attr_name, {}).get(element_name)
                    for element_name in sorted(attr[top_level_attr_name])
                )
                subvalues = []
                for subattr_name in sorted(attr[top_level_attr_name]):
                    subvalues.append((subattr_name, finding_data.get(top_level_attr_name, {}).get(subattr_name)))
                subvalues_str = ", ".join(f"{key}={self.display_value(value)}" for key, value in sorted(subvalues))
                descriptions.append(f"{top_level_attr_name}: {subvalues_str}")
        return values, descriptions

    def display_value(self, value):
        if value is None:
            return '(undefined)'
        else:
            return value
