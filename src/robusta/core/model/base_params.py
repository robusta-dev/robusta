from typing import List, Callable
from pydantic import SecretStr
from ...utils.documented_pydantic import DocumentedModel
from ...integrations.kubernetes.custom_models import Process, RobustaPod
from ...core.reporting.blocks import (
    BaseBlock,
    CallbackBlock,
    CallbackChoice,
    MarkdownBlock,
    TableBlock,
)


class ActionParams(DocumentedModel):
    """
    Base class for all Action parameter classes.
    """

    pass


class BashParams(ActionParams):
    """
    :var bash_command: Bash command to execute on the target.

    :example bash_command: ls -l /etc/data/db
    """

    bash_command: str


class PrometheusParams(ActionParams):
    """
    :var prometheus_url: Prometheus url. If omitted, we will try to find a prometheus instance in the same cluster

    :example prometheus_url: "http://prometheus-k8s.monitoring.svc.cluster.local:9090"
    """

    prometheus_url: str = None


class GrafanaParams(ActionParams):
    """
    :var grafana_url: http(s) url of grafana or None for autodetection of an in-cluster grafana
    :var grafana_api_key: grafana key with write permissions.
    :var grafana_dashboard_uid: dashboard ID as it appears in the dashboard's url

    :example grafana_url: http://grafana.namespace.svc
    :example grafana_dashboard_uid: 09ec8aa1e996d6ffcd6817bbaff4db1b
    """

    grafana_api_key: SecretStr
    grafana_dashboard_uid: str
    grafana_url: str = None


class GrafanaAnnotationParams(GrafanaParams):
    """
    :var grafana_dashboard_panel: when present, annotations will be added only to panels with this text in their title.
    :var cluster_name: writen as one of the annotation's tags
    :var custom_tags: custom tags to add to the annotation
    """

    grafana_dashboard_panel: str = None
    cluster_name: str = None
    cluster_zone: str = None
    custom_tags: List[str] = None


class PythonProcessParams(ActionParams):
    """
    :var process_substring: process name (or substring).
    :var pid: pid
    :var interactive: if more than one process matches, interactively ask which process to choose.
    """

    process_substring: str = ""
    pid: int = None
    interactive: bool = True

    def has_exactly_one_match(self, all_processes: List[Process]) -> bool:
        """
        Returns true when exactly one process matches this class's filters
        """
        return len(self.get_matches(all_processes)) == 1

    def get_exact_match(self, all_processes: List[Process]) -> Process:
        """
        Returns a process matching this class and throws when there is more than one match
        """
        matches = self.get_matches(all_processes)
        if len(matches) != 1:
            raise Exception("Only one match is expected")
        return matches[0]

    def get_matches(self, all_processes: List[Process]) -> List[Process]:
        """
        Returns all_processes filtered by this class
        """
        pid_to_process = {p.pid: p for p in all_processes}

        if self.pid is None:
            return [
                p
                for p in pid_to_process.values()
                if "python" in p.exe and self.process_substring in " ".join(p.cmdline)
            ]

        if self.pid not in pid_to_process:
            return []

        return [pid_to_process[self.pid]]

    def __retrigger_blocks_for_processes(
        self, processes: List[Process], pod: RobustaPod, text: str, action: Callable
    ) -> List[BaseBlock]:
        blocks = [
            TableBlock(
                [[p.pid, p.exe, " ".join(p.cmdline)] for p in processes],
                ["pid", "exe", "cmdline"],
            ),
        ]
        if self.interactive:
            choices = {}
            for proc in processes:
                updated_params = self.copy()
                updated_params.process_substring = ""
                updated_params.pid = proc.pid
                choices[f"{text} {proc.pid}"] = CallbackChoice(
                    action=action,
                    action_params=updated_params,
                    kubernetes_object=pod,
                )
            blocks.append(CallbackBlock(choices))
            blocks.append(
                MarkdownBlock(
                    "*After clicking a button please wait up to 120 seconds for a response*"
                )
            )
        return blocks

    def get_retrigger_blocks(
        self, all_processes: List[Process], pod: RobustaPod, text: str, action: Callable
    ) -> List[BaseBlock]:
        """
        Return Blocks which will allow you to retrigger an action with a chosen process.
        """
        relevant_processes = self.get_matches(all_processes)
        if len(relevant_processes) == 1:
            raise Exception(
                "Retrigger not supported when there is only one matching process"
            )

        if len(relevant_processes) == 0:
            return [
                MarkdownBlock(f"No matching processes. The processes in the pod are:")
            ] + self.__retrigger_blocks_for_processes(all_processes, pod, text, action)
        elif len(relevant_processes) > 1:
            return [
                MarkdownBlock(
                    f"More than one matching process. The matching processes are:"
                )
            ] + self.__retrigger_blocks_for_processes(
                relevant_processes, pod, text, action
            )
