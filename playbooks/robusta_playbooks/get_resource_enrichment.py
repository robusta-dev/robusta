import hikaru.model
import kubernetes.client.exceptions
from robusta.api import *


class GetKubernetesResourcesParams(ActionParams):
    """
    :var name: Name of the Kubernetes resource we want to export.
    :var namespace: Namespace of the Kubernetes resource we want to export.
    :var kind: Kind of the Kubernetes resource we want to export.
    """

    name: str
    namespace: str = "default"
    kind: str

    def __str__(self):
        return f"name={self.name} namespace={self.namespace} kind={self.kind}"


@action
def get_k8s_resource(event: ExecutionBaseEvent, action_params: GetKubernetesResourcesParams):
    """
    Export Kubernetes resources from the cluster as the yaml file.
    Expects the kind of resource, its name and namespace. If namespace
    is not provided, the "default" would be takes as default namespace.
    """
    resource_kind = action_params.kind.strip()
    try:
        loaded_resource = ResourceLoader.read_resource(
            kind=resource_kind,
            namespace=action_params.namespace,
            name=action_params.name
        ).obj
        resource_yaml = hikaru.get_yaml(loaded_resource)

        event.add_enrichment(
            [
                MarkdownBlock(f"Your YAML file for {resource_kind} {action_params.namespace}/{action_params.name}"),
                FileBlock(f"{action_params.name}.yaml", resource_yaml.encode())
            ],
        )
    except KeyError:
        logging.error(f"{resource_kind} is not supported resource kind")
    except kubernetes.client.exceptions.ApiException as exc:
        if exc.status == 404:
            logging.error(f"{resource_kind.title()} {action_params.namespace}/{action_params.name} was not found")
        else:
            logging.error(f"A following error occurred: {str(exc)}")
    except Exception as exc:
        if "resource loader not found" in str(exc):
            logging.error(f"{resource_kind} is not supported resource kind")
        else:
            logging.exception(exc)
