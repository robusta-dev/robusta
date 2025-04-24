from unittest.mock import MagicMock

import pytest

from robusta.core.reporting import FindingSubject
from robusta.core.reporting.base import Enrichment, Finding, FindingSeverity
from robusta.core.reporting.blocks import HeaderBlock, MarkdownBlock
from robusta.core.sinks.opsgenie.opsgenie_sink import OpsGenieSink
from robusta.core.sinks.opsgenie.opsgenie_sink_params import OpsGenieSinkConfigWrapper, OpsGenieSinkParams
from robusta.core.sinks.sink_base import SinkBase


def create_finding(labels=None, annotations=None):
    """Helper function to create a finding with customizable labels and annotations."""
    return Finding(
        title="Test Finding",
        description="Test Description",
        severity=FindingSeverity.HIGH,
        aggregation_key="test",
        subject=FindingSubject(
            name="test-pod",
            namespace="test-namespace",
            node="test-node",
            labels=labels or {},
            annotations=annotations or {},
        ),
    )


def create_sink(teams=None, default_team=None, tags=None):
    """Helper function to create an OpsGenie sink with customizable parameters."""
    config = OpsGenieSinkParams(
        name="sink",
        api_key="test-key",
        teams=teams or [],
        default_team=default_team,
        tags=tags or [],
    )
    return OpsGenieSink(
        OpsGenieSinkConfigWrapper(opsgenie_sink=config),
        MagicMock(),
    )


def test_get_teams_with_labels():
    sink = create_sink(teams=["$labels.team", "$annotations.owner"], default_team="default-team")
    finding = create_finding(labels={"team": "backend-team", "environment": "prod"}, annotations={"owner": "ops-team"})
    teams = sink._OpsGenieSink__get_teams(finding)
    assert set(teams) == {"backend-team", "ops-team"}


def test_get_teams_without_labels():
    sink = create_sink(teams=["$labels.team", "$annotations.owner"], default_team="default-team")
    finding = create_finding()
    teams = sink._OpsGenieSink__get_teams(finding)
    assert teams == ["default-team"]


def test_get_teams_with_missing_label():
    sink = create_sink(teams=["$labels.team", "$annotations.owner"], default_team="default-team")
    finding = create_finding(labels={"environment": "prod"}, annotations={"owner": "ops-team"})  # missing team label
    teams = sink._OpsGenieSink__get_teams(finding)
    assert teams == ["default-team", "ops-team"]


def test_get_teams_with_missing_annotation():
    sink = create_sink(teams=["$labels.team", "$annotations.owner"], default_team="default-team")
    finding = create_finding(
        labels={"team": "backend-team", "environment": "prod"}, annotations={}  # missing owner annotation
    )
    teams = sink._OpsGenieSink__get_teams(finding)
    assert teams == ["backend-team", "default-team"]


def test_get_teams_no_default_team():
    sink = create_sink(teams=["$labels.team", "$annotations.owner"])
    finding = create_finding()
    teams = sink._OpsGenieSink__get_teams(finding)
    assert teams == []


def test_get_teams_static_teams():
    sink = create_sink(teams=["static-team-1", "static-team-2"])
    finding = create_finding(labels={"team": "backend-team", "environment": "prod"}, annotations={"owner": "ops-team"})
    teams = sink._OpsGenieSink__get_teams(finding)
    assert set(teams) == {"static-team-1", "static-team-2"}


def test_get_teams_duplicate_teams():
    sink = create_sink(teams=["$labels.team", "$annotations.owner"], default_team="default-team")
    finding = create_finding(labels={"team": "backend-team", "environment": "prod"}, annotations={"owner": "ops-team"})
    teams = sink._OpsGenieSink__get_teams(finding)
    assert len(teams) == len(set(teams))


class TestOpsGenieSink:
    def test___enrichments_as_text(self):
        enrichments = [
            Enrichment(blocks=[HeaderBlock("header"), MarkdownBlock("a")]),
            Enrichment(blocks=[MarkdownBlock("*b*")]),
        ]
        assert (
            OpsGenieSink._OpsGenieSink__enrichments_as_text(enrichments)
            == "<strong>header</strong>\n<p>a</p>\n---\n<p><b>b</b></p>\n"
        )

    def test_static_team_routing(self):
        """Test that static team names are used directly without template processing"""
        sink = create_sink(teams=["static-team"])
        finding = create_finding()
        teams = sink._OpsGenieSink__get_teams(finding)
        assert teams == ["static-team"]

    def test_dynamic_team_routing(self):
        """Test that dynamic team routing works with labels"""
        sink = create_sink(teams=["$labels.team"])
        finding = create_finding(labels={"team": "backend-team"})
        teams = sink._OpsGenieSink__get_teams(finding)
        assert teams == ["backend-team"]

    def test_mixed_team_routing(self):
        """Test that both static and dynamic teams work together"""
        sink = create_sink(teams=["static-team", "$labels.team"])
        finding = create_finding(labels={"team": "backend-team"})
        teams = sink._OpsGenieSink__get_teams(finding)
        assert set(teams) == {"static-team", "backend-team"}

    def test_default_team_fallback(self):
        """Test that default team is used when template fails to resolve"""
        sink = create_sink(teams=["$labels.team"], default_team="fallback-team")
        finding = create_finding()
        teams = sink._OpsGenieSink__get_teams(finding)
        assert teams == ["fallback-team"]

    def test_annotation_based_routing(self):
        """Test that annotations can be used for team routing"""
        sink = create_sink(teams=["$annotations.owner"])
        finding = create_finding(annotations={"owner": "team-a"})
        teams = sink._OpsGenieSink__get_teams(finding)
        assert teams == ["team-a"]

    def test_no_teams_without_default(self):
        """Test that no teams are returned when template fails and no default team"""
        sink = create_sink(teams=["$labels.team"])
        finding = create_finding()
        teams = sink._OpsGenieSink__get_teams(finding)
        assert teams == []

    def test_duplicate_teams(self):
        """Test that duplicate team names are handled correctly"""
        sink = create_sink(teams=["$labels.team", "$labels.team"])
        finding = create_finding(labels={"team": "backend-team"})
        teams = sink._OpsGenieSink__get_teams(finding)
        assert teams == ["backend-team"]  # Duplicates should be removed
