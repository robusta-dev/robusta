from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.reporting.base import Finding, FindingSeverity, FindingSubject
from robusta.core.reporting.consts import FindingSubjectType
from playbooks.robusta_playbooks.common_actions import FindingLabelRule, FindingOverrides, customise_finding


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(subject: FindingSubject) -> ExecutionBaseEvent:
    finding = Finding(
        title="Test Finding",
        aggregation_key="TestKey",
        severity=FindingSeverity.HIGH,
        subject=subject,
    )
    event = ExecutionBaseEvent(named_sinks=["default"])
    event.sink_findings["default"].append(finding)
    event.get_subject = lambda: subject
    return event


def _finding(event: ExecutionBaseEvent) -> Finding:
    return event.sink_findings["default"][0]


def _run(subject: FindingSubject, rules: list) -> Finding:
    event = _make_event(subject)
    params = FindingOverrides(finding_label_rules=[FindingLabelRule(**r) for r in rules])
    customise_finding(event, params)
    return _finding(event)


# ---------------------------------------------------------------------------
# Basic match / no-match
# ---------------------------------------------------------------------------

def test_namespace_match_sets_label():
    subject = FindingSubject(name="pod", namespace="infra-monitoring")
    finding = _run(subject, [
        {"source_fields": ["namespace"], "regex": "infra-.*", "target_label": "team", "replacement": "infra-team"},
    ])
    assert finding.subject.labels["team"] == "infra-team"


def test_namespace_no_match_leaves_label_absent():
    subject = FindingSubject(name="pod", namespace="app-prod")
    finding = _run(subject, [
        {"source_fields": ["namespace"], "regex": "infra-.*", "target_label": "team", "replacement": "infra-team"},
    ])
    assert "team" not in finding.subject.labels


def test_alternation_regex_matches_second_branch():
    subject = FindingSubject(name="pod", namespace="kube-system")
    finding = _run(subject, [
        {"source_fields": ["namespace"], "regex": "infra-.*|kube-system", "target_label": "team", "replacement": "infra-team"},
    ])
    assert finding.subject.labels["team"] == "infra-team"


# ---------------------------------------------------------------------------
# Capture-group replacement
# ---------------------------------------------------------------------------

def test_capture_group_replacement():
    subject = FindingSubject(name="pod", namespace="team-backend")
    finding = _run(subject, [
        {"source_fields": ["namespace"], "regex": "team-(.*)", "target_label": "team", "replacement": "$1"},
    ])
    assert finding.subject.labels["team"] == "backend"


def test_multiple_capture_groups():
    subject = FindingSubject(name="pod", namespace="eu-backend-prod")
    finding = _run(subject, [
        {"source_fields": ["namespace"], "regex": "(\\w+)-(\\w+)-(\\w+)", "target_label": "env", "replacement": "$3-$1"},
    ])
    assert finding.subject.labels["env"] == "prod-eu"


# ---------------------------------------------------------------------------
# Source: name, kind, node
# ---------------------------------------------------------------------------

def test_source_from_name():
    subject = FindingSubject(name="payments-worker", namespace="default")
    finding = _run(subject, [
        {"source_fields": ["name"], "regex": "payments-.*", "target_label": "team", "replacement": "payments"},
    ])
    assert finding.subject.labels["team"] == "payments"


def test_source_from_kind():
    subject = FindingSubject(name="pod", namespace="default", subject_type=FindingSubjectType.TYPE_POD)
    finding = _run(subject, [
        {"source_fields": ["kind"], "regex": "pod", "target_label": "resource_type", "replacement": "pod"},
    ])
    assert finding.subject.labels["resource_type"] == "pod"


# ---------------------------------------------------------------------------
# Source: pod labels, annotations, namespace_labels
# ---------------------------------------------------------------------------

def test_source_from_pod_label():
    subject = FindingSubject(name="pod", namespace="default", labels={"app": "payments"})
    finding = _run(subject, [
        {"source_fields": ["labels.app"], "regex": "payments", "target_label": "team", "replacement": "payments-team"},
    ])
    assert finding.subject.labels["team"] == "payments-team"


