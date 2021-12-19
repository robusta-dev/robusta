from pydantic import SecretStr

from robusta.api import *


class ArgoBaseParams(BaseModel):
    argo_url: str
    argo_token: SecretStr
    argo_verify_server_cert: bool = True


class ArgoAppParams(ArgoBaseParams):
    argo_app_name: str
    rate_limit_seconds: int = 1800


@action
def argo_app_sync(event: ExecutionBaseEvent, params: ArgoAppParams):

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
        aggregation_key="argo_app_sync",
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
