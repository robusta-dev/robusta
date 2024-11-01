import json
import logging

import requests

from robusta.core.model.base_params import (
    AIInvestigateParams,
    HolmesChatParams,
    HolmesConversationParams,
    HolmesIssueChatParams,
    HolmesWorkloadHealthParams,
    ResourceInfo,
)
from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.playbooks.actions_registry import action
from robusta.core.reporting import Finding, FindingSubject
from robusta.core.reporting.base import EnrichmentType
from robusta.core.reporting.consts import FindingSubjectType, FindingType
from robusta.core.reporting.holmes import (
    HolmesChatRequest,
    HolmesChatResult,
    HolmesChatResultsBlock,
    HolmesConversationRequest,
    HolmesConversationResult,
    HolmesIssueChatRequest,
    HolmesRequest,
    HolmesResult,
    HolmesResultsBlock,
)
from robusta.core.schedule.model import FixedDelayRepeat
from robusta.integrations.kubernetes.autogenerated.events import KubernetesAnyChangeEvent
from robusta.integrations.prometheus.utils import HolmesDiscovery
from robusta.utils.error_codes import ActionException, ErrorCodes


def build_investigation_title(params: AIInvestigateParams) -> str:
    if params.investigation_type == "analyze_problems":
        return params.ask

    return params.context.get("issue_type", "unknown health issue")


@action
def ask_holmes(event: ExecutionBaseEvent, params: AIInvestigateParams):
    holmes_url = HolmesDiscovery.find_holmes_url(params.holmes_url)
    if not holmes_url:
        raise ActionException(ErrorCodes.HOLMES_DISCOVERY_FAILED, "Robusta couldn't connect to the Holmes client.")

    investigation__title = build_investigation_title(params)
    subject = params.resource.dict() if params.resource else {}

    try:
        holmes_req = HolmesRequest(
            source=params.context.get("source", "unknown source") if params.context else "unknown source",
            title=investigation__title,
            subject=subject,
            context=params.context if params.context else {},
            include_tool_calls=True,
            include_tool_call_results=True,
        )
        result = requests.post(f"{holmes_url}/api/investigate", data=holmes_req.json())
        result.raise_for_status()

        holmes_result = HolmesResult(**json.loads(result.text))
        title_suffix = (
            f" on {params.resource.name}"
            if params.resource and params.resource.name and params.resource.name.lower() != "unresolved"
            else ""
        )

        kind = params.resource.kind if params.resource else None
        finding = Finding(
            title=f"AI Analysis of {investigation__title}{title_suffix}",
            aggregation_key="HolmesInvestigationResult",
            subject=FindingSubject(
                name=params.resource.name if params.resource else "",
                namespace=params.resource.namespace if params.resource else "",
                subject_type=FindingSubjectType.from_kind(kind) if kind else FindingSubjectType.TYPE_NONE,
                node=params.resource.node if params.resource else "",
                container=params.resource.container if params.resource else "",
            ),
            finding_type=FindingType.AI_ANALYSIS,
            failure=False,
        )
        finding.add_enrichment(
            [HolmesResultsBlock(holmes_result=holmes_result)], enrichment_type=EnrichmentType.ai_analysis
        )

        event.add_finding(finding)

    except Exception as e:
        logging.exception(
            f"Failed to get holmes analysis for {investigation__title} {params.context} {subject}", exc_info=True
        )
        if isinstance(e, requests.ConnectionError):
            raise ActionException(ErrorCodes.HOLMES_CONNECTION_ERROR, "Holmes endpoint is currently unreachable.")
        elif isinstance(e, requests.HTTPError):
            if e.response.status_code == 401 and "invalid_api_key" in e.response.text:
                raise ActionException(ErrorCodes.HOLMES_REQUEST_ERROR, "Holmes invalid api key.")

            raise ActionException(ErrorCodes.HOLMES_REQUEST_ERROR, "Holmes internal configuration error.")
        else:
            raise ActionException(ErrorCodes.HOLMES_UNEXPECTED_ERROR, "An unexpected error occured.")