def test_source_from_annotation():
    subject = FindingSubject(name="pod", namespace="default", annotations={"owner": "platform"})
    finding = _run(subject, [
        {"source_fields": ["annotations.owner"], "regex": "platform", "target_label": "team", "replacement": "platform-team"},
    ])
    assert finding.subject.labels["team"] == "platform-team"


# ---------------------------------------------------------------------------
# Multiple source_fields (concatenation)
# ---------------------------------------------------------------------------

def test_multiple_source_fields_concatenated():
    subject = FindingSubject(name="pod", namespace="eu", labels={"env": "prod"})
    finding = _run(subject, [
        {"source_fields": ["namespace", "labels.env"], "regex": "eu;prod", "target_label": "region", "replacement": "eu-prod"},
    ])
    assert finding.subject.labels["region"] == "eu-prod"


def test_custom_separator():
    subject = FindingSubject(name="pod", namespace="eu", labels={"env": "prod"})
    finding = _run(subject, [
        {"source_fields": ["namespace", "labels.env"], "separator": "/", "regex": "eu/prod", "target_label": "region", "replacement": "eu-prod"},
    ])
    assert finding.subject.labels["region"] == "eu-prod"


# ---------------------------------------------------------------------------
# Multiple rules (ordering & overwrite)
# ---------------------------------------------------------------------------

def test_multiple_rules_both_match():
    subject = FindingSubject(name="pod", namespace="infra-db")
    finding = _run(subject, [
        {"source_fields": ["namespace"], "regex": "infra-.*", "target_label": "team", "replacement": "infra"},
        {"source_fields": ["namespace"], "regex": "infra-.*", "target_label": "cost_center", "replacement": "cc-infra"},
    ])
    assert finding.subject.labels["team"] == "infra"
    assert finding.subject.labels["cost_center"] == "cc-infra"


def test_later_rule_overwrites_earlier():
    subject = FindingSubject(name="pod", namespace="infra-db")
    finding = _run(subject, [
        {"source_fields": ["namespace"], "regex": "infra-.*", "target_label": "team", "replacement": "first"},
        {"source_fields": ["namespace"], "regex": "infra-db", "target_label": "team", "replacement": "second"},
    ])
    assert finding.subject.labels["team"] == "second"


def test_only_matching_rules_apply():
    subject = FindingSubject(name="pod", namespace="app-prod")
    finding = _run(subject, [
        {"source_fields": ["namespace"], "regex": "infra-.*", "target_label": "team", "replacement": "infra"},
        {"source_fields": ["namespace"], "regex": "app-.*", "target_label": "team", "replacement": "app"},
    ])
    assert finding.subject.labels["team"] == "app"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_no_namespace_does_not_crash():
    subject = FindingSubject(name="pod", namespace=None)
    finding = _run(subject, [
        {"source_fields": ["namespace"], "regex": "infra-.*", "target_label": "team", "replacement": "infra"},
    ])
    assert "team" not in finding.subject.labels


def test_missing_source_label_key_treated_as_empty():
    subject = FindingSubject(name="pod", namespace="default")
    finding = _run(subject, [
        {"source_fields": ["labels.nonexistent"], "regex": "", "target_label": "team", "replacement": "x"},
    ])
    assert finding.subject.labels["team"] == "x"


def test_existing_pod_label_not_overwritten_when_no_match():
    subject = FindingSubject(name="pod", namespace="app-prod", labels={"team": "original"})
    finding = _run(subject, [
        {"source_fields": ["namespace"], "regex": "infra-.*", "target_label": "team", "replacement": "infra"},
    ])
    assert finding.subject.labels["team"] == "original"


def test_no_rules_is_noop():
    subject = FindingSubject(name="pod", namespace="infra-x", labels={"team": "original"})
    event = _make_event(subject)
    customise_finding(event, FindingOverrides())
    assert _finding(event).subject.labels["team"] == "original"
