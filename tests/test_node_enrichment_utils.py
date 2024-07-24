from unittest.mock import patch

import pytest
from hikaru.model.rel_1_26 import Node, NodeCondition, NodeStatus, ObjectMeta, PodCondition, PodList, PodStatus

from robusta.core.playbooks.node_enrichment_utils import (
    get_node_allocatable_resources_table_block,
    get_node_running_pods_table_block_or_none,
    get_node_status_table_block,
)
from robusta.core.reporting import TableBlock
from robusta.integrations.kubernetes.custom_models import RobustaPod


@pytest.fixture
def create_test_node():
    def _create_test_node(allocatable=None, conditions=None):
        # this way of Node object initialization is taken from hikaru repo
        # https://github.com/haxsaw/hikaru/blob/bb89e0ddc2de241c2d04da9f720b01ce46473fb1/tests/basic_tests_rel_1_26.py#L1634
        status = NodeStatus(allocatable=allocatable, conditions=conditions)
        return Node(status=status)

    return _create_test_node


@pytest.fixture
def create_test_pod():
    def _create_test_pod(name, namespace, conditions):
        return RobustaPod(
            metadata=ObjectMeta(name=name, namespace=namespace),
            status=PodStatus(
                conditions=[
                    PodCondition(status=condition["status"], type=condition["type"]) for condition in conditions
                ]
            ),
        )

    return _create_test_pod


def test_get_node_allocatable_resources_table_block(create_test_node):
    test_node = create_test_node(allocatable={"cpu": "4", "memory": "8Gi"})

    table_block = get_node_allocatable_resources_table_block(test_node)

    assert isinstance(table_block, TableBlock)
    assert table_block.headers == ["resource", "value"]
    assert (
        table_block.table_name
        == "Node Allocatable Resources - The amount of compute resources that are available for pods"
    )
    assert table_block.rows == [["cpu", "4"], ["memory", "8Gi"]]


def test_get_node_status_table_block(create_test_node):
    first_node_condition = NodeCondition(type="Ready", status="True")
    second_node_condition = NodeCondition(type="DiskPressure", status="False")
    test_node = create_test_node(conditions=[first_node_condition, second_node_condition])

    table_block = get_node_status_table_block(test_node)

    assert isinstance(table_block, TableBlock)
    assert table_block.headers == ["Type", "Status"]
    assert table_block.table_name == "*Node status details:*"
    assert table_block.rows == [
        [first_node_condition.type, first_node_condition.status],
        [second_node_condition.type, second_node_condition.status],
    ]


def test_get_node_running_pods_table_block_or_none(create_test_node, create_test_pod):
    test_node = Node(metadata=ObjectMeta(name="test-node"))
    pods = [
        create_test_pod("pod1", "default", [{"status": "True", "type": "Ready"}]),
        create_test_pod("pod2", "default", [{"status": "False", "type": "PodScheduled"}]),
        create_test_pod("pod3", "default", [{"status": "Unknown", "type": "ContainersReady"}]),
    ]
    pod_list = PodList(pods)

    with patch("robusta.core.playbooks.node_enrichment_utils.PodList.listPodForAllNamespaces") as patched_list_pods:
        patched_list_pods.return_value.obj = pod_list

        table_block = get_node_running_pods_table_block_or_none(test_node)

        assert isinstance(table_block, TableBlock)
        assert table_block.headers == ["namespace", "name", "ready"]
        assert table_block.table_name == "Pods running on the node"
        assert table_block.rows == [
            ["default", "pod1", "True"],
            ["default", "pod2", "Unknown"],
            ["default", "pod3", "Unknown"],
        ]


def test_get_node_running_pods_table_block_or_none_failure():
    test_node = Node(metadata=ObjectMeta(name="test-node"))
    with patch(
        "robusta.core.playbooks.node_enrichment_utils.PodList.listPodForAllNamespaces",
        side_effect=Exception("API call failed"),
    ):

        table_block = get_node_running_pods_table_block_or_none(test_node)
        assert table_block is None
