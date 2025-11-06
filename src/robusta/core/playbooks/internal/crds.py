import json
import logging
import re
import subprocess
from typing import Optional, List

from robusta.core.reporting.consts import SlackAnnotations
from robusta.core.playbooks.common import get_resource_events_table
from robusta.core.model.env_vars import KUBECTL_CMD_TIMEOUT_SEC
from robusta.core.model.base_params import ActionParams
from robusta.core.playbooks.actions_registry import action
from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.reporting.blocks import FileBlock, JsonBlock
from robusta.core.reporting.base import Finding, EnrichmentType
from robusta.utils.error_codes import ActionException, ErrorCodes


def run_kubectl_command(command: List[str]) -> str:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=KUBECTL_CMD_TIMEOUT_SEC
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = f"kubectl command failed with exit code {e.returncode}\n"
        error_msg += f"Command: {' '.join(command)}\n"
        if e.stderr:
            error_msg += f"Error: {e.stderr}"
        else:
            error_msg += f"Error: {e.stdout}"
        logging.error(error_msg)
        raise ActionException(ErrorCodes.ACTION_UNEXPECTED_ERROR, error_msg)
    except Exception as e:
        logging.exception(f"Unexpected error running kubectl command {command}")
        raise e


class ResourceParams(ActionParams):
    kind: str
    name: str
    namespace: Optional[str] = None

@action
def kubectl_describe(event: ExecutionBaseEvent, params: ResourceParams):
    """
    Fetch resource description using kubectl describe.
    Output format is a FileBlock containing the describe output.
    """
    finding = Finding(
        title=f"kubectl describe {params.kind}/{params.name}",
        aggregation_key="kubectl_describe",
    )

    try:
        cmd = ["kubectl", "describe", params.kind, params.name]
        if params.namespace:
            cmd.extend(["-n", params.namespace])

        output = run_kubectl_command(cmd)

        filename = f"{params.kind}_{params.name}_describe.txt"
        if params.namespace:
            filename = f"{params.namespace}_{filename}"

        file_block = FileBlock(
            filename=filename,
            contents=output.encode()
        )

        finding.add_enrichment([file_block])
        event.add_finding(finding)

    except Exception as e:
        msg = f"Error running kubectl_describe for {params}"
        logging.exception(msg)
        raise ActionException(ErrorCodes.ACTION_UNEXPECTED_ERROR, msg) from e

@action
def fetch_resource_yaml(event: ExecutionBaseEvent, params: ResourceParams):
    """
    Fetch resource YAML using kubectl get -o yaml.
    Output format is a FileBlock containing the YAML.
    """
    finding = Finding(
        title=f"YAML for {params.kind}/{params.name}",
        aggregation_key="fetch_resource_yaml",
    )

    try:
        cmd = ["kubectl", "get", params.kind, params.name, "-o", "yaml"]
        if params.namespace:
            cmd.extend(["-n", params.namespace])

        output = run_kubectl_command(cmd)

        filename = f"{params.kind}_{params.name}.yaml"
        if params.namespace:
            filename = f"{params.namespace}_{filename}"

        file_block = FileBlock(
            filename=filename,
            contents=output.encode()
        )

        finding.add_enrichment([file_block])
        event.add_finding(finding)

    except Exception as e:
        msg = f"Error running fetch_resource_yaml for {params}"
        logging.exception(msg)
        raise ActionException(ErrorCodes.ACTION_UNEXPECTED_ERROR, msg) from e



@action
def fetch_resource_events(event: ExecutionBaseEvent, params: ResourceParams):
    """
    Fetch events for a specific resource using kubectl.
    Output format is a TableBlock with event information.
    """
    finding = Finding(
        title=f"Events for {params.kind}/{params.name}",
        aggregation_key="fetch_resource_events",
    )

    try:
        events_table = get_resource_events_table(
            "Resource Events",
            params.kind,
            params.name,
            params.namespace,
        )
        if events_table:
            finding.add_enrichment(
                [events_table],
                {SlackAnnotations.ATTACHMENT: True},
                enrichment_type=EnrichmentType.k8s_events,
                title="Resource Events",
            )


        event.add_finding(finding)

    except Exception as e:
        msg = f"Error running fetch_resource_events for {params}"
        logging.exception(msg)
        raise ActionException(ErrorCodes.ACTION_UNEXPECTED_ERROR, msg) from e


