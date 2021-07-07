import logging
import json
import textwrap
from enum import IntEnum
from typing import Optional
from robusta.api import *

RATIONALE_FOR_REMOVING_LIMIT = textwrap.dedent("""\
    <https://twitter.com/thockin/status/1134193838841401345|Kubernetes maintainers like Tim Hockin recommend not using 
    CPU limits at all.> Contrary to common belief, <https://github.com/kubernetes/community/blob/master/contributors/
    design-proposals/node/resource-qos.md#compressible-resource-guarantees|even if you remove this pod's CPU limit, 
    other pods are still guaranteed the CPU they requested.> The only difference is how spare CPU is distributed
    """).replace("\n", "")


# four-valued logic where we differentiate between not knowing because we didn't ask the user yet
# and not knowing because we asked but the user themselves doesn't know
# we use an IntEnum and not Enum because IntEnums are json-serializable
class FourValuedLogic(IntEnum):
    NO = 0
    YES = 1
    NO_INPUT = 2
    USER_DOESNT_KNOW = 3

    def possibly_true(self):
        return self.value in [FourValuedLogic.YES, FourValuedLogic.USER_DOESNT_KNOW]

    def yes(self):
        return self.value == FourValuedLogic.YES

    def no(self):
        return self.value == FourValuedLogic.NO


class CpuThrottlingQuestion(IntEnum):
    LATENCY = 1
    EXPANSION = 2
    DONE = 3


class CpuThrottlingAnalysis(BaseModel):
    # TODO: we should add a pydantic field for pod's which automatically serializes to name+namespace
    # but deserializes to the hikaru object
    pod_name: str
    namespace: str
    # TODO: these can eventually be service-level parameters
    # which we know because we asked the user or they are known services like kafka, mongodb, etc
    is_latency_critical: FourValuedLogic = FourValuedLogic.NO_INPUT
    is_expansion_desired: FourValuedLogic = FourValuedLogic.NO_INPUT
    current_question: Optional[CpuThrottlingQuestion] = None


def do_cpu_throttling_answer(event, answer: FourValuedLogic):
    analysis = CpuThrottlingAnalysis(**json.loads(event.source_context))
    if analysis.current_question == CpuThrottlingQuestion.LATENCY:
        analysis.is_latency_critical = answer
    elif analysis.current_question == CpuThrottlingQuestion.EXPANSION:
        analysis.is_expansion_desired = answer
    else:
        raise Exception(f"Unknown question: {analysis.current_question}")
    pod = RobustaPod.read(analysis.pod_name, analysis.namespace)
    event.report_blocks.extend(do_cpu_throttling_analysis(pod, analysis))
    event.report_title = "Throttling report"
    event.slack_allow_unfurl = False
    send_to_slack(event)


@on_report_callback
def cpu_throttling_answer_yes(event: ReportCallbackEvent):
    do_cpu_throttling_answer(event, FourValuedLogic.YES)


@on_report_callback
def cpu_throttling_answer_no(event: ReportCallbackEvent):
    do_cpu_throttling_answer(event, FourValuedLogic.NO)


@on_report_callback
def cpu_throttling_answer_unknown(event: ReportCallbackEvent):
    do_cpu_throttling_answer(event, FourValuedLogic.USER_DOESNT_KNOW)


@on_report_callback
def cpu_throttling_restart_analysis(event: ReportCallbackEvent):
    analysis = CpuThrottlingAnalysis(**json.loads(event.source_context))
    analysis.is_latency_critical = FourValuedLogic.NO_INPUT
    analysis.is_expansion_desired = FourValuedLogic.NO_INPUT
    analysis.current_question = None
    pod = RobustaPod.read(analysis.pod_name, analysis.namespace)
    event.report_blocks.extend(do_cpu_throttling_analysis(pod, analysis))
    event.report_title = "Throttling report"
    event.slack_allow_unfurl = False
    send_to_slack(event)


