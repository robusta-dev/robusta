import json
import logging
from typing import Optional

from kubernetes.client import ApiregistrationV1Api, V1APIServiceList
from robusta.api import PrometheusKubernetesAlert, action


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

@action
def api_service_status_enricher(alert: PrometheusKubernetesAlert):
    apiservice_name = alert.alert.labels.get("name", "")
    if not apiservice_name:
        logging.info(f"No apiservice name for api_service_status_enricher.")
        return
    #"v1beta1.metrics.k8s.io"
    apiservice = get_api_service(apiservice_name)
    if not apiservice:
        logging.info(f"Apiservice {apiservice_name} not found for api_service_status_enricher.")
        return
    # if has service, list service status
    # list apiservice status