import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from robusta.api import (
    ActionException,
    ActionParams,
    ErrorCodes,
    ExecutionBaseEvent,
    Finding,
    FindingSeverity,
    FindingSource,
    MarkdownBlock,
    action,
)


class EksNodeGroupParams(ActionParams):
    """
    :var cluster_name: EKS cluster name.
    :var region: AWS region where the cluster is located (e.g. us-east-1).
    :var node_group_name: Name of the EKS managed node group to scale.
    :var new_max_size: New maximum node count. Must exceed the current maxSize.
    :var aws_access_key_id: Optional AWS access key ID. Falls back to instance role or environment.
    :var aws_secret_access_key: Optional AWS secret access key.
    """

    cluster_name: str
    region: str
    node_group_name: str
    new_max_size: int
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None


@action
def eks_scale_node_group(event: ExecutionBaseEvent, params: EksNodeGroupParams):
    """
    Increase the maximum size of an EKS managed node group.

    Use as a remediation action when the cluster autoscaler cannot provision
    new nodes because the node group has reached its configured maxSize.

    Requires IAM permission: eks:DescribeNodegroup and eks:UpdateNodegroupConfig.
    """
    eks = boto3.client(
        "eks",
        region_name=params.region,
        aws_access_key_id=params.aws_access_key_id,
        aws_secret_access_key=params.aws_secret_access_key,
    )

    try:
        ng = eks.describe_nodegroup(
            clusterName=params.cluster_name,
            nodegroupName=params.node_group_name,
        )["nodegroup"]
    except ClientError as e:
        raise ActionException(
            ErrorCodes.ACTION_UNEXPECTED_ERROR,
            f"Failed to describe node group '{params.node_group_name}' "
            f"in cluster '{params.cluster_name}': {e}",
        ) from e

    scaling = ng["scalingConfig"]
    current_min = scaling["minSize"]
    current_max = scaling["maxSize"]
    current_desired = scaling["desiredSize"]

    if params.new_max_size <= current_max:
        event.add_enrichment(
            [
                MarkdownBlock(
                    f"Node group *{params.node_group_name}* already has maxSize={current_max}. "
                    f"Requested new_max_size={params.new_max_size} is not larger — no change made."
                )
            ]
        )
        return

    try:
        eks.update_nodegroup_config(
            clusterName=params.cluster_name,
            nodegroupName=params.node_group_name,
            scalingConfig={
                "minSize": current_min,
                "maxSize": params.new_max_size,
                "desiredSize": current_desired,
            },
        )
    except ClientError as e:
        raise ActionException(
            ErrorCodes.ACTION_UNEXPECTED_ERROR,
            f"Failed to update node group '{params.node_group_name}': {e}",
        ) from e

    logging.info(
        f"eks_scale_node_group: {params.cluster_name}/{params.node_group_name} "
        f"maxSize {current_max} -> {params.new_max_size}"
    )

    finding = Finding(
        title=f"EKS node group *{params.node_group_name}* maxSize updated",
        severity=FindingSeverity.INFO,
        source=FindingSource.MANUAL,
        aggregation_key="EksNodeGroupScaled",
    )
    finding.add_enrichment(
        [
            MarkdownBlock(
                f"*Cluster:* {params.cluster_name}\n"
                f"*Region:* {params.region}\n"
                f"*Node group:* {params.node_group_name}\n"
                f"*maxSize:* {current_max} → {params.new_max_size}\n"
                f"*desiredSize:* {current_desired} | *minSize:* {current_min}"
            )
        ]
    )
    event.add_finding(finding)
