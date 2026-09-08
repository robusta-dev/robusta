from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from robusta.api import ActionException


DESCRIBE_RESPONSE = {
    "nodegroup": {
        "nodegroupName": "workers",
        "scalingConfig": {
            "minSize": 1,
            "maxSize": 5,
            "desiredSize": 3,
        },
    }
}

BASE_PARAMS = {
    "cluster_name": "my-cluster",
    "region": "us-west-2",
    "node_group_name": "workers",
    "new_max_size": 10,
}


def _make_client_error(code: str) -> ClientError:
    """Build a ClientError with the given error code."""
    return ClientError(
        {"Error": {"Code": code, "Message": "mocked"}},
        "operation",
    )


@pytest.fixture
def mock_event():
    """Return a MagicMock configured to track enrichments and findings."""
    event = MagicMock()
    event.findings = []
    event.add_enrichment = MagicMock()
    event.add_finding = MagicMock()
    return event


@patch("boto3.client")
def test_scale_up_succeeds(mock_boto_client, mock_event):
    """Verify the EKS API is called with the correct scaling config on a successful scale-up."""
    from robusta_playbooks.aws_node_group_actions import EksNodeGroupParams, eks_scale_node_group

    eks_mock = MagicMock()
    eks_mock.describe_nodegroup.return_value = DESCRIBE_RESPONSE
    mock_boto_client.return_value = eks_mock

    params = EksNodeGroupParams(**BASE_PARAMS)
    eks_scale_node_group(mock_event, params)

    eks_mock.update_nodegroup_config.assert_called_once_with(
        clusterName="my-cluster",
        nodegroupName="workers",
        scalingConfig={"minSize": 1, "maxSize": 10, "desiredSize": 3},
    )
    mock_event.add_finding.assert_called_once()
    finding = mock_event.add_finding.call_args[0][0]
    assert "workers" in finding.title
    assert "maxSize updated" in finding.title


@patch("boto3.client")
def test_no_op_when_new_max_not_larger(mock_boto_client, mock_event):
    """Verify no update is made when the requested max is below the current max."""
    from robusta_playbooks.aws_node_group_actions import EksNodeGroupParams, eks_scale_node_group

    eks_mock = MagicMock()
    eks_mock.describe_nodegroup.return_value = DESCRIBE_RESPONSE
    mock_boto_client.return_value = eks_mock

    params = EksNodeGroupParams(**{**BASE_PARAMS, "new_max_size": 3})
    eks_scale_node_group(mock_event, params)

    eks_mock.update_nodegroup_config.assert_not_called()
    mock_event.add_enrichment.assert_called_once()
    mock_event.add_finding.assert_not_called()
    enrichment_blocks = mock_event.add_enrichment.call_args[0][0]
    assert any("no change" in block.text for block in enrichment_blocks)


@patch("boto3.client")
def test_no_op_when_new_max_is_equal(mock_boto_client, mock_event):
    """Verify no update is made when the requested max matches the current max."""
    from robusta_playbooks.aws_node_group_actions import EksNodeGroupParams, eks_scale_node_group

    eks_mock = MagicMock()
    eks_mock.describe_nodegroup.return_value = DESCRIBE_RESPONSE
    mock_boto_client.return_value = eks_mock

    params = EksNodeGroupParams(**{**BASE_PARAMS, "new_max_size": 5})
    eks_scale_node_group(mock_event, params)

    eks_mock.update_nodegroup_config.assert_not_called()
    mock_event.add_enrichment.assert_called_once()
    mock_event.add_finding.assert_not_called()


@patch("boto3.client")
def test_raises_on_describe_failure(mock_boto_client, mock_event):
    """Verify ActionException is raised and update is skipped when describe fails."""
    from robusta_playbooks.aws_node_group_actions import EksNodeGroupParams, eks_scale_node_group

    eks_mock = MagicMock()
    eks_mock.describe_nodegroup.side_effect = _make_client_error("ResourceNotFoundException")
    mock_boto_client.return_value = eks_mock

    params = EksNodeGroupParams(**BASE_PARAMS)
    with pytest.raises(ActionException) as exc_info:
        eks_scale_node_group(mock_event, params)

    assert isinstance(exc_info.value.__cause__, ClientError)
    eks_mock.update_nodegroup_config.assert_not_called()


@patch("boto3.client")
def test_raises_on_update_failure(mock_boto_client, mock_event):
    """Verify ActionException is raised when the nodegroup update call fails."""
    from robusta_playbooks.aws_node_group_actions import EksNodeGroupParams, eks_scale_node_group

    eks_mock = MagicMock()
    eks_mock.describe_nodegroup.return_value = DESCRIBE_RESPONSE
    eks_mock.update_nodegroup_config.side_effect = _make_client_error("InvalidParameterException")
    mock_boto_client.return_value = eks_mock

    params = EksNodeGroupParams(**BASE_PARAMS)
    with pytest.raises(ActionException) as exc_info:
        eks_scale_node_group(mock_event, params)

    assert isinstance(exc_info.value.__cause__, ClientError)


@patch("boto3.client")
def test_boto_client_uses_explicit_credentials(mock_boto_client, mock_event):
    """Verify explicit AWS credentials are forwarded to boto3.client."""
    from robusta_playbooks.aws_node_group_actions import EksNodeGroupParams, eks_scale_node_group

    eks_mock = MagicMock()
    eks_mock.describe_nodegroup.return_value = DESCRIBE_RESPONSE
    mock_boto_client.return_value = eks_mock

    params = EksNodeGroupParams(
        **{**BASE_PARAMS, "aws_access_key_id": "AKID", "aws_secret_access_key": "SECRET"}
    )
    eks_scale_node_group(mock_event, params)

    mock_boto_client.assert_called_once_with(
        "eks",
        region_name="us-west-2",
        aws_access_key_id="AKID",
        aws_secret_access_key="SECRET",  # noqa: S106
    )
