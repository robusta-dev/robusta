import json
import logging

import requests

from robusta.core.model.base_params import AIInvestigateParams
from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.playbooks.actions_registry import action
from robusta.core.reporting import Finding, FindingSubject
from robusta.core.reporting.base import EnrichmentType
from robusta.core.reporting.consts import FindingSubjectType, FindingType
from robusta.core.reporting.holmes import HolmesRequest, HolmesResult, HolmesResultsBlock
from robusta.integrations.prometheus.utils import HolmesDiscovery


def build_investigation_title(investigation__type: str, params: AIInvestigateParams) -> str:
    if investigation__type == "analyze_problems":
        return params.ask

    return params.context.get("issue_type", "unknown health issue")


@action
def ask_holmes(event: ExecutionBaseEvent, params: AIInvestigateParams):
    holmes_url = HolmesDiscovery.find_holmes_url(params.holmes_url)
    if not holmes_url:
        logging.error("Holmes url not found")
        return

    investigation__title = build_investigation_title(params.investigation_type, params)
    subject = params.resource.dict() if params.resource else {}
    try:
        holmes_req = HolmesRequest(
            source=params.context.get("source", "unknown source"),
            title=f"{investigation__title}",
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
            if params.resource.name and params.resource.name.lower() != "unresolved"
            else ""
        )

        finding = Finding(
            title=f"AI Analysis of {investigation__title}{title_suffix}",
            aggregation_key="HolmesInvestigationResult",
            subject=FindingSubject(
                name=params.resource.name,
                namespace=params.resource.namespace,
                subject_type=FindingSubjectType.from_kind(params.resource.kind),
                node=params.resource.node,
                container=params.resource.container,
            ),
            finding_type=FindingType.AI_ANALYSIS,
            failure=False,
        )
        finding.add_enrichment(
            [HolmesResultsBlock(holmes_result=holmes_result)], enrichment_type=EnrichmentType.ai_analysis
        )

        event.add_finding(finding)

    except Exception:
        logging.exception(f"Failed to get holmes analysis for {investigation__title} {params.context} {subject}")
