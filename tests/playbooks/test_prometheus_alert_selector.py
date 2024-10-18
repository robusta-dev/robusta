
import pytest
from playbooks.robusta_playbooks.util import resolve_selectors

@pytest.mark.parametrize(
    "labels,input_selectors,expected_resolved_selectors",
    [
        ({}, ["my_selector"], ["my_selector"]),
        ({"field1": "nominal"}, ["{{ labels.field1 }}"], ["nominal"]),
        ({"field1": "no_leading_space"}, ["{{labels.field1 }}"], ["no_leading_space"]),
        ({"field1": "no_trailing_space"}, ["{{ labels.field1}}"], ["no_trailing_space"]),
        ({"field1": "no_space"}, ["{{labels.field1}}"], ["no_space"]),
        ({"field1": "many_spaces"}, ["{{    labels.field1    }}"], ["many_spaces"]),
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
        #         "{{ labels.domain}}",
        #         "{labels.domain}",
        #         "{{apiUrl}}"
            ],
            [
                "http://localhost:3000/my_api",
        #         "localhost",
        #         "{labels.domain}",
        #         "{{apiUrl}}"
            ]
        )
    ],
)
def test_clean_up_k8s_logs_from_job_output(labels, input_selectors, expected_resolved_selectors):
    actual = resolve_selectors(labels, input_selectors)
    assert actual == expected_resolved_selectors, f"received selectors {str(actual)} but expected {str(expected_resolved_selectors)}"