def do_cpu_throttling_analysis(pod: Pod, analysis: CpuThrottlingAnalysis = None) -> List[BaseBlock]:
    logging.info(f"running cpu throttling analysis on {pod.metadata.name}")

    if analysis is None:
        analysis = CpuThrottlingAnalysis(pod_name=pod.metadata.name, namespace=pod.metadata.namespace)

    # gather data
    if analysis.is_latency_critical == FourValuedLogic.NO_INPUT:
        analysis.current_question = CpuThrottlingQuestion.LATENCY
        return [
            MarkdownBlock("*This pod is throttled. It wanted to use the CPU and was blocked due to it's CPU limit.*"),
            # TODO: move most of the text in this tip to our wiki page and just link to it
            MarkdownBlock("""\
                _Tip: This can occur even when CPU usage is far below the limit. For example, a pod will have low 
                CPU but be heavily throttled if it does nothing for 10 minutes and then uses the CPU nonstop for 
                200ms on 10 threads. The usage during the burst is equivalent to 2000m (200*10) and the pod's limit 
                must be above that to prevent throttling._""",
                          single_paragraph=True),
            MarkdownBlock("*To determine the correct alert response, more information is needed. "
                          "Does it matter if this pod has high latency?*"),
            # TODO: link to our wiki or add a button to "Help me decide"
            MarkdownBlock("_Tip: Latency usually matters for http servers, databases, and other servers which respond "
                          "to client requests. Latency does *not* matter for long running batch jobs._"),
            CallbackBlock(choices={f'Latency is important': cpu_throttling_answer_yes,
                                   'Latency is NOT important': cpu_throttling_answer_no,
                                   'I have no idea': cpu_throttling_answer_unknown},
                          context=analysis.dict())
        ]
    if analysis.is_expansion_desired == FourValuedLogic.NO_INPUT:
        analysis.current_question = CpuThrottlingQuestion.EXPANSION
        return [
            MarkdownBlock("Thank you. I have one more question."),
            MarkdownBlock("*If there is extra CPU available on the node, should this pod take advantage of it? Doing "
                          "so will _not_ steal CPU that other pods requested.*"),
            MarkdownBlock("""\
                _Tip: This is desirable rather than letting the CPU idle while the pod has work to do. 
                The only exception is if you define CPU requests for other pods too low (or not at all) and want those 
                pods to get extra CPU instead of this pod. *As long as all your CPU requests are approximately correct,
                you should choose to Allow Extra CPU*_""",
                          single_paragraph=True),
            CallbackBlock(choices={f'Use Extra CPU': cpu_throttling_answer_yes,
                                   "Don't use extra CPU": cpu_throttling_answer_no,
                                   "I don't know or care": cpu_throttling_answer_unknown},
                          context=analysis.dict())
        ]

    # make a decision
    restart_block = CallbackBlock(choices={f'Restart analysis': cpu_throttling_restart_analysis},
                                  context=analysis.dict())

    # latency is critical, expansion is OK
    if analysis.is_latency_critical.possibly_true() and analysis.is_expansion_desired.possibly_true():
        return [
            MarkdownBlock("*Robusta's Recommendation: You should remove this pod's CPU limit entirely.*"),
            MarkdownBlock(f"_Rationale: {RATIONALE_FOR_REMOVING_LIMIT}_"),
            MarkdownBlock(f"""\
                _*In your case, it is especially desirable to remove the limit because this service 
                {"is" if analysis.is_latency_critical.yes() else "might be"} latency sensitive and throttling can 
                dramatically increase latency.*_""",
                          single_paragraph=True),
            restart_block,
        ]
    # latency is not critical, expansion is OK
    elif analysis.is_latency_critical.no() and analysis.is_expansion_desired.possibly_true():
        return [
            MarkdownBlock("*Robusta's Recommendation: You should consider removing this pod's CPU limit entirely.*"),
            MarkdownBlock(f"_Rationale: {RATIONALE_FOR_REMOVING_LIMIT}_"),
            MarkdownBlock("""\
                _This pod isn't latency-sensitive, so occasional throttling is OK. On the other hand, you indicated that 
                you are OK with letting this pod use extra CPU rather than letting the CPU go idle, so there is no 
                reason not to get rid of the pod's CPU limit._""", single_paragraph=True),
            restart_block,
        ]
    # latency is critical, but expansion is not desired
    elif analysis.is_latency_critical.yes():
        return [
            MarkdownBlock("*Robusta's Recommendation: You should raise this pod's CPU limit until throttling stops*"),
            MarkdownBlock("""\
                _Rationale: This is a latency-sensitive pod so it is critical that it not be CPU throttled. Therefore 
                you must raise the limit. On the other hand, you don't want this pod to take unlimited advantage of 
                extra CPU, so you can't get rid of the limit entirely._""", single_paragraph=True),
            MarkdownBlock("""\
                _*Recommendation regarding the pod's CPU request:* If this pod is CPU throttled often, you 
                should raise the request as well as the limit so this pod is guaranteed the CPU it needs even when 
                the node has no spare CPU._""", single_paragraph=True),
            restart_block,
        ]
    # we have an explicit no to both questions
    else:
        return [
            MarkdownBlock("*Robusta's Recommendation: Raise this pod's CPU limit or raise the alert threshold.*"),
            MarkdownBlock("_Rationale: This pod is not latency sensitive so occasional throttling is OK. "
                          "You don't want this pod to take advantage of extra CPU so it needs a limit._"),
            MarkdownBlock("""\
                _What remains is to decide how much throttling you are OK with and modify the limit and alert threshold 
                until this alert stops firing. To find this balance, keep in mind that 25% throttling means that 25% of 
                this pod's needs for CPU were denied due to it's CPU limit. I'm sorry I can't help more in this case. 
                Good luck!_""", single_paragraph=True),
            restart_block,
        ]


@on_manual_trigger
def cpu_throttling_analysis(event: ManualTriggerEvent):
    pod = RobustaPod.read("metrics-server-v0.3.6-7b5cdbcbb8-wddbk", "kube-system")
    event.report_blocks.extend(do_cpu_throttling_analysis(pod))
    event.report_title = "Throttling report"
    event.slack_channel = "throttling-test"
    event.slack_allow_unfurl = False
    send_to_slack(event)
