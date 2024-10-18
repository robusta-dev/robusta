
import pytest
from playbooks.robusta_playbooks.util import resolve_selectors

@pytest.mark.parametrize(
    "labels,input_selectors,expected_resolved_selectors",
    [
        ({}, ["my_selector"], ["my_selector"]),
        ({"field1": "value1"}, ["{{ labels.field1 }}"], ["value1"]),
        ({}, ["{{ labels.field_not_found }}"], ["{{ labels.field_not_found }}"]),
        ({"field_1": "field_with_underscore"}, ["{{ labels.field_1 }}"], ["field_with_underscore"]),
        ({"field-1": "field_with_dash"}, ["{{ labels.field-1 }}"], ["field_with_dash"]),
        (
            {"domain": "localhost", "port": "3000", "apiUrl": "/my_api"},
            ["http://{{ labels.domain}}:{{ labels.port }}{{labels.apiUrl}}"],
            ["http://localhost:3000/my_api"]),
        (
            {"domain": "localhost", "port": "3000", "apiUrl": "/my_api"},
            [
                "http://{{ labels.domain}}:{{ labels.port}}{{labels.apiUrl}}",
                "{{ labels.domain}}",
                "{labels.domain}",
                "{apiUrl"
            ],
            [
                "http://localhost:3000/my_api",
                "localhost",
                "{labels.domain}",
                "{apiUrl"
            ]
        )
    ],
)
def test_clean_up_k8s_logs_from_job_output(labels, input_selectors, expected_resolved_selectors):
    assert resolve_selectors(labels, input_selectors) == expected_resolved_selectors
