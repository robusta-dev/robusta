import unittest.mock
from typing import Dict, List, Optional
from unittest.mock import Mock

import pytest
import yaml
from pydantic import ConfigDict, BaseModel

from robusta.core.reporting import Finding, FindingSeverity, FindingSource, FindingSubject
from robusta.core.reporting.consts import FindingSubjectType, FindingType
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.integrations.kubernetes.base_triggers import K8sTriggerEventScopeMatcher
from robusta.utils.scope import ScopeParams


class CheckFindingSubject(BaseModel):
    name: Optional[str] = "pod-xxx-yyy"
    namespace: Optional[str] = "default"
    kind: Optional[str] = "pod"
    node: Optional[str] = None
    model_config = ConfigDict(extra="forbid")


class CheckFinding(BaseModel):
    title: str = "test finding"
    subject: CheckFindingSubject = CheckFindingSubject()
    labels: Dict[str, str] = {}
    annotations: Dict[str, str] = {}
    aggregation_key: str = "OomKill"
    severity: str = "INFO"
    source: str = "NONE"
    finding_type: str = "ISSUE"
    model_config = ConfigDict(extra="forbid")

    def create_finding(self) -> Finding:
        subject = FindingSubject(
            name=self.subject.name,
            namespace=self.subject.namespace,
            subject_type=FindingSubjectType.from_kind(self.subject.kind),
            node=self.subject.node,
            labels=self.labels,
            annotations=self.annotations,
        )
        return Finding(
            title=self.title,
            subject=subject,
            aggregation_key=self.aggregation_key,
            severity=FindingSeverity.from_severity(self.severity),
            source=FindingSource.from_source(self.source),
            finding_type=FindingType.from_type(self.finding_type),
        )


class ScopeCheck(BaseModel):
    finding: CheckFinding
    expected: bool
    message: str
    namespace_labels: Optional[Dict[str, str]] = {}
    model_config = ConfigDict(extra="forbid")


class ScopeTest(BaseModel):
    scope: ScopeParams
    checks: List[ScopeCheck]
    model_config = ConfigDict(extra="forbid")


class _TestConfig(BaseModel):
    tests: List[ScopeTest]


class TestScopeParams:
    def test_scope_params_inc_and_exc_missing(self):
        with pytest.raises(ValueError):
            ScopeParams(include=None, exclude=None)

    @pytest.mark.parametrize(
        "include,exclude",
        [
            (None, []),
            ([], None),
            ([], []),
        ],
    )
    def test_scope_params_empty_inc_exc(self, include, exclude):
        with pytest.raises(ValueError):
            ScopeParams(include=include, exclude=exclude)

    @pytest.mark.parametrize(
        "include_data,exclude_data,expected_include_data,expected_exclude_data",
        [
            (
                None,
                [{"labels": "xyz", "name": ["1", "2"]}],
                None,
                [{"labels": ["xyz"], "name": ["1", "2"]}],
            ),
            (
                [{"name": ".*", "labels": ["1", "2"]}],
                None,
                [{"name": [".*"], "labels": ["1", "2"]}],
                None,
            ),
        ],
    )
    def test_scope_params_normalization(self, include_data, exclude_data, expected_include_data, expected_exclude_data):
        params = ScopeParams(include=include_data, exclude=exclude_data)
        assert params.include == expected_include_data
        assert params.exclude == expected_exclude_data


class _TestSink(SinkBase):
    def write_finding(self, finding: Finding, platform_enabled: bool):
        pass


class _TestSinkParams(SinkBaseParams):
    @classmethod
    def _get_sink_type(cls):
        return "test"


class TestSinkBase:
    @pytest.mark.parametrize("matches_result,expected_result", [(True, True), (False, False)])
    def test_accepts(self, matches_result, expected_result):
        sink_base = _TestSink(sink_params=_TestSinkParams(name="x"), registry=Mock())
        finding = Finding(title="y", aggregation_key="Aaa")
        finding.matches = Mock(return_value=matches_result)
        # sink_base.time_slices is [TimeSliceAlways()] here, so the result will depend
        # solely on matches_result.
        assert sink_base.accepts(finding) is expected_result