@action
def holmes_workload_health(event: ExecutionBaseEvent, params: HolmesWorkloadHealthParams):
    holmes_url = HolmesDiscovery.find_holmes_url(params.holmes_url)
    if not holmes_url:
        raise ActionException(ErrorCodes.HOLMES_DISCOVERY_FAILED, "Robusta couldn't connect to the Holmes client.")

    params.resource.cluster = event.get_context().cluster_name

    try:
        result = requests.post(f"{holmes_url}/api/workload_health_check", data=params.json())
        result.raise_for_status()

        holmes_result = HolmesResult(**json.loads(result.text))

        healthy = True
        try:
            analysis = json.loads(holmes_result.analysis)
            healthy = analysis.get("workload_healthy")
        except Exception:
            logging.exception("Error in holmes response format, analysis did not return the expecrted json format.")
            pass

        if params.silent_healthy and healthy:
            return

        finding = Finding(
            title=f"AI Health check of {params.resource}",
            aggregation_key="HolmesHealthCheck",
            subject=FindingSubject(
                name=params.resource.name if params.resource else "",
                namespace=params.resource.namespace if params.resource else "",
                subject_type=FindingSubjectType.from_kind(params.resource.kind)
                if params.resource
                else FindingSubjectType.TYPE_NONE,
                node=params.resource.node if params.resource else "",
                container=params.resource.container if params.resource else "",
            ),
            finding_type=FindingType.AI_ANALYSIS,
            failure=False,
        )
        finding.add_enrichment(
            [HolmesResultsBlock(holmes_result=holmes_result)], enrichment_type=EnrichmentType.ai_analysis
        )

        event.add_finding(finding)
    except Exception as e:
        logging.exception(f"Failed to get holmes analysis for {params.resource}, {params.ask}", exc_info=True)
        if isinstance(e, requests.ConnectionError):
            raise ActionException(ErrorCodes.HOLMES_CONNECTION_ERROR, "Holmes endpoint is currently unreachable.")
        elif isinstance(e, requests.HTTPError):
            if e.response.status_code == 401 and "invalid_api_key" in e.response.text:
                raise ActionException(ErrorCodes.HOLMES_REQUEST_ERROR, "Holmes invalid api key.")

            raise ActionException(ErrorCodes.HOLMES_REQUEST_ERROR, "Holmes internal configuration error.")
        else:
            raise ActionException(ErrorCodes.HOLMES_UNEXPECTED_ERROR, "An unexpected error occured.")


def build_conversation_title(params: HolmesConversationParams):
    return f"{params.resource}, {params.ask} for issue {params.context.robusta_issue_id}"


# old version of holmes conversation API
@action
def holmes_conversation(event: ExecutionBaseEvent, params: HolmesConversationParams):
    holmes_url = HolmesDiscovery.find_holmes_url(params.holmes_url)
    if not holmes_url:
        raise ActionException(ErrorCodes.HOLMES_DISCOVERY_FAILED, "Robusta couldn't connect to the Holmes client.")

    conversation_title = build_conversation_title(params)

    try:
        holmes_req = HolmesConversationRequest(
            user_prompt=params.ask,
            source=getattr(params.context, "source", "unknown source") if params.context else "unknown source",
            resource=params.resource,
            conversation_type=params.conversation_type,
            context=params.context,
            include_tool_calls=True,
            include_tool_call_results=True,
        )
        result = requests.post(f"{holmes_url}/api/conversation", data=holmes_req.json())
        result.raise_for_status()
        holmes_result = HolmesConversationResult(**json.loads(result.text))

        params_resource_kind = params.resource.kind or ""
        finding = Finding(
            title=f"AI Analysis of {conversation_title}",
            aggregation_key="HolmesConversationResult",
            subject=FindingSubject(
                name=params.resource.name if params.resource else "",
                namespace=params.resource.namespace if params.resource else "",
                subject_type=FindingSubjectType.from_kind(params_resource_kind)
                if params.resource
                else FindingSubjectType.TYPE_NONE,
                node=params.resource.node if params.resource else "",
                container=params.resource.container if params.resource else "",
            ),
            finding_type=FindingType.AI_ANALYSIS,
            failure=False,
        )
        finding.add_enrichment(
            [HolmesResultsBlock(holmes_result=holmes_result)], enrichment_type=EnrichmentType.ai_analysis
        )

        event.add_finding(finding)

    except Exception as e:
        logging.exception(f"Failed to get holmes chat for {conversation_title}", exc_info=True)
        if isinstance(e, requests.ConnectionError):
            raise ActionException(ErrorCodes.HOLMES_CONNECTION_ERROR, "Holmes endpoint is currently unreachable.")
        elif isinstance(e, requests.HTTPError):
            if e.response.status_code == 401 and "invalid_api_key" in e.response.text:
                raise ActionException(ErrorCodes.HOLMES_REQUEST_ERROR, "Holmes invalid api key.")

            raise ActionException(ErrorCodes.HOLMES_REQUEST_ERROR, "Holmes internal configuration error.")
        else:
            raise ActionException(ErrorCodes.HOLMES_UNEXPECTED_ERROR, "An unexpected error occured.")


class DelayedHealthCheckParams(HolmesWorkloadHealthParams):
    delay_seconds: int = 120


@action
def delayed_health_check(event: KubernetesAnyChangeEvent, action_params: DelayedHealthCheckParams):
    """
    runs a holmes workload health action with a delay
    """
    metadata = event.obj and event.obj.metadata

    if not action_params.ask:
        action_params.ask = f"help me diagnose an issue with a workload {metadata.namespace}/{event.obj.kind}/{metadata.name} running in my Kubernetes cluster. Can you assist with identifying potential issues and pinpoint the root cause."

    action_params.resource = ResourceInfo(name=metadata.name, namespace=metadata.namespace, kind=event.obj.kind)

    logging.info(f"Scheduling health check. {metadata.name} delays: {action_params.delay_seconds}")
    event.get_scheduler().schedule_action(
        action_func=holmes_workload_health,
        task_id=f"health_check_{metadata.name}_{metadata.namespace}",
        scheduling_params=FixedDelayRepeat(repeat=1, seconds_delay=action_params.delay_seconds),
        named_sinks=event.named_sinks,
        action_params=action_params,
        replace_existing=True,
        standalone_task=True,
    )