@action
def fetch_crds(event: ExecutionBaseEvent):
    """
    Fetch all custom resource definitions.
    Returns a JsonBlock with apiVersion, kind, scope, createdAt, and additionalPrinterColumns for each CRD.
    """
    finding = Finding(
        title="Custom Resource Definitions",
        aggregation_key="fetch_crds",
    )

    try:
        cmd = ["kubectl", "get", "crds", "-o", "json"]
        output = run_kubectl_command(cmd)

        crds_data = json.loads(output)
        items = crds_data.get("items", [])

        crd_list = []
        for item in items:
            metadata = item.get("metadata", {})
            spec = item.get("spec", {})
            versions = spec.get("versions", [])

            served_version = None
            for version in versions:
                if version.get("storage", False):
                    served_version = version
                    break
            if not served_version and versions:
                served_version = versions[0]

            additional_columns = []
            if served_version and "additionalPrinterColumns" in served_version:
                additional_columns = [
                    {
                        "name": col.get("name", ""),
                        "type": col.get("type", ""),
                        "jsonPath": col.get("jsonPath", "")
                    }
                    for col in served_version.get("additionalPrinterColumns", [])
                ]

            crd_info = {
                "apiVersion": spec.get("group", "") + "/" + (served_version.get("name", "") if served_version else ""),
                "kind": spec.get("names", {}).get("kind", ""),
                "plural": spec.get("names", {}).get("plural", ""),
                "scope": spec.get("scope", ""),
                "createdAt": metadata.get("creationTimestamp", ""),
                "additionalPrinterColumns": additional_columns
            }
            crd_list.append(crd_info)

        crd_list.sort(key=lambda x: x.get("kind", ""))

        json_block = JsonBlock(
            json_str=json.dumps(crd_list, indent=2)
        )

        finding.add_enrichment([json_block])
        event.add_finding(finding)

    except Exception as e:
        msg = "Error running fetch_crds"
        logging.exception(msg)
        raise ActionException(ErrorCodes.ACTION_UNEXPECTED_ERROR, msg) from e


class CRInstancesParams(ActionParams):
    kind: str
    namespace: Optional[str] = None
    fields: Optional[List[str]] = None  # List of fields to return from each instance

@action
def fetch_cr_instances(event: ExecutionBaseEvent, params: CRInstancesParams):
    """
    Fetch all instances of a custom resource type.
    Returns a JsonBlock with name, namespace, and selected fields for each instance.
    """
    finding = Finding(
        title=f"Instances of {params.kind}",
        aggregation_key="fetch_cr_instances",
    )

    try:
        cmd = ["kubectl", "get", params.kind, "-o", "json"]
        if params.namespace:
            cmd.extend(["-n", params.namespace])
        else:
            cmd.append("--all-namespaces")

        output = run_kubectl_command(cmd)

        instances_data = json.loads(output)
        items = instances_data.get("items", [])

        instance_list = []
        for item in items:
            metadata = item.get("metadata", {})
            instance_info = {
                "name": metadata.get("name", ""),
                "namespace": metadata.get("namespace", "")
            }

            if params.fields:
                for field in params.fields:
                    # Support nested field paths using dot notation. Remove leading dot if present (JSONPath style)
                    clean_field = field.lstrip('.')

                    # Check if this is a JSONPath filter pattern like "status.conditions[?(@.type == 'Reconciled')].status"
                    # or "spec.containers[?(@.name == 'main')].image"
                    # Pattern: (path).(array)[?(@.field == 'value')](.afterField)
                    filter_pattern = r"^((?:.*?\.)?)([^.\[]+)\[\?\(@\.(\w+)\s*==\s*['\"]([^'\"]+)['\"]\)\](?:\.(.+))?$"
                    match = re.match(filter_pattern, clean_field)

                    if match:
                        path_to_array = match.group(1).rstrip('.')  # e.g., "status" or "" (empty for root-level)
                        array_name = match.group(2)                  # e.g., "conditions", "containers", "volumes"
                        filter_field = match.group(3)                # e.g., "type", "name", "id"
                        filter_value = match.group(4)                # e.g., "Reconciled", "main", "data"
                        field_after = match.group(5)                 # e.g., "status", "image", None

                        try:
                            value = item
                            if path_to_array:
                                for part in path_to_array.split("."):
                                    if isinstance(value, dict):
                                        value = value.get(part, None)
                                    else:
                                        value = None
                                        break

                            if value and isinstance(value, dict):
                                array_items = value.get(array_name, [])
                            else:
                                array_items = None

                            if array_items and isinstance(array_items, list):
                                for array_item in array_items:
                                    if isinstance(array_item, dict) and array_item.get(filter_field) == filter_value:
                                        if field_after:
                                            value = array_item.get(field_after)
                                        else:
                                            value = array_item
                                        break
                                else:
                                    value = None
                            else:
                                value = None

                            instance_info[field] = value
                        except (KeyError, TypeError, AttributeError):
                            instance_info[field] = None
                    else:
                        # Regular dot notation path
                        field_parts = clean_field.split(".")
                        value = item

                        try:
                            for part in field_parts:
                                if isinstance(value, dict):
                                    value = value.get(part, None)
                                else:
                                    value = None
                                    break
                            instance_info[field] = value
                        except (KeyError, TypeError):
                            instance_info[field] = None

            instance_list.append(instance_info)

        json_block = JsonBlock(
            json_str=json.dumps(instance_list, indent=2, default=str)
        )

        finding.add_enrichment([json_block])
        event.add_finding(finding)

    except Exception as e:
        msg = f"Error running fetch_cr_instances for {params}"
        logging.exception(msg)
        raise ActionException(ErrorCodes.ACTION_UNEXPECTED_ERROR, msg) from e