class TestFindingScopeMatching:
    @pytest.fixture()
    def get_invalid_attributes(self):
        return Mock(return_value=[])

    @pytest.fixture()
    def finding(self, get_invalid_attributes):
        finding = Finding(title="title", aggregation_key="AgKey")
        with unittest.mock.patch.object(finding, "get_invalid_attributes", get_invalid_attributes):
            yield finding

    @pytest.fixture()
    def finding_with_data(self, finding):
        finding.subject.labels = {"a": "x", "b": "fffy", "X": " hello "}
        finding.subject.namespace = "ns12"
        finding.title = "c1"
        return finding

    def test_matches_no_scope_req(self, finding):
        with unittest.mock.patch.object(
            K8sTriggerEventScopeMatcher, "scope_inc_exc_matches", Mock()
        ) as mock_scope_inc_exc_matches:
            finding.matches({}, None)
        mock_scope_inc_exc_matches.assert_not_called()
        finding.get_invalid_attributes.assert_called_once()

    @pytest.mark.parametrize(
        "include,exclude,expected_output,match_req_evaluated",
        [
            ([{"labels": "a=x,b=.*y"}], None, True, False),
            ([{"labels": "a=q,b=.*y"}], None, False, True),
            ([{"labels": "a=q,b=.*y"}, {"namespace": "ns12"}], None, True, False),
            ([{"labels": "a=q,b=.*y"}, {"title": "c1"}], None, True, False),
            ([{"labels": "a=q,b=.*y"}, {"title": "d[1-9]*"}], None, False, True),
            (None, [{"labels": "a=x,b=.*y"}], False, False),
            (None, [{"labels": "a=q,b=.*y"}, {"namespace": "ns12"}], False, False),
            (None, [{"labels": "a=q,b=.*y"}, {"title": "c[1-9]"}], False, False),
            (None, [{"labels": "a=q,b=.*y"}, {"title": "d[1-9]*"}], True, True),
            ([{"namespace": "ns"}], None, False, True),
            (None, [{"namespace": "ns"}], True, True),
            ([{"labels": " a=x , b=.*y "}], None, True, False),
            ([{"labels": "X=hello"}], None, True, False),
            ([{"labels": "X=.*el.*"}], None, True, False),
            ([{"labels": "X!=aaa"}], None, True, False),
            ([{"labels": " X != aaa "}], None, True, False),
        ],
    )
    def test_matches_inc_match(
        self,
        finding_with_data,
        get_invalid_attributes,
        include,
        exclude,
        expected_output,
        match_req_evaluated,
    ):
        assert finding_with_data.matches({}, ScopeParams(include=include, exclude=exclude)) is expected_output
        # The asserts below check that the result has/has not been computed using scope params only and
        # that match_requirements were not evaluated.
        if match_req_evaluated:
            get_invalid_attributes.assert_called_once()
        else:
            get_invalid_attributes.assert_not_called()

    def test_matches_unknown_attr(self, finding_with_data):
        with unittest.mock.patch("robusta.utils.scope.logging") as mock_logging:
            result = finding_with_data.matches({}, ScopeParams(include=[{"xyzzfoo": "123"}], exclude=None))
        assert result is False
        mock_logging.warning.assert_called_once()

    def test_sink_scopes(self, finding):
        with open("tests/scope_test_config.yaml") as test_config_file:
            test_config = _TestConfig(**yaml.safe_load(test_config_file))

        for scope_test in test_config.tests:
            sink_base = _TestSink(sink_params=_TestSinkParams(name="x", scope=scope_test.scope), registry=Mock())

            for check in scope_test.checks:
                finding = check.finding.create_finding()
                with unittest.mock.patch(
                        "robusta.core.reporting.base.get_namespace_labels",
                        return_value=check.namespace_labels
                ):
                    assert sink_base.accepts(finding) is check.expected, f'check "{check.message}" failed'
