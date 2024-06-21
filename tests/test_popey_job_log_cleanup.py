from unittest import mock

import pytest

from playbooks.robusta_playbooks.popeye import clean_up_k8s_logs_from_job_output


@pytest.mark.parametrize(
    "input,expected_output",
    [
        ("", ""),
        ("{}", "{}"),
        ("{}\nextra text", "{}\nextra text"),
        ('{"popeye": []}', '{"popeye": []}'),
        ('{"popeye": []}\n{}', '{"popeye": []}\n{}'),
        ('{"invalid_json": {[{', '{"invalid_json": {[{'),
        (" \t\n", ""),
        ('\nlog line 1\n\nweird log\n{"x": 3}', '{"x": 3}'),
        (
            "xxx Waited for 3.14159s due to client-side throttling, not priority and fairness, blah\n"
            "\n"
            '{"data": []}',
            '{"data": []}',
        ),
        (
            "xxx Waited for 21.37s - request: some text here\n" "\n" '{"x": 123}',
            '{"x": 123}',
        ),
        (
            "xxx Waited for 666s due to client-side throttling, not priority and fairness, blah\n"
            "\n"
            "aaa Waited for 777s - request: some text here\n"
            "\n"
            "bad logging message\n"
            '{"p": "q"}',
            '{"p": "q"}',
        ),
    ],
)
def test_clean_up_k8s_logs_from_job_output(input, expected_output):
    assert clean_up_k8s_logs_from_job_output(input) == expected_output
