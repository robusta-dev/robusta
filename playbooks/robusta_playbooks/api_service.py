import json
import logging
from typing import List, Optional

from kubernetes.client import ApiregistrationV1Api, V1APIServiceList
from robusta.api import BaseBlock, MarkdownBlock, PrometheusKubernetesAlert, action


def get_api_service(name: str) -> Optional[str]:
    try:
        field_selector = f"metadata.name={name}"
        api_services_json: V1APIServiceList = (
            ApiregistrationV1Api()
            .list_api_service(field_selector=field_selector, _preload_content=False)
            .data.decode("utf-8")
        )
        api_services_json_list = json.loads(api_services_json).get("items", [])
        if len(api_services_json_list) == 0:
            logging.info(f"Api service {name} not found.")
            return None
        if len(api_services_json_list) > 1:
            logging.info(f"Too many matching api services found.")
            return None
        api_service = api_services_json_list[0]
        logging.warning(json.dumps(api_service, indent=1))
        return api_service
    except Exception:
        logging.error(f"Failed getting api_services", exc_info=True)
    return None


def investigate_service(name: str, namespace: str):
    # check if exists if not respond with "service X does not exist"
    # return service status
    pass


def get_apiservice_available_condition(apiservice):
    conditions = apiservice.get("status", {}).get("conditions", [])
    if not conditions:
        logging.info(f"Apiservice {apiservice.metadata.name} no conditions found api_service_status_enricher.")
        return None
    available_conditions = [condition for condition in conditions if condition.get("type", "") == "Available"]
    if not available_conditions:
        logging.info(
            f"Apiservice {apiservice.metadata.name} no available conditions found api_service_status_enricher."
        )
        return None
    return available_conditions[0]


@action
def api_service_status_enricher(alert: PrometheusKubernetesAlert):
    apiservice_name = alert.alert.labels.get("name", "")
    if not apiservice_name:
        logging.info(f"No apiservice name for api_service_status_enricher.")
        return
    apiservice = get_api_service(apiservice_name)
    if not apiservice:
        logging.info(f"Apiservice {apiservice_name} not found for api_service_status_enricher.")
        return
    blocks: List[BaseBlock] = []
    # if has service, list service status
    # list apiservice status is not available list reason and message
    available_condition = get_apiservice_available_condition(apiservice)
    if not available_condition:
        logging.info(f"Apiservice {apiservice_name} missing available status's api_service_status_enricher.")
        return

    available_status = available_condition.get("status") == "True"
    reason = available_condition.get("reason")
    message = available_condition.get("message")
    blocks.append(MarkdownBlock(f"*Apiservice status details:*\n{available_status}, *{reason}-* {message}"))
    alert.add_enrichment(blocks)
