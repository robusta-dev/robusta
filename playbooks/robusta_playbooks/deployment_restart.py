from robusta.api import *
import datetime
import logging


class DeploymentParams(RateLimitParams):
    name: str
    namespace: str


@action
def deployment_restart(alert: PrometheusKubernetesAlert, params: DeploymentParams):
    if not RateLimiter.mark_and_test(
            "deployment_restart", params.name + params.namespace, params.rate_limit
    ):
        return
    now = datetime.datetime.utcnow()
    now = str(now.isoformat("T") + "Z")
    my_deployment: RobustaDeployment = RobustaDeployment.readNamespacedDeployment(params.name, params.namespace).obj

    if not my_deployment:
        logging.error(
            f"cannot run deployment_restart on alert with no deployment: {alert}"
        )
        return
    my_deployment.spec.template.metadata.annotations['kubectl.kubernetes.io/restartedAt'] = now
    my_deployment.update()