"""
Utilities for detecting deployment context (CLI vs Helm, Robusta vs Holmes).

This module provides functions to detect how Robusta/Holmes is deployed and
generate appropriate guidance messages for users based on their deployment method.
"""

import os
from enum import Enum
from typing import Optional


class DeploymentMethod(Enum):
    """How the application is deployed."""
    CLI = "cli"
    HELM = "helm"
    UNKNOWN = "unknown"


class ChartType(Enum):
    """Which Helm chart is being used (if deployed via Helm)."""
    ROBUSTA = "robusta"
    HOLMES = "holmes"
    UNKNOWN = "unknown"


class DeploymentContext:
    """Detected deployment context information."""

    def __init__(
        self,
        method: DeploymentMethod,
        chart_type: ChartType,
        release_name: Optional[str] = None,
        namespace: Optional[str] = None,
    ):
        self.method = method
        self.chart_type = chart_type
        self.release_name = release_name
        self.namespace = namespace

    @property
    def is_cli(self) -> bool:
        return self.method == DeploymentMethod.CLI

    @property
    def is_helm(self) -> bool:
        return self.method == DeploymentMethod.HELM

    @property
    def is_robusta_chart(self) -> bool:
        return self.chart_type == ChartType.ROBUSTA

    @property
    def is_holmes_chart(self) -> bool:
        return self.chart_type == ChartType.HOLMES


def detect_deployment_context() -> DeploymentContext:
    """
    Detect the current deployment context based on environment variables.

    Detection logic:
    - CLI: No PLAYBOOKS_CONFIG_FILE_PATH and no INSTALLATION_NAMESPACE set
      (or INSTALLATION_NAMESPACE is the default "robusta" without other indicators)
    - Helm (Robusta): Has PLAYBOOKS_CONFIG_FILE_PATH set to /etc/robusta/... path
    - Helm (Holmes standalone): Has HOLMES_ENABLED but no Robusta-specific paths,
      or explicitly marked via HOLMES_STANDALONE env var

    Returns:
        DeploymentContext with detected method and chart type
    """
    playbooks_config_path = os.environ.get("PLAYBOOKS_CONFIG_FILE_PATH")
    installation_namespace = os.environ.get("INSTALLATION_NAMESPACE")
    release_name = os.environ.get("RELEASE_NAME")
    holmes_enabled = os.environ.get("HOLMES_ENABLED", "false").lower() == "true"
    holmes_standalone = os.environ.get("HOLMES_STANDALONE", "false").lower() == "true"

    # Check for explicit Holmes standalone marker
    if holmes_standalone:
        return DeploymentContext(
            method=DeploymentMethod.HELM,
            chart_type=ChartType.HOLMES,
            release_name=release_name,
            namespace=installation_namespace,
        )

    # Robusta Helm deployment: has playbooks config path pointing to /etc/robusta/
    if playbooks_config_path and playbooks_config_path.startswith("/etc/robusta/"):
        return DeploymentContext(
            method=DeploymentMethod.HELM,
            chart_type=ChartType.ROBUSTA,
            release_name=release_name,
            namespace=installation_namespace,
        )

    # Check if we're in a Kubernetes environment (has namespace set from pod metadata)
    # This would indicate Helm deployment even without the config path
    if installation_namespace and installation_namespace != "robusta":
        # Non-default namespace suggests actual Helm deployment
        chart_type = ChartType.HOLMES if holmes_enabled and not playbooks_config_path else ChartType.ROBUSTA
        return DeploymentContext(
            method=DeploymentMethod.HELM,
            chart_type=chart_type,
            release_name=release_name,
            namespace=installation_namespace,
        )

    # If we have a release name that's not the default, likely Helm
    if release_name and release_name != "robusta":
        chart_type = ChartType.HOLMES if holmes_enabled and not playbooks_config_path else ChartType.ROBUSTA
        return DeploymentContext(
            method=DeploymentMethod.HELM,
            chart_type=chart_type,
            release_name=release_name,
            namespace=installation_namespace,
        )

    # Default to CLI if no Helm indicators found
    return DeploymentContext(
        method=DeploymentMethod.CLI,
        chart_type=ChartType.UNKNOWN,
    )


