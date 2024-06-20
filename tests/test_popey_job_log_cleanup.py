from unittest import mock

import pytest

from playbooks.robusta_playbooks.popeye import clean_up_k8s_logs_from_job_output


@pytest.mark.parametrize(
    "input,expected_output,expected_warnings",
    [
        ("", "", []),
        ("{}", "{}", []),
        ("{}\nextra text", "{}\nextra text", []),
        ('{"popeye": []}', '{"popeye": []}', []),
        ('{"popeye": []}\n{}', '{"popeye": []}\n{}', []),
        ('{"invalid_json": {[{', '{"invalid_json": {[{', []),
        (" \t\n", "", []),
        ('\nlog line 1\n\nweird log\n{"x": 3}', '{"x": 3}', [
            'Unexpected k8s log line "log line 1" in Popeye scan job output',
            'Unexpected k8s log line "weird log" in Popeye scan job output',
        ]),
        (
            "xxx Waited for 3.14159s due to client-side throttling, not priority and fairness, blah\n"
            "\n"
            '{"data": []}',
            '{"data": []}',
            [
                "Popeye scan job delayed by 3.14159s by Kubernetes due to throttling",
            ],
        ),
        (
            "xxx Waited for 21.37s - request: some text here\n"
            "\n"
            '{"x": 123}',
            '{"x": 123}',
            [
                "Popeye scan job delayed by 21.37s by Kubernetes",
            ],
        ),
        (
            "xxx Waited for 666s due to client-side throttling, not priority and fairness, blah\n"
            "\n"
            "aaa Waited for 777s - request: some text here\n"
            "\n"
            "bad logging message\n"
            '{"p": "q"}',
            '{"p": "q"}',
            [
                "Popeye scan job delayed by 666s by Kubernetes due to throttling",
                "Popeye scan job delayed by 777s by Kubernetes",
                'Unexpected k8s log line "bad logging message" in Popeye scan job output'
            ],
        ),
    ],
)
def test_clean_up_k8s_logs_from_job_output(input, expected_output, expected_warnings):
    with mock.patch("playbooks.robusta_playbooks.popeye.logging.warning") as mock_warning:
        assert clean_up_k8s_logs_from_job_output(input) == expected_output
    assert mock_warning.call_args_list == [
        mock.call(warning_msg) for warning_msg in expected_warnings
    ]
