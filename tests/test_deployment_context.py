"""Tests for deployment context detection utility."""

import os
from unittest import mock

import pytest

from robusta.core.model.deployment_context import (
    ChartType,
    DeploymentContext,
    DeploymentMethod,
    detect_deployment_context,
    get_env_var_guidance,
)


class TestDeploymentContext:
    """Tests for the DeploymentContext class."""

    def test_cli_context_properties(self):
        context = DeploymentContext(
            method=DeploymentMethod.CLI,
            chart_type=ChartType.UNKNOWN,
        )
        assert context.is_cli is True
        assert context.is_helm is False
        assert context.is_robusta_chart is False
        assert context.is_holmes_chart is False

    def test_helm_robusta_context_properties(self):
        context = DeploymentContext(
            method=DeploymentMethod.HELM,
            chart_type=ChartType.ROBUSTA,
            release_name="my-robusta",
            namespace="monitoring",
        )
        assert context.is_cli is False
        assert context.is_helm is True
        assert context.is_robusta_chart is True
        assert context.is_holmes_chart is False
        assert context.release_name == "my-robusta"
        assert context.namespace == "monitoring"

    def test_helm_holmes_context_properties(self):
        context = DeploymentContext(
            method=DeploymentMethod.HELM,
            chart_type=ChartType.HOLMES,
            release_name="holmes",
            namespace="default",
        )
        assert context.is_cli is False
        assert context.is_helm is True
        assert context.is_robusta_chart is False
        assert context.is_holmes_chart is True


class TestDetectDeploymentContext:
    """Tests for detect_deployment_context function."""

    def test_detects_cli_with_no_env_vars(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            context = detect_deployment_context()
            assert context.method == DeploymentMethod.CLI
            assert context.chart_type == ChartType.UNKNOWN

    def test_detects_cli_with_default_values(self):
        env = {
            "INSTALLATION_NAMESPACE": "robusta",
            "RELEASE_NAME": "robusta",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            context = detect_deployment_context()
            assert context.method == DeploymentMethod.CLI

    def test_detects_robusta_helm_with_playbooks_config(self):
        env = {
            "PLAYBOOKS_CONFIG_FILE_PATH": "/etc/robusta/config/active_playbooks.yaml",
            "INSTALLATION_NAMESPACE": "monitoring",
            "RELEASE_NAME": "my-robusta",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            context = detect_deployment_context()
            assert context.method == DeploymentMethod.HELM
            assert context.chart_type == ChartType.ROBUSTA
            assert context.release_name == "my-robusta"
            assert context.namespace == "monitoring"

    def test_detects_helm_with_non_default_namespace(self):
        env = {
            "INSTALLATION_NAMESPACE": "custom-namespace",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            context = detect_deployment_context()
            assert context.method == DeploymentMethod.HELM

    def test_detects_helm_with_non_default_release_name(self):
        env = {
            "RELEASE_NAME": "custom-release",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            context = detect_deployment_context()
            assert context.method == DeploymentMethod.HELM

    def test_detects_holmes_standalone_with_explicit_marker(self):
        env = {
            "HOLMES_STANDALONE": "true",
            "INSTALLATION_NAMESPACE": "holmes",
            "RELEASE_NAME": "holmes",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            context = detect_deployment_context()
            assert context.method == DeploymentMethod.HELM
            assert context.chart_type == ChartType.HOLMES

    def test_detects_holmes_with_enabled_flag_no_playbooks(self):
        env = {
            "HOLMES_ENABLED": "true",
            "INSTALLATION_NAMESPACE": "custom-ns",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            context = detect_deployment_context()
            assert context.method == DeploymentMethod.HELM
            assert context.chart_type == ChartType.HOLMES


class TestGetEnvVarGuidance:
    """Tests for get_env_var_guidance function."""

    def test_cli_guidance(self):
        context = DeploymentContext(
            method=DeploymentMethod.CLI,
            chart_type=ChartType.UNKNOWN,
        )
        guidance = get_env_var_guidance("MY_VAR", context)
        assert "export MY_VAR=" in guidance
        assert "MY_VAR=<your-value> robusta" in guidance
        assert "Helm" not in guidance

    def test_robusta_helm_guidance(self):
        context = DeploymentContext(
            method=DeploymentMethod.HELM,
            chart_type=ChartType.ROBUSTA,
        )
        guidance = get_env_var_guidance("MY_VAR", context)
        assert "runner:" in guidance
        assert "additional_env_vars:" in guidance
        assert "helm upgrade robusta robusta/robusta" in guidance
        assert "docs.robusta.dev" in guidance

    def test_holmes_helm_guidance(self):
        context = DeploymentContext(
            method=DeploymentMethod.HELM,
            chart_type=ChartType.HOLMES,
        )
        guidance = get_env_var_guidance("MY_VAR", context)
        assert "additionalEnvVars:" in guidance
        assert "helm upgrade holmes robusta/holmes" in guidance
        assert "holmesgpt.dev" in guidance

    def test_guidance_with_auto_detection(self):
        # When no context is provided, it should auto-detect
        with mock.patch.dict(os.environ, {}, clear=True):
            guidance = get_env_var_guidance("TEST_VAR")
            assert "TEST_VAR" in guidance
            # Should be CLI guidance since no env vars set
            assert "export TEST_VAR=" in guidance

    def test_generic_helm_guidance_unknown_chart(self):
        context = DeploymentContext(
            method=DeploymentMethod.HELM,
            chart_type=ChartType.UNKNOWN,
        )
        guidance = get_env_var_guidance("MY_VAR", context)
        assert "additionalEnvVars:" in guidance
        assert "<release-name>" in guidance
