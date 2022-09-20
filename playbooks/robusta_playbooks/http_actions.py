from robusta.api import ActionParams, action, ExecutionBaseEvent, FileBlock, Finding, Optional, FindingSource, FindingType, MarkdownBlock
from urllib.error import URLError, HTTPError
import requests


class HTTP_GET(ActionParams):
    """
    :var url: In cluster target url.
    :var get_response: (optional) (Default: False) Send results to sink.
    :var params: (optional) Dictionary, list of tuples or bytes to send
        in the query string
    """

    url: str
    get_response: Optional[bool] = False
    params: Optional[dict] = None


@action
def http_get(event: ExecutionBaseEvent, action_params: HTTP_GET):
    """
    Run an http GET against a url
    """
    function_name = "http_get"

    # https://docs.robusta.dev/master/developer-guide/actions/findings-api.html

    finding = Finding(
        title=f"{action_params.url} status check",
        source=FindingSource.MANUAL,
        aggregation_key=function_name,
        finding_type=FindingType.REPORT,
        failure=False,
    )

    try:

        result = requests.get(action_params.url, params=action_params.params)
        if action_params.get_response:
            finding.title = f"Response received from {action_params.url} "
            finding.add_enrichment(
                [
                    FileBlock(f"Response.txt: ", result.text.encode()),
                ]
            )
            event.add_finding(finding)

    except HTTPError as e:
        finding.title = f"{action_params.url} is un-reachable"
        finding.add_enrichment(
            [
                MarkdownBlock(
                    f"*Status Code*\n```\n{e.code}\n```"
                ),
            ]
        )
        event.add_finding(finding)
    except URLError as e:
        finding.title = f"{action_params.url} is un-reachable"
        finding.add_enrichment(
            [
                MarkdownBlock(
                    f"*Reason*\n```\n{e.reason}\n```"
                ),
            ]
        )
        event.add_finding(finding)
    except Exception as e:
        finding.title = f"{action_params.url} is un-reachable"
        finding.add_enrichment(
            [
                MarkdownBlock(
                    f"*Error*\n```\n{e}\n```"
                ),
            ]
        )
        event.add_finding(finding)


class HTTP_POST(ActionParams):
    """
    :var url: In cluster target url.
    :var get_response: (optional) (Default: False) Send results to sink.
    :var data: (optional) Dictionary, list of tuples, bytes, or file-like
        object to send in the body of request.
    """

    url: str
    data: dict = None
    get_response: Optional[bool] = False


@action
def http_post(event: ExecutionBaseEvent, action_params: HTTP_POST):
    """
    Run an http POST against a url
    """
    function_name = "http_post"

    # https://docs.robusta.dev/master/developer-guide/actions/findings-api.html

    finding = Finding(
        title=f"{action_params.url} status check",
        source=FindingSource.MANUAL,
        aggregation_key=function_name,
        finding_type=FindingType.REPORT,
        failure=False,
    )

    try:

        result = requests.post(
            action_params.url, data=action_params.data)

        if action_params.get_response:
            finding.title = f"Response received from {action_params.url} "
            finding.add_enrichment(
                [

                    FileBlock(f"Response.txt: ", result.text.encode()),

                ]
            )
            event.add_finding(finding)

    except HTTPError as e:
        finding.title = f"{action_params.url} is un-reachable"
        finding.add_enrichment(
            [
                MarkdownBlock(
                    f"*Status Code*\n```\n{e.code}\n```"
                ),
            ]
        )
        event.add_finding(finding)
    except URLError as e:
        finding.title = f"{action_params.url} is un-reachable"
        finding.add_enrichment(
            [
                MarkdownBlock(
                    f"*Reason*\n```\n{e.reason}\n```"
                ),
            ]
        )
        event.add_finding(finding)
    except Exception as e:
        finding.title = f"{action_params.url} is un-reachable"
        finding.add_enrichment(
            [
                MarkdownBlock(
                    f"*Error*\n```\n{e}\n```"
                ),
            ]
        )
        event.add_finding(finding)
