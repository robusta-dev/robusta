from typing import Dict
import logging

import requests
import zeep

from robusta.core.reporting.base import BaseBlock, Emojis, Finding, FindingStatus
from robusta.core.sinks.servicenow.servicenow_sink_params import ServiceNowSinkParams


class ServiceNowSender:
    def __init__(self, params: ServiceNowSinkParams, account_id: str, cluster_name: str, signing_key: str):
        self.session = requests.Session()
        self.session.auth = requests.auth.HTTPBasicAuth(params.username, params.password.get_secret_value())
        self.transport = zeep.transports.Transport(session=self.session)
        self.params = params
        self.account_id = account_id
        self.cluster_name = cluster_name
        self.signing_key = signing_key

    def send_finding(self, finding: Finding, platform_enabled: bool):
        status: FindingStatus = (
            FindingStatus.RESOLVED if finding.title.startswith("[RESOLVED]") else FindingStatus.FIRING
        )

        message = self.format_message(finding)
        header = self.format_header(finding, status)
        wsdl_url = f"https://{self.params.instance}.service-now.com/incident.do?WSDL"
        client = zeep.CachingClient(wsdl_url, transport=self.transport)
        soap_payload = self.params_to_soap_payload(self.get_params_dict(header, message, self.params.caller_id))
        response = client.service.insert(**soap_payload)
        logging.warning(f"XXXXX {response=}")

    @staticmethod
    def format_message(finding: Finding) -> str:
        return ""

    def format_header(self, finding: Finding, status: FindingStatus) -> str:
        title = finding.title.removeprefix("[RESOLVED] ")
        sev = finding.severity
        status_name: str = "Prometheus Alert Firing" if status == FindingStatus.FIRING else "Resolved"
        status_str: str = f"{status.to_emoji()} {status_name}" if finding.add_silence_url else ""
        return f"{status_str} {sev.to_emoji()} {sev.name.upper()} {sev.to_emoji()} {title}"

# f'[code]<a href="{finding.get_investigate_uri(self.account_id, self.cluster_name)}"><b></b>[/code]'

    @staticmethod
    def get_params_dict(short_desc: str, message :str, caller_id: str) -> Dict[str, str]:
        result = {
            "impact": "1",
            "urgency": "1",
            "priority": "1",
            "category": "High",
            "location": "Warsaw",
            "user": "fred.luddy@yourcompany.com",
            # "assignment_group": "Technical Support",
            # "assigned_to": "David Loo",
            "short_description": short_desc,
            "comments": message,
        }
        if caller_id:
            result["caller_id"] = caller_id
        return result

    def params_to_soap_payload(self, params_dict: Dict) -> Dict:
        result = {
            "impact": int(params_dict["impact"]),
            "urgency": int(params_dict["urgency"]),
            "priority": int(params_dict["priority"]),
            "category": params_dict["category"],
            "location": params_dict["location"],
            # assignment_group=params_dict["assignment_group"],
            # assigned_to=params_dict["assigned_to"],
            "short_description": params_dict["short_description"],
            "comments": params_dict["comments"],
        }
        if "caller_id" in params_dict:
            result["caller_id"] = params_dict["caller_id"]
        return result
