from robusta.api import ActionParams, action, DeploymentEvent, Finding, FindingSource, FindingType, MarkdownBlock
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class ServiceCheck(ActionParams):
    """
    :var url: In cluster target url.
    """

    url: str


@action
def http_check(event: DeploymentEvent, action_params: ServiceCheck):
    """
    Run an http request to check deployments
    """

    dep = event.get_deployment()
    req = Request(action_params.url)

    # https://docs.robusta.dev/master/developer-guide/actions/findings-api.html

    finding = Finding(
        title=f"{action_params.url} status check",
        source=FindingSource.MANUAL,
        aggregation_key="http_check",
        finding_type=FindingType.REPORT,
        failure=False,
    )

    try:
        response = urlopen(req)

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
