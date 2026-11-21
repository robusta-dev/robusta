"""Scan jobs run their parameters through `sh -c`, so every parameter must reach the shell as data."""
import shlex

import pytest

from playbooks.robusta_playbooks.krr import (
    KRRParams,
    KRRSecret,
    KRRSecretKeyValuePair,
    _generate_additional_env_args,
    _generate_prometheus_secrets,
    get_krr_additional_flags,
)
from robusta.integrations.prometheus.utils import generate_prometheus_config

INJECTION = "x'; echo unquoted; echo '"


def test_prometheus_label_is_one_shell_word_each():
    params = KRRParams(prometheus_additional_labels={INJECTION: INJECTION})
    assert shlex.split(get_krr_additional_flags(params)) == ["--prometheus-label", INJECTION, "-l", INJECTION]


def test_secret_values_are_expanded_by_the_shell_not_pasted_into_the_command():
    secrets = [
        KRRSecret(env_var_name="PROMETHEUS_AUTH_HEADER", secret_key="k", secret_value="v", command_flag="--auth"),
        KRRSecretKeyValuePair(
            env_var_name="PROMETHEUS_HEADER_X", secret_key="k2", secret_value="v", command_flag="--h", arg_key="X"
        ),
    ]
    args = _generate_additional_env_args(secrets)
    # $(VAR) is substituted by Kubernetes before the shell parses the command; ${VAR} is not
    assert "$(" not in args
    assert args == '--auth "${PROMETHEUS_AUTH_HEADER}" --h X:"${PROMETHEUS_HEADER_X}"'


def test_illegal_prometheus_header_name_is_rejected():
    params = KRRParams(prometheus_url="http://prometheus", prometheus_additional_headers={INJECTION: "value"})
    with pytest.raises(ValueError, match="Illegal prometheus header name"):
        _generate_prometheus_secrets(generate_prometheus_config(params))
