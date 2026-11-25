from enum import Enum
from typing import Callable, List, Optional

from robusta.core.model.base_params import ProcessParams
from robusta.core.reporting.base import Finding
from robusta.core.reporting.blocks import BaseBlock, MarkdownBlock, TableBlock
from robusta.integrations.kubernetes.custom_models import Process, RobustaPod


class ProcessType(Enum):
    PYTHON = "python3"
    JAVA = "java"


class ProcessFinder:
    """
    Find the processes in a Kubernetes pod which match certain filters.
    """

    def __init__(self, pod: RobustaPod, filters: ProcessParams, process_type: ProcessType):
        if process_type not in {ProcessType.PYTHON, ProcessType.JAVA}:
            raise Exception(f"Unsupported process type: {process_type}")
        self.pod = pod
        self.filters = filters
        self.process_type = process_type
        self.all_processes = pod.get_processes(custom_annotations=filters.custom_annotations)
        self.matching_processes = self.__get_matches(self.all_processes, filters, process_type)

    def get_match_or_report_error(
        self, finding: Finding, retrigger_text: str, retrigger_action: Callable, debug_action: Callable
    ) -> Optional[Process]:
        """
        Returns the single-matching process. If more than one process matches, blocks will be added to the Finding
        to report the error and list the processes. The retrigger arguments are unused: the actions that call
        this are local-only, so a button cannot re-trigger them.
        """
        if self.has_exactly_one_match():
            return self.get_exact_match()
        elif len(self.matching_processes) == 0:
            finding.add_enrichment(
                [MarkdownBlock("No matching processes. The processes in the pod are:")]
                + self.__get_error_blocks(self.all_processes)
            )
            return None
        elif len(self.matching_processes) > 1:
            finding.add_enrichment(
                [MarkdownBlock("More than one matching process. The matching processes are:")]
                + self.__get_error_blocks(self.matching_processes)
            )
            return None

    def has_exactly_one_match(self) -> bool:
        """
        Returns true when exactly one process matches
        """
        return len(self.matching_processes) == 1

    def get_pids(self) -> List[int]:
        """
        Returns all relevant pids
        """
        return [p.pid for p in self.matching_processes]

    def get_lowest_relevant_pid(self) -> int:
        """
        Returns the lowest pid which is most likely the parent process
        """
        return min([p.pid for p in self.matching_processes])

    def get_exact_match(self) -> Process:
        """
        Returns a process matching this class and throws when there is more than one match
        """
        if len(self.matching_processes) != 1:
            raise Exception("Only one match is expected")
        return self.matching_processes[0]

    @staticmethod
    def __get_matches(processes: List[Process], filters: ProcessParams, process_type: ProcessType) -> List[Process]:
        """
        Returns the processes that match a ProcessParams class
        """
        pid_to_process = {p.pid: p for p in processes}

        if filters.pid is None:
            return [
                p
                for p in pid_to_process.values()
                if process_type.value in p.exe and filters.process_substring in " ".join(p.cmdline)
            ]

        if filters.pid not in pid_to_process:
            return []

        return [pid_to_process[filters.pid]]

    @staticmethod
    def __get_error_blocks(processes: List[Process]) -> List[BaseBlock]:
        if not processes:
            return [MarkdownBlock("No processes")]
        return [
            TableBlock(
                [[p.pid, p.exe, " ".join(p.cmdline)] for p in processes],
                ["pid", "exe", "cmdline"],
            ),
            MarkdownBlock("To choose a process, set `pid` in this action's parameters in your playbook."),
        ]
