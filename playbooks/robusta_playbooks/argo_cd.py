from pydantic import SecretStr

from robusta.api import (
    ActionParams,
    ArgoCDClient,
    ExecutionBaseEvent,
    Finding,
    FindingType,
    MarkdownBlock,
    RateLimiter,
    action,
)


class ArgoBaseParams(ActionParams):
    """
    :var argo_url: http(s) Argo CD server url.
    :var argo_token: Argo CD authentication token.
    :var argo_verify_server_cert: verify Argo CD server certificate. Defaults to True.

    :example argo_url: https://my-argo-cd.com
    """

    argo_url: str
    argo_token: SecretStr
    argo_verify_server_cert: bool = True


class ArgoAppParams(ArgoBaseParams):
    """
    :var argo_app_name: Argo CD application that needs syncing.
    :var rate_limit_seconds: this playbook is rate limited. Defaults to 1800 seconds.
    """

    argo_app_name: str
    rate_limit_seconds: int = 1800


@action
def argo_app_sync(event: ExecutionBaseEvent, params: ArgoAppParams):
    """
    Sync a specified Argo CD application.
    Send a finding notifying the sync was performed
    """

    if not RateLimiter.mark_and_test(
        "argo_app_sync",
        params.argo_url + params.argo_app_name,
        params.rate_limit_seconds,
    ):
        return

    argo_client = ArgoCDClient(
        params.argo_url,
        params.argo_token.get_secret_value(),
        params.argo_verify_server_cert,
    )
    success = argo_client.sync_application(params.argo_app_name)

    finding = Finding(
        title="Argo CD application sync",
        aggregation_key="ArgoAppSync",
        finding_type=FindingType.REPORT,
        failure=False,
    )
    finding.add_enrichment(
        [
            MarkdownBlock(
                f"Argo CD app sync for application: *{params.argo_app_name}* ended with *{'success' if success else 'failure'}*"
            )
        ]
    )
    event.add_finding(finding)
