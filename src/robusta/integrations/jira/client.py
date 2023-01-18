import logging
from typing import Optional

from requests.auth import HTTPBasicAuth
from requests_toolbelt import MultipartEncoder

from robusta.core.sinks.jira.jira_sink_params import JiraSinkParams
from robusta.integrations.common.requests import HttpMethod, check_response_succeed, process_request

_API_PREFIX = "rest/api/3"


class JiraClient:
    headers = {"Content-type": "application/json", "X-Atlassian-Token": "no-check"}
    configured = True

    def __init__(self, jira_params: JiraSinkParams):
        self.params = jira_params
        self.default_issue_type_id = self._get_default_issue_type()
        self.default_project_id = self._get_default_project_id()
        if not self.default_issue_type_id:
            logging.warning("Couldn't find the default issue type!")
            self.configured = False
        if not self.default_project_id:
            logging.warning("Couldn't find the project!")
            self.configured = False

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
            response = response.json()
            return response
        else:
            logging.error(f"Response to {url} received an error code: {response.status_code}")
            logging.info(response.request)
            return None

    def list_issues(self, search_params: Optional[str] = None):
        endpoint = "search"
        search_params = search_params or ""
        url = self._get_full_jira_url(endpoint)
        query = {"jql": search_params}
        return self._call_jira_api(url, params=query) or []

    def create_issue(self, issue_data, issue_attachments=None):
        endpoint = "issue"
        url = self._get_full_jira_url(endpoint)
        issue_exists = self._check_issue_exists(issue_data.get("labels", []))
        if issue_exists:
            return
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
        issue_id = response.get("id")
        if issue_id and issue_attachments:
            self.add_attachment(issue_id, issue_attachments)

    def add_attachment(self, issue_id, issue_attachments):
        endpoint = f"issue/{issue_id}/attachments"
        url = self._get_full_jira_url(endpoint)
        for attachment in issue_attachments:
            data = MultipartEncoder(fields={"file": attachment})
            request_headers = {"Content-type": data.content_type}
            response = self._call_jira_api(url, http_method=HttpMethod.POST, data=data, headers=request_headers) or {}
            logging.debug(response)

    def _check_issue_exists(self, labels):
        query = []
        for label in labels:
            query.append(f"labels = '{label}'")
        query = " AND ".join(query)
        issues = self.list_issues(query)
        if issues.get("total", 0) < 1:
            return False
        return True

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
