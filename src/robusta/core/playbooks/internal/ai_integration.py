import json
import logging

import requests

from robusta.core.model.base_params import AIInvestigateParams, HolmesWorkloadHealthParams
from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.playbooks.actions_registry import action
from robusta.core.reporting import Finding, FindingSubject
from robusta.core.reporting.base import EnrichmentType
from robusta.core.reporting.consts import FindingSubjectType, FindingType
from robusta.core.reporting.holmes import HolmesRequest, HolmesResult, HolmesResultsBlock
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

        finding = Finding(
            title=f"AI Analysis of {investigation__title}{title_suffix}",
            aggregation_key="HolmesInvestigationResult",
            subject=FindingSubject(
                name=params.resource.name if params.resource else "",
                namespace=params.resource.namespace if params.resource else "",
                subject_type=FindingSubjectType.from_kind(params.resource.kind) if params.resource else FindingSubjectType.TYPE_NONE,
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
        logging.exception(f"Failed to get holmes analysis for {investigation__title} {params.context} {subject}")
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

        finding = Finding(
            title=f"AI Analysis of {params.resource}",
            aggregation_key="HolmesInvestigationResult",
            subject=FindingSubject(
                name=params.resource.name if params.resource else "",
                namespace=params.resource.namespace if params.resource else "",
                subject_type=FindingSubjectType.from_kind(params.resource.kind) if params.resource else FindingSubjectType.TYPE_NONE,
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
        logging.exception(f"Failed to get holmes analysis for {params.resource}, {params.ask}")
        if isinstance(e, requests.ConnectionError):
            raise ActionException(ErrorCodes.HOLMES_CONNECTION_ERROR, "Holmes endpoint is currently unreachable.")
        elif isinstance(e, requests.HTTPError):
            if e.response.status_code == 401 and "invalid_api_key" in e.response.text:
                raise ActionException(ErrorCodes.HOLMES_REQUEST_ERROR, "Holmes invalid api key.")

            raise ActionException(ErrorCodes.HOLMES_REQUEST_ERROR, "Holmes internal configuration error.")
        else:
            raise ActionException(ErrorCodes.HOLMES_UNEXPECTED_ERROR, "An unexpected error occured.")