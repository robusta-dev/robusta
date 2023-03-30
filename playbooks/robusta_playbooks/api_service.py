import json
import logging
from typing import List, Optional

import yaml
from kubernetes.client import ApiregistrationV1Api, V1APIServiceList
from pydantic import BaseModel
from robusta.api import BaseBlock, FileBlock, MarkdownBlock, PrometheusKubernetesAlert, action


class ApiServiceConditions(BaseModel):
    message: Optional[str]
    reason: Optional[str]
    status: Optional[str]
    type: Optional[str]


class ApiService(BaseModel):
    name: str
    service_name: Optional[str]
    service_namespace: Optional[str]
    conditions: List[ApiServiceConditions]
    full_json: dict

    def get_json(self):
        return self.full_json

    def get_yaml(self):
        # remove noisy fields
        if self.full_json.get("metadata", {}).get("managedFields", {}):
            del self.full_json["metadata"]["managedFields"]
        last_applied = "kubectl.kubernetes.io/last-applied-configuration"
        if self.full_json.get("metadata", {}).get("annotations", {}).get(last_applied):
            del self.full_json["metadata"]["annotations"][last_applied]
        return yaml.dump(self.full_json)

    def get_available_condition(self) -> Optional[ApiServiceConditions]:
        if not self.conditions:
            return None
        available_conditions = [condition for condition in self.conditions if condition.type == "Available"]
        if not available_conditions:
            return None
        return available_conditions[0]

    @staticmethod
    def parse_apiservice(apiservice: dict, name: str):
        service = apiservice.get("spec", {}).get("service", {})
        service_name = service.get("name")
        namespace = service.get("namespace")
        conditions = apiservice.get("status", {}).get("conditions", [])
        return ApiService(
            name=name,
            service_name=service_name,
            service_namespace=namespace,
            conditions=conditions,
            full_json=apiservice,
        )


def get_api_service(name: str) -> Optional[ApiService]:
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
        return ApiService.parse_apiservice(api_service, name=name)
    except Exception:
        logging.error(f"Failed getting api_services", exc_info=True)
    return None


def get_apiservice_no_service_blocks(apiservice: ApiService) -> List[BaseBlock]:
    return [
        MarkdownBlock(
            f"The APIServer was extended with APIs from `{apiservice.service_namespace}/{apiservice.service_name}`. "
            f"However, this service doesn't exist."
        ),
        MarkdownBlock(
            f"To fix this alert, restore that service or remove it from the APIServer by running: "
            f"```kubectl delete apiservice {apiservice.name}```"
        ),
    ]


def get_apiservice_yaml_blocks(apiservice: ApiService) -> List[BaseBlock]:
    try:
        apiservice_yaml = apiservice.get_yaml()
        has_service = apiservice.service_name and apiservice.service_namespace
        error_text = (
            f"The APIServer was extended with APIs from `{apiservice.service_name}/{apiservice.service_namespace}` which has an error."
            if has_service
            else f"The APIService {apiservice.name} has an error. "
        )
        return [
            MarkdownBlock(error_text + f"Below is the relevant YAML definition."),
            FileBlock(f"{apiservice.name}.yaml", apiservice_yaml.encode()),
        ]
    except Exception:
        logging.error(f"error with apiservice yaml", exc_info=True)


@action
def api_service_status_enricher(alert: PrometheusKubernetesAlert):
    apiservice_name = alert.alert.labels.get("name", "")
    if not apiservice_name:
        logging.info(f"No apiservice name for api_service_status_enricher.")
        return
    apiservice: ApiService = get_api_service(apiservice_name)
    if not apiservice:
        logging.info(f"Apiservice {apiservice_name} not found for api_service_status_enricher.")
        return

    available_condition = apiservice.get_available_condition()
    if not available_condition:
        logging.info(f"Apiservice {apiservice.name} missing available status's api_service_status_enricher.")
        return

    available_status = available_condition.status == "True"

    # Enrich for no ServiceNotFound
    if available_condition.reason == "ServiceNotFound" and not available_status:
        blocks = get_apiservice_no_service_blocks(apiservice)
        if blocks:
            alert.add_enrichment(blocks)
            return

    # Enrich with yaml
    blocks = get_apiservice_yaml_blocks(apiservice)
    alert.add_enrichment(blocks)