def get_env_var_guidance(var_name: str, context: Optional[DeploymentContext] = None) -> str:
    """
    Generate guidance for setting an environment variable based on deployment context.

    Args:
        var_name: The name of the environment variable
        context: Optional pre-detected deployment context. If None, will be detected.

    Returns:
        A helpful message with instructions for the detected deployment method.
    """
    if context is None:
        context = detect_deployment_context()

    if context.is_cli:
        return _get_cli_guidance(var_name)
    elif context.is_helm:
        if context.is_robusta_chart:
            return _get_robusta_helm_guidance(var_name)
        elif context.is_holmes_chart:
            return _get_holmes_helm_guidance(var_name)
        else:
            # Generic Helm guidance
            return _get_generic_helm_guidance(var_name)
    else:
        return _get_generic_guidance(var_name)


def _get_cli_guidance(var_name: str) -> str:
    """Guidance for CLI users."""
    return f"""Environment variable '{var_name}' is not set.

To fix this issue, set the environment variable before running the command:

  export {var_name}=<your-value>

Or pass it inline:

  {var_name}=<your-value> robusta <command>"""


def _get_robusta_helm_guidance(var_name: str) -> str:
    """Guidance for Robusta Helm chart users."""
    return f"""Environment variable '{var_name}' is not set.

To fix this issue, add the environment variable to your Robusta Helm values.yaml:

  runner:
    additional_env_vars:
      - name: {var_name}
        value: "<your-value>"

  # Or use a Kubernetes secret:
  runner:
    additional_env_vars:
      - name: {var_name}
        valueFrom:
          secretKeyRef:
            name: <secret-name>
            key: <secret-key>

Then upgrade your Helm release:

  helm upgrade robusta robusta/robusta -f values.yaml

For more information, see: https://docs.robusta.dev/master/configuration/index.html"""


def _get_holmes_helm_guidance(var_name: str) -> str:
    """Guidance for Holmes standalone Helm chart users."""
    return f"""Environment variable '{var_name}' is not set.

To fix this issue, add the environment variable to your Holmes Helm values.yaml:

  additionalEnvVars:
    - name: {var_name}
      value: "<your-value>"

  # Or use a Kubernetes secret:
  additionalEnvVars:
    - name: {var_name}
      valueFrom:
        secretKeyRef:
          name: <secret-name>
          key: <secret-key>

Then upgrade your Helm release:

  helm upgrade holmes robusta/holmes -f values.yaml

For more information, see: https://holmesgpt.dev/getting-started/"""


def _get_generic_helm_guidance(var_name: str) -> str:
    """Generic Helm guidance when chart type is unknown."""
    return f"""Environment variable '{var_name}' is not set.

To fix this issue, add the environment variable to your Helm values.yaml:

  additionalEnvVars:
    - name: {var_name}
      value: "<your-value>"

  # Or use a Kubernetes secret:
  additionalEnvVars:
    - name: {var_name}
      valueFrom:
        secretKeyRef:
          name: <secret-name>
          key: <secret-key>

Then upgrade your Helm release with:

  helm upgrade <release-name> <chart> -f values.yaml"""


def _get_generic_guidance(var_name: str) -> str:
    """Generic guidance when deployment method is unknown."""
    return f"""Environment variable '{var_name}' is not set.

To fix this issue:

  For CLI users:
    export {var_name}=<your-value>

  For Helm chart users (Holmes or Robusta):
    Add the environment variable to your values.yaml:

    additionalEnvVars:
      - name: {var_name}
        value: "<your-value>"

    # Or use a secret:
    additionalEnvVars:
      - name: {var_name}
        valueFrom:
          secretKeyRef:
            name: <secret-name>
            key: <secret-key>"""
