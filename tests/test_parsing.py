"""Tests for template placeholder substitution in robusta.utils.parsing."""

import pytest

from robusta.core.reporting import FindingSubject, FindingSubjectType
from robusta.utils.parsing import format_event_templated_string

SUBJECT = FindingSubject(
    name="example-pod-1",
    subject_type=FindingSubjectType.TYPE_POD,
    namespace="default",
    node="node-1",
    labels={"app": "example", "app.kubernetes.io/name": "example"},
    annotations={"com.example/job-count": "5", "team": "backend"},
)


@pytest.mark.parametrize(
    "template,expected_output",
    [
        # basic subject fields, braced and unbraced
        ("$name in $namespace", "example-pod-1 in default"),
        ("${name} on ${node} (${kind})", "example-pod-1 on node-1 (pod)"),
        # unbraced placeholders stop at characters outside the pattern
        ("$name-suffix", "example-pod-1-suffix"),
        # labels and annotations with plain keys
        ("app=${labels.app}", "app=example"),
        ("team=${annotations.team}", "team=backend"),
        # keys containing "/" and "-" work in braced placeholders
        ("count=${annotations.com.example/job-count}", "count=5"),
        ("name=${labels.app.kubernetes.io/name}", "name=example"),
        # unknown variables resolve to <missing>
        ("${labels.missing} / ${annotations.com.example/missing}", "<missing> / <missing>"),
        # escaped dollar signs are preserved
        ("$$name", "$name"),
    ],
)
def test_format_event_templated_string(template: str, expected_output: str):
    """Resolve subject fields, labels and annotations in braced and unbraced placeholders."""
    assert format_event_templated_string(SUBJECT, template) == expected_output