@action
def holmes_issue_chat(event: ExecutionBaseEvent, params: HolmesIssueChatParams):
    holmes_url = HolmesDiscovery.find_holmes_url(params.holmes_url)
    if not holmes_url:
        raise ActionException(ErrorCodes.HOLMES_DISCOVERY_FAILED, "Robusta couldn't connect to the Holmes client.")

    conversation_title = build_conversation_title(params)
    params_resource_kind = params.resource.kind or ""
    try:
        holmes_req = HolmesIssueChatRequest(
            ask=params.ask,
            conversation_history=params.conversation_history,
            investigation_result=params.context.investigation_result,
            issue_type=params.context.issue_type,
        )
        result = requests.post(f"{holmes_url}/api/issue_chat", data=holmes_req.json())
        result.raise_for_status()

        holmes_result = HolmesChatResult(**json.loads(result.text))

        finding = Finding(
            title=f"AI Analysis of {conversation_title}",
            aggregation_key="HolmesConversationResult",
            subject=FindingSubject(
                name=params.resource.name if params.resource else "",
                namespace=params.resource.namespace if params.resource else "",
                subject_type=FindingSubjectType.from_kind(params_resource_kind)
                if params.resource
                else FindingSubjectType.TYPE_NONE,
                node=params.resource.node if params.resource else "",
                container=params.resource.container if params.resource else "",
            ),
            finding_type=FindingType.AI_ANALYSIS,
            failure=False,
        )
        finding.add_enrichment(
            [HolmesChatResultsBlock(holmes_result=holmes_result)], enrichment_type=EnrichmentType.ai_analysis
        )

        event.add_finding(finding)

    except Exception as e:
        logging.exception(f"Failed to get holmes chat for {conversation_title}", exc_info=True)
        if isinstance(e, requests.ConnectionError):
            raise ActionException(ErrorCodes.HOLMES_CONNECTION_ERROR, "Holmes endpoint is currently unreachable.")
        elif isinstance(e, requests.HTTPError):
            if e.response.status_code == 401 and "invalid_api_key" in e.response.text:
                raise ActionException(ErrorCodes.HOLMES_REQUEST_ERROR, "Holmes invalid api key.")

            raise ActionException(ErrorCodes.HOLMES_REQUEST_ERROR, "Holmes internal configuration error.")
        else:
            raise ActionException(ErrorCodes.HOLMES_UNEXPECTED_ERROR, "An unexpected error occured.")


@action
def holmes_chat(event: ExecutionBaseEvent, params: HolmesChatParams):
    holmes_url = HolmesDiscovery.find_holmes_url(params.holmes_url)
    if not holmes_url:
        raise ActionException(ErrorCodes.HOLMES_DISCOVERY_FAILED, "Robusta couldn't connect to the Holmes client.")

    cluster_name = event.get_context().cluster_name
    account_id = event.get_context().account_id

    try:
        holmes_req = HolmesChatRequest(ask=params.ask, conversation_history=params.conversation_history)
        result = requests.post(f"{holmes_url}/api/chat", data=holmes_req.json())
        result.raise_for_status()
        holmes_result = HolmesChatResult(**json.loads(result.text))

        finding = Finding(
            title=f"AI Ask Chat for {cluster_name} cluster {account_id} account_id",
            aggregation_key="HolmesChatResult",
            subject=FindingSubject(
                subject_type=FindingSubjectType.TYPE_NONE,
            ),
            finding_type=FindingType.AI_ANALYSIS,
            failure=False,
        )
        finding.add_enrichment(
            [HolmesChatResultsBlock(holmes_result=holmes_result)], enrichment_type=EnrichmentType.ai_analysis
        )

        event.add_finding(finding)

    except Exception as e:
        logging.exception(f"Failed to get holmes chat for {cluster_name} cluster {account_id} account_id")
        if isinstance(e, requests.ConnectionError):
            raise ActionException(ErrorCodes.HOLMES_CONNECTION_ERROR, "Holmes endpoint is currently unreachable.")
        elif isinstance(e, requests.HTTPError):
            if e.response.status_code == 401 and "invalid_api_key" in e.response.text:
                raise ActionException(ErrorCodes.HOLMES_REQUEST_ERROR, "Holmes invalid api key.")

            raise ActionException(ErrorCodes.HOLMES_REQUEST_ERROR, "Holmes internal configuration error.")
        else:
            raise ActionException(ErrorCodes.HOLMES_UNEXPECTED_ERROR, "An unexpected error occured.")
