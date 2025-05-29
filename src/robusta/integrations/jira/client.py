import logging
from typing import Optional, Dict

from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from requests_toolbelt import MultipartEncoder

from robusta.core.reporting.base import FindingStatus
from robusta.core.reporting.consts import FindingSource
from robusta.core.sinks.jira.jira_sink_params import JiraSinkParams
from robusta.integrations.common.requests import (
    HttpMethod,
    check_response_no_content,
    check_response_succeed,
    process_request,
)

_API_PREFIX = "rest/api/3"


class JiraClient:
    headers = {"Content-type": "application/json", "X-Atlassian-Token": "no-check"}
    configured = True

    def __init__(self, jira_params: JiraSinkParams):
        self.params = jira_params
        self.configured = True
        self.sendResolved = self.params.sendResolved
        self.reopenIssues = self.params.reopenIssues
        self.doneStatusName = self.params.doneStatusName
        self.reopenStatusName = self.params.reopenStatusName
        self.noReopenResolution = self.params.noReopenResolution
        if jira_params.issue_type_id_override:
            self.default_issue_type_id = jira_params.issue_type_id_override
        else:
            self.default_issue_type_id = self._get_default_issue_type()

        if jira_params.epic:
            self.epic = jira_params.epic
        
        if jira_params.assignee:
            self.assignee = jira_params.assignee


        if jira_params.project_type_id_override:
            self.default_project_id = jira_params.project_type_id_override
        else:
            self.default_project_id = self._get_default_project_id()

        if not self.default_issue_type_id:
            logging.warning("Could not find Jira default issue type!")
            self.configured = False
        if not self.default_project_id:
            logging.warning("Could not find Jira default project")
            self.configured = False

        if self.configured:
            logging.info(
                f"Jira initialized successfully. Project: {self.default_project_id} issue type: {self.default_issue_type_id}"
            )

        if jira_params.priority_mapping:
            if logging.getLogger().getEffectiveLevel() <= logging.DEBUG:
                self._validate_priorities(jira_params.priority_mapping)

    def _validate_priorities(self, priority_mapping: Dict[str, str]) -> None:
        """Validate that configured priorities exist in Jira"""
        endpoint = "priority"
        url = self._get_full_jira_url(endpoint)
        available_priorities = self._call_jira_api(url) or []
        available_priority_names = {p.get("name") for p in available_priorities}

        for severity, priority in priority_mapping.items():
            if priority not in available_priority_names:
                logging.warning(
                    f"Configured priority '{priority}' for severity '{severity}' "
                    f"is not available in Jira. Available priorities: {available_priority_names}"
                )

    def _get_full_jira_url(self, endpoint: str) -> str:
        return "/".join([self.params.url, _API_PREFIX, endpoint])

    def _construct_auth(self):
        return HTTPBasicAuth(self.params.username, self.params.api_key)

    def _call_jira_api(self, url, http_method: HttpMethod = HttpMethod.GET, **kwargs):
        if not self.configured:
            logging.warning(
                "Failed to configure default issue type and/or project, fix the errors so sink can work properly"
            )
            return None
        headers = self.headers.copy()
        headers.update(kwargs.pop("headers", {}))
        response = process_request(url, http_method, headers=headers, auth=self._construct_auth(), **kwargs)
        if check_response_succeed(response):
            return response.json()
        elif check_response_no_content(response):
            return
        else:
            logging.error(
                f"Response to {url} received an error code: {response.status_code} "
                f"reason: {response.reason} text: {response.text} data: {response.json()}"
            )
            logging.info(
                f"request: url: {response.request.url} "
                f"headers: {response.request.headers} body: {response.request.body}"
            )
            return None

    def _get_transition_id(self, issue_id, status_name):
        transitions = self._get_transitions_for_issue(issue_id)
        for t in transitions:
            if self._get_nested_property(t, "to.name", "").lower() == status_name.lower():
                return t.get("id", None)
        return None

    def _get_transitions_for_issue(self, issue_id):
        endpoint = f"issue/{issue_id}/transitions"
        url = self._get_full_jira_url(endpoint)
        logging.debug(f"Getting transitions for issue {issue_id}")
        response = self._call_jira_api(url, http_method=HttpMethod.GET) or {}
        logging.debug(response)
        return response.get("transitions", [])

    def _get_nested_property(self, my_dict, key, default=None):
        keys = key.split(".")
        current = my_dict

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    def _check_issue_done(self, issue):
        issue_status = self._get_nested_property(issue, "fields.status.name", "")
        return issue_status.lower() == self.doneStatusName.lower()

    def _get_issue_for_labels(self, labels):
        query = []
        for label in labels:
            query.append(f"labels = '{label}'")
        query = " AND ".join(query)
        issues = self.list_issues(query)

        if issues.get("total", 0) < 1:
            logging.debug(f"No issue exists for query: '{query}'.")
            return

        issue = issues.get("issues")[0]
        if issues.get("total", 0) > 1:
            logging.warning(f"More than one issue found for query: '{query}', picking most recent one")
            logging.debug(f"Picked issue '{issue}'")

        return issue

    def _get_default_issue_type(self):
        available_issue_types = self.get_available_issue_types()
        default_issue = next(
            (issue for issue in available_issue_types if issue.get("name") == self.params.issue_type), None
        )
        if default_issue:
            return default_issue["id"]
        return None

    def _get_default_project_id(self):
        available_projects = self.get_available_projects(self.params.project_name)
        available_projects = available_projects.get("values", [])
        default_issue = next(
            (
                issue
                for issue in available_projects
                if issue.get("name") == self.params.project_name or issue.get("key") == self.params.project_name
            ),
            None,
        )
        if default_issue:
            return default_issue["id"]
        return None

    def _resolve_priority(self, priority_name: str) -> dict:
        """Resolve Jira priority:
        1. User configured priority mapping (if defined)
        2. Fallback to current behavior (use priority name as-is)

        Returns:
            dict: Priority field in format {"name": str}
        """
        # 1. Try user configured priority mapping
        if hasattr(self, "params") and self.params.priority_mapping:
            for severity, mapped_name in self.params.priority_mapping.items():
                if mapped_name == priority_name:
                    return {"name": mapped_name}

        # 2. Fallback to current behavior
        return {"name": priority_name}

    def list_issues(self, search_params: Optional[str] = None):
        endpoint = "search"
        search_params = search_params or ""
        url = self._get_full_jira_url(endpoint)
        query = {"jql": search_params}
        return self._call_jira_api(url, params=query) or []

    def transition_issue(self, issue_id, status_name):
        endpoint = f"issue/{issue_id}/transitions"
        url = self._get_full_jira_url(endpoint)
        transition_id = self._get_transition_id(issue_id, status_name)
        if transition_id is None:
            logging.error(f"No '{status_name}' transition was found for issue with id {issue_id}")
            return
        payload = {
            "transition": {"id": f"{transition_id}"},
        }
        logging.debug(f"Transitioning issue {issue_id} to {status_name} status with payload: {payload}")
        response = self._call_jira_api(url, http_method=HttpMethod.POST, json=payload) or {}
        logging.debug(f"Transitioned issue with response {response}")

    def comment_issue(self, issue_id, text):
        endpoint = f"issue/{issue_id}/comment"
        url = self._get_full_jira_url(endpoint)
        payload = {
            "body": {
                "content": [
                    {
                        "content": [
                            {
                                "text": text,
                                "type": "text",
                            }
                        ],
                        "type": "paragraph",
                    }
                ],
                "type": "doc",
                "version": 1,
            }
        }
        logging.debug(f"Adding comment to issue {issue_id} with payload: {payload}")
        response = self._call_jira_api(url, http_method=HttpMethod.POST, json=payload) or {}
        logging.debug(response)

    def create_issue(self, issue_data, issue_attachments=None):
        endpoint = "issue"
        url = self._get_full_jira_url(endpoint)

        # Add priority resolution if it exists
        if "priority" in issue_data:
            priority_name = issue_data["priority"].get("name")
            if priority_name:
                issue_data["priority"] = self._resolve_priority(priority_name)

        payload = {
            "update": {},
            "fields": {
                **issue_data,
                "issuetype": {"id": str(self.default_issue_type_id)},
                "project": {"id": str(self.default_project_id)},
            },
        }
        logging.debug(f"Create issue with payload: {payload}")
        response = self._call_jira_api(url, http_method=HttpMethod.POST, json=payload) or {}
        logging.debug(response)
        issue_id = response.get("id")
        if issue_id and issue_attachments:
            self.add_attachment(issue_id, issue_attachments)

    def update_issue(self, issue_id, issue_data):
        summary = self._get_nested_property(issue_data, "summary", "")
        description = self._get_nested_property(issue_data, "description", "")
        endpoint = f"issue/{issue_id}"
        url = self._get_full_jira_url(endpoint)

        payload = {
            "fields": {
                "summary": summary,
                "description": description,
            }
        }

        # Only add assignee if defined
        if hasattr(self, 'assignee') and self.assignee:
            payload["fields"]["assignee"] = {"id": self.assignee}

        # Only add parent if epic is defined
        if hasattr(self, 'epic') and self.epic:
            payload["fields"]["parent"] = {"key": self.epic}

        logging.debug(f"Update issue '{issue_id}' with payload: {payload}")
        response = self._call_jira_api(url, http_method=HttpMethod.PUT, json=payload) or {}
        logging.debug(response)

    def manage_issue(self, issue_data, alert_data, issue_attachments=None):
        existing_issue = self._get_issue_for_labels(issue_data.get("labels", [])) or []
        status = self._get_nested_property(alert_data, "status", -1)
        source = self._get_nested_property(alert_data, "source", None)
        alert_resolved = status == FindingStatus.RESOLVED
        is_prometheus_alert = source == FindingSource.PROMETHEUS

        if not is_prometheus_alert:
            # It's not an alert fired from Prometheus, we simply create
            # a Jira issue without other logic involved
            self.create_issue(issue_data, issue_attachments)
        elif existing_issue:
            issue_done = self._check_issue_done(existing_issue)
            issue_id = self._get_nested_property(existing_issue, "id", -1)
            issue_resolution = self._get_nested_property(existing_issue, "fields.resolution.name", "")

            if issue_done:
                if alert_resolved:
                    logging.info(
                        f"Ignoring resolved alert that is already 'done' in Jira for issue with id '{issue_id}'"
                    )
                elif self.noReopenResolution and issue_resolution == self.noReopenResolution:
                    logging.info(f"Jira issue '{issue_id}' has '{issue_resolution}' resolution, we won't re-open it")
                elif self.reopenIssues:
                    self.transition_issue(issue_id, self.reopenStatusName)
                    self.update_issue(issue_id, issue_data)
                else:
                    self.create_issue(issue_data, issue_attachments)
            else:
                if alert_resolved:
                    if self.sendResolved:
                        self.transition_issue(issue_id, self.doneStatusName)
                        self.comment_issue(issue_id, "Issue was marked as resolved by the Alertmanager")
                    else:
                        logging.info("Alert is resolved but 'sendResolved' is false, so we don't update Jira")
                else:
                    self.update_issue(issue_id, issue_data)
        else:
            if not alert_resolved:
                self.create_issue(issue_data, issue_attachments)

    def add_attachment(self, issue_id, issue_attachments):
        endpoint = f"issue/{issue_id}/attachments"
        url = self._get_full_jira_url(endpoint)
        for attachment in issue_attachments:
            data = MultipartEncoder(fields={"file": attachment})
            request_headers = {"Content-type": data.content_type}
            response = self._call_jira_api(url, http_method=HttpMethod.POST, data=data, headers=request_headers) or {}
            logging.debug(response)

    def get_available_issue_types(self):
        endpoint = "issuetype"
        url = self._get_full_jira_url(endpoint)
        return self._call_jira_api(url) or []

    def get_available_projects(self, project_name=None):
        params = {}
        if project_name:
            params.update({"query": project_name})
        endpoint = "project/search"
        url = self._get_full_jira_url(endpoint)
        return self._call_jira_api(url, params=params) or {}
