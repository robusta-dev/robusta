import os
import sys
import logging
from datetime import datetime

# Add the src directory to the Python path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from robusta.integrations.slack.sender import SlackSender
from robusta.core.reporting.base import Finding, FindingSource, FindingSeverity, FindingStatus, FindingSubject, Link, \
    EnrichmentType
from robusta.core.reporting.consts import FindingSubjectType, FindingType
from robusta.core.reporting.base import LinkType
from robusta.core.reporting.blocks import (
    MarkdownBlock,
    HeaderBlock,
    DividerBlock,
    TableBlock,
    ListBlock,
    LinkProp,
    LinksBlock,
    CallbackBlock,
    CallbackChoice,
    FileBlock
)
from robusta.core.model.base_params import ResourceInfo
from robusta.core.sinks.slack.slack_sink_params import SlackSinkParams
from robusta.core.playbooks.internal.ai_integration import ask_holmes

# Configure logging - set to DEBUG to see full block details
logging.basicConfig(
    level=logging.DEBUG if os.environ.get("DEBUG", "").lower() == "true" else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# You'll need to provide a Slack API token to run this script
# You can get one from https://api.slack.com/apps
# For testing, you can hardcode a token here, but don't commit it to the repo
# By default, try to get token from env var
SLACK_TOKEN = os.environ.get("SLACK_TOKEN", "xoxb-your-actual-token-here")
# The Slack channel to send messages to
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "test-robusta")


# In a real scenario, we'd use @action decorator, but for testing
# we'll just remove the CallbackBlock as it requires the full Robusta action system
# We'll use a simple MarkdownBlock with button simulation instead

# Create mock data for the Finding
def create_test_finding(title: str, severity: FindingSeverity = FindingSeverity.INFO) -> Finding:
    """Create a test finding with the given title and severity"""
    # Create a subject first with the correct type
    subject = FindingSubject(
        name="test-pod",
        namespace="default",
        subject_type=FindingSubjectType.TYPE_POD,
        labels={
            "app": "test-app",
            "environment": "test"
        },
        annotations={
            "description": "Test annotation"
        }
    )

    finding = Finding(
        title=title,
        source=FindingSource.PROMETHEUS,
        severity=severity,
        aggregation_key=f"test-{title}",
        finding_type=FindingType.ISSUE,
        description="This is a test finding for Slack message formatting",
        subject=subject
    )

    # We need to mock the service since TopServiceResolver won't work in test environment
    # Create a simple mock for the service object
    class MockService:
        def __init__(self, name, namespace, resource_type):
            self.name = name
            self.namespace = namespace
            self.resource_type = resource_type

        def get_resource_key(self):
            return f"{self.namespace}/{self.name}"

    # Set the service directly
    finding.service = MockService(
        name="test-deployment",
        namespace="default",
        resource_type="Deployment"
    )

    # Add links as proper Link objects

    finding.links = [
        Link(url="https://example.com/logs", name="View Logs"),
        Link(url="https://example.com/grafana", name="Grafana", type=LinkType.PROMETHEUS_GENERATOR_URL)
    ]

    return finding


def add_basic_blocks(finding: Finding) -> None:
    """Add some basic blocks to the finding"""
    finding.add_enrichment([
        HeaderBlock("Kubernetes Resource Information"),
        MarkdownBlock("This alert was triggered by high resource usage"),
        TableBlock(
            rows=[
                ["Namespace", "default"],
                ["Pod", "test-pod"],
                ["Container", "test-container"],
                ["CPU Usage", "250m"],
                ["Memory Usage", "512Mi"],
            ],
            headers=["Property", "Value"],
            table_name="Resource Usage",
        ),
        DividerBlock(),
        MarkdownBlock("*Recent Events:*"),
        ListBlock([
            "Pod started at 08:15:30",
            "CPU usage spiked at 08:45:22",
            "Memory usage increased at 08:47:15"
        ]),
        LinksBlock(links=[
            LinkProp(text="View Pod Details", url="https://example.com/pod"),
            LinkProp(text="View Container Logs", url="https://example.com/logs")
        ]),
        # Instead of using CallbackBlock which requires the @action decorator
        MarkdownBlock("*Available Actions:* (Simulated buttons)\n• Restart Pod\n• Scale Deployment")
    ])


def add_complex_table(finding: Finding) -> None:
    """Add a more complex table to the finding"""
    finding.add_enrichment([
        HeaderBlock("Detailed Resource Metrics"),
        TableBlock(
            rows=[
                ["pod-1", "Running", "0.25", "256Mi", "node-1", "app=web,tier=frontend"],
                ["pod-2", "Running", "0.50", "512Mi", "node-1", "app=web,tier=frontend"],
                ["pod-3", "CrashLoopBackOff", "0.10", "128Mi", "node-2", "app=db,tier=backend"],
                ["pod-4", "Running", "0.75", "1024Mi", "node-2", "app=api,tier=backend"],
                ["pod-5", "Pending", "0", "0", "None", "app=cache,tier=backend"],
            ],
            headers=["Pod", "Status", "CPU", "Memory", "Node", "Labels"],
            table_name="Cluster Pod Overview",
        )
    ])


def create_holmes_callback(finding: Finding) -> None:
    """Add a Holmes AI callback to the finding"""
    # Instead of using a real callback, we'll simulate it with markdown
    finding.add_enrichment([
        MarkdownBlock("*AI Investigation:*"),
        MarkdownBlock("🤖 *Ask Holmes AI* to investigate this alert (simulated button)"),
        MarkdownBlock("_Holmes would analyze this alert and provide insights on cause and remediation._")
    ])


def create_crash_loop_finding() -> Finding:
    """Create a sample crash loop finding with exact requested data"""
    subject = FindingSubject(
        name="payment-processing-worker-747ccfb9db-r7z7m",
        namespace="default",
        subject_type=FindingSubjectType.TYPE_POD,
        node="gke-1-4d3c8387-d24h",
        labels={
            "app": "payment-processing-worker",
            "pod-template-hash": "747ccfb9db"
        },
        annotations={}
    )

    finding = Finding(
        title="Crashing pod payment-processing-worker-747ccfb9db-r7z7m in namespace default",
        source=FindingSource.KUBERNETES_API_SERVER,
        severity=FindingSeverity.HIGH,
        aggregation_key="CrashLoopBackoff",
        finding_type=FindingType.ISSUE,
        subject=subject,
        failure=True,
        fingerprint="d7c6e2ac798ee28c8a4ac6c8c33de52e60f0b019cd10d78ac04831d44cf86389",
        starts_at=datetime(2025, 3, 23, 20, 8, 43, 822328)
    )

    # Add the crash info enrichment
    finding.add_enrichment([
        TableBlock(
            rows=[
                ["Container", "payment-processing-container"],
                ["Restarts", 130],
                ["Status", "WAITING"],
                ["Reason", "CrashLoopBackOff"]
            ],
            headers=["label", "value"],
            table_name="*Crash Info*",
            metadata={"format": "vertical"}
        ),
        TableBlock(
            rows=[
                ["Status", "TERMINATED"],
                ["Reason", "Completed"],
                ["Started at", "2025-03-23T18:08:32Z"],
                ["Finished at", "2025-03-23T18:08:32Z"]
            ],
            headers=["label", "value"],
            table_name="*Previous Container*",
            metadata={"format": "vertical"}
        )
    ], title="Container Crash information", enrichment_type=EnrichmentType.crash_info)

    # Add the logs enrichment
    finding.add_enrichment([
        FileBlock(
            filename="payment-processing-worker-747ccfb9db-r7z7m.log",
            contents=b'Environment variable DEPLOY_ENV is undefined\n'
        )
    ], title="Logs", enrichment_type=EnrichmentType.text_file)

    return finding


def create_node_saturation_finding() -> Finding:
    """Create a node saturation finding with exact requested data"""
    subject = FindingSubject(
        name="gke-1-4d3c8387-c4bp",
        subject_type=FindingSubjectType.TYPE_NODE,
        namespace="default",
        node="gke-1-4d3c8387-c4bp",
        container="node-exporter",
        labels={
            "beta.kubernetes.io/arch": "amd64",
            "beta.kubernetes.io/instance-type": "e2-standard-2",
            "beta.kubernetes.io/os": "linux",
            "cloud.google.com/gke-boot-disk": "pd-balanced",
            "cloud.google.com/gke-container-runtime": "containerd",
            "cloud.google.com/gke-cpu-scaling-level": "2",
            "cloud.google.com/gke-logging-variant": "DEFAULT",
            "cloud.google.com/gke-max-pods-per-node": "110",
            "cloud.google.com/gke-memory-gb-scaling-level": "8",
            "cloud.google.com/gke-nodepool": "pool-1",
            "cloud.google.com/gke-os-distribution": "cos",
            "cloud.google.com/gke-provisioning": "spot",
            "cloud.google.com/gke-spot": "true",
            "cloud.google.com/gke-stack-type": "IPV4",
            "cloud.google.com/machine-family": "e2",
            "cloud.google.com/private-node": "false",
            "failure-domain.beta.kubernetes.io/region": "us-central1",
            "failure-domain.beta.kubernetes.io/zone": "us-central1-c",
            "kubernetes.io/arch": "amd64",
            "kubernetes.io/hostname": "gke-4d3c8387-c4bp"
        },
        annotations={}
    )

    finding = Finding(
        title="System saturated, load per core is very high.",
        source=FindingSource.PROMETHEUS,
        severity=FindingSeverity.LOW,
        aggregation_key="NodeSystemSaturation",
        finding_type=FindingType.ISSUE,
        subject=subject,
        description="System load per core at 10.128.0.77:9104 has been above 2 for the last 15 minutes, is currently at 5.22.\nThis might indicate this instance resources saturation and can cause it becoming unresponsive.\n",
        starts_at=datetime(2025, 3, 23, 20, 9, 4, 838000)
    )

    # Could add enrichments here if needed

    return finding


def create_datadog_agent_crash_finding() -> Finding:
    """Create a datadog agent crash finding"""
    subject = FindingSubject(
        name="datadog-agent-w49mv",
        subject_type=FindingSubjectType.TYPE_POD,
        namespace="default",
        node="gke-1-4d3c8387-mm23",
        labels={
            "agent.datadoghq.com/component": "agent",
            "agent.datadoghq.com/name": "datadog",
            "agent.datadoghq.com/provider": "",
            "app.kubernetes.io/component": "agent",
            "app.kubernetes.io/instance": "datadog-agent",
            "app.kubernetes.io/managed-by": "datadog-operator",
            "app.kubernetes.io/name": "datadog-agent-deployment",
            "app.kubernetes.io/part-of": "default-datadog"
        },
        annotations={}
    )

    finding = Finding(
        title="Crashing pod datadog-agent-w49mv in namespace default",
        source=FindingSource.KUBERNETES_API_SERVER,
        severity=FindingSeverity.HIGH,
        aggregation_key="CrashLoopBackoff",
        finding_type=FindingType.ISSUE,
        subject=subject,
        failure=True,
        starts_at=datetime(2025, 3, 23, 20, 9, 2, 211000)
    )

    # Could add crash info enrichment here if needed

    return finding


def create_cpu_throttling_finding() -> Finding:
    """Create a CPU throttling finding with exact requested data"""
    subject = FindingSubject(
        name="vmagent-vmks-victoria-metrics-k8s-stack-6dcd499cb5-tdlkm",
        subject_type=FindingSubjectType.TYPE_POD,
        namespace="default",
        node="gke-4ksv",
        container="vmagent",
        labels={
            "app.kubernetes.io/component": "monitoring",
            "app.kubernetes.io/instance": "vmks-victoria-metrics-k8s-stack",
            "app.kubernetes.io/name": "vmagent",
            "managed-by": "vm-operator",
            "pod-template-hash": "6dcd499cb5",
            "alertname": "CPUThrottlingHigh",
            "container": "vmagent",
            "namespace": "default",
            "pod": "vmagent-vmks-victoria-metrics-k8s-stack-6dcd499cb5-tdlkm",
            "prometheus": "default/robusta-kube-prometheus-st-prometheus",
            "severity": "info"
        },
        annotations={
            "description": "71.13% throttling of CPU in namespace default for container vmagent in pod vmagent-vmks-victoria-metrics-k8s-stack-6dcd499cb5-tdlkm.",
            "runbook_url": "https://runbooks.prometheus-operator.dev/runbooks/kubernetes/cputhrottlinghigh",
            "summary": "Processes experience elevated CPU throttling."
        }
    )

    # Create the finding
    finding = Finding(
        title="Processes experience elevated CPU throttling.",
        source=FindingSource.PROMETHEUS,
        severity=FindingSeverity.INFO,
        aggregation_key="CPUThrottlingHigh",
        finding_type=FindingType.ISSUE,
        subject=subject,
        description="71.13% throttling of CPU in namespace default for container vmagent in pod vmagent-vmks-victoria-metrics-k8s-stack-6dcd499cb5-tdlkm.",
        failure=True,
        fingerprint="9674d957b35e0e9f",
        starts_at=datetime(2025, 3, 22, 10, 22, 10, 219000),
        add_silence_url=True,
        silence_labels={
            "alertname": "CPUThrottlingHigh",
            "container": "vmagent",
            "namespace": "default",
            "pod": "vmagent-vmks-victoria-metrics-k8s-stack-6dcd499cb5-tdlkm",
            "prometheus": "default/robusta-kube-prometheus-st-prometheus",
            "severity": "info"
        }
    )
    table_rows = [["Row1_Col1", "Row1_Col2"], ["Row2_Col1", "Row2_Col2"]]
    table_block = TableBlock(table_rows, headers=["Header1", "Header2"])
    # Add explanation enrichment
    finding.add_enrichment([
        MarkdownBlock(
            '📘 *Alert Explanation:* This pod is throttled due to its CPU limit. This can occur even when CPU usage is far below the limit. <https://github.com/robusta-dev/alert-explanations/wiki/CPUThrottlingHigh-(Prometheus-Alert)|Learn more.>'),
        MarkdownBlock(
            "🛠 *Robusta's Recommendation:* Remove this pod's CPU limit entirely. <https://home.robusta.dev/blog/stop-using-cpu-limits/|Using CPU limits is *not* a best practice.>"),table_block
    ], annotations={"unfurl": False})

    # Instead of adding an SVG file which can cause JSON serialization issues,
    # Let's add a simpler enrichment with just a table for CPU usage
    finding.add_enrichment([
        TableBlock(
            rows=[
                ["Current CPU Usage", "19.5m"],
                ["CPU Request", "100m"],
                ["CPU Limit", "300m"],
                ["Throttling Percentage", "71.13%"],
                ["Duration", "Last 5 minutes"]
            ],
            headers=["Metric", "Value"],
            table_name="*CPU Usage*"
        )
    ], title="Resources", enrichment_type=EnrichmentType.graph)

    # We're not including the SVG graph anymore to avoid JSON serialization issues

    # Add alert labels enrichment
    finding.add_enrichment([
        TableBlock(
            rows=[
                ["alertname", "CPUThrottlingHigh"],
                ["container", "vmagent"],
                ["namespace", "default"],
                ["pod", "vmagent-vmks-victoria-metrics-k8s-stack-6dcd499cb5-tdlkm"],
                ["prometheus", "default/robusta-kube-prometheus-st-prometheus"],
                ["severity", "info"]
            ],
            headers=["label", "value"],
            table_name="*Alert labels*",
            metadata={"format": "vertical"}
        )
    ], title="Alert labels", enrichment_type=EnrichmentType.alert_labels, annotations={"attachment": True})

    # Add Prometheus link
    finding.add_link(
        Link(
            url="http://robusta-kube-prometheus-st-prometheus.default:9090/graph?g0.expr=sum+by+%28cluster%2C+container%2C+pod%2C+namespace%29+%28increase%28container_cpu_cfs_throttled_periods_total%7Bcontainer%21%3D%22%22%7D%5B5m%5D%29%29+%2F+sum+by+%28cluster%2C+container%2C+pod%2C+namespace%29+%28increase%28container_cpu_cfs_periods_total%5B5m%5D%29%29+%3E+%2825+%2F+100%29&g0.tab=1",
            name="View Graph",
            type=LinkType.PROMETHEUS_GENERATOR_URL
        )
    )

    return finding


def main():
    if not SLACK_TOKEN:
        logging.error("SLACK_TOKEN environment variable not set. Please set it to proceed.")
        sys.exit(1)

    # Enable detailed block logging if DEBUG=true
    if os.environ.get("DEBUG", "").lower() == "true":
        logging.info("DEBUG mode enabled - will print detailed block information")
        logging.info("Run script with DEBUG=false to disable detailed logging")

    # Initialize the SlackSender
    sender = SlackSender(
        slack_token=SLACK_TOKEN,
        account_id="test-account",
        cluster_name="test-cluster",
        signing_key="test-signing-key",
        slack_channel=SLACK_CHANNEL
    )

    # Create the SlackSinkParams
    sink_params = SlackSinkParams(
        name="test-sink",
        slack_channel=SLACK_CHANNEL,
        api_key=SLACK_TOKEN,
        investigate_link=True,
        prefer_redirect_to_platform=False,
        max_log_file_limit_kb=1000
    )

    # Create a SlackSinkParams with legacy style
    legacy_template_params = SlackSinkParams(
        name="legacy-template-sink",
        slack_channel=SLACK_CHANNEL,
        api_key=SLACK_TOKEN,
        investigate_link=True,
        prefer_redirect_to_platform=False,
        max_log_file_limit_kb=1000,
        template_style="legacy"  # Use the legacy template style
    )

    # Create a SlackSinkParams with a custom template
    custom_template_params = SlackSinkParams(
        name="custom-template-sink",
        slack_channel=SLACK_CHANNEL,
        api_key=SLACK_TOKEN,
        investigate_link=True,
        prefer_redirect_to_platform=False,
        max_log_file_limit_kb=1000,
        template_name="custom.j2",
        slack_custom_templates={
            "custom.j2": """
            {
              "type": "section",
              "text": {
                "type": "mrkdwn",
                "text": "{{ status_emoji }} *CUSTOM TEMPLATE: {{ title }}*"
              }
            }

            {
              "type": "context",
              "elements": [
                {
                  "type": "mrkdwn", 
                  "text": ":rotating_light: {{ alert_type }} on cluster {{ cluster_name }}"
                },
                {
                  "type": "mrkdwn",
                  "text": "{{ severity_emoji }} {{ severity }} severity"
                }
                {% if resource_text %}
                ,{
                  "type": "mrkdwn",
                  "text": "{{ resource_emoji }} {{ resource_text }}"
                }
                {% endif %}
              ]
            }
            """
        }
    )

    # Create all findings
    crash_loop_finding = create_crash_loop_finding()
    node_saturation_finding = create_node_saturation_finding()
    datadog_agent_crash_finding = create_datadog_agent_crash_finding()
    cpu_throttling_finding = create_cpu_throttling_finding()

    # Send findings to Slack with standard templates
    logging.info(f"Sending crash loop finding to Slack channel (DEFAULT TEMPLATE): {SLACK_CHANNEL}...")
    sender.send_finding_to_slack(crash_loop_finding, sink_params, platform_enabled=True)

    # Send findings to Slack with legacy template style
    logging.info(f"Sending node saturation finding to Slack channel with LEGACY TEMPLATE: {SLACK_CHANNEL}...")
    sender.send_finding_to_slack(node_saturation_finding, legacy_template_params, platform_enabled=True)

    # Send findings to Slack with custom templates
    logging.info(f"Sending datadog agent crash finding to Slack channel with CUSTOM TEMPLATE: {SLACK_CHANNEL}...")
    sender.send_finding_to_slack(datadog_agent_crash_finding, custom_template_params, platform_enabled=True)

    logging.info(f"Sending CPU throttling finding to Slack channel with CUSTOM TEMPLATE: {SLACK_CHANNEL}...")
    sender.send_finding_to_slack(cpu_throttling_finding, custom_template_params, platform_enabled=True)

    logging.info(f"Test messages sent successfully to Slack channel: {SLACK_CHANNEL}")

    # Uncomment the below code to send the original test findings
    """
    # Create test findings with different severities
    finding_info = create_test_finding("Test INFO Alert", FindingSeverity.INFO)
    finding_low = create_test_finding("Test LOW Alert", FindingSeverity.LOW)
    finding_medium = create_test_finding("Test MEDIUM Alert", FindingSeverity.MEDIUM)
    finding_high = create_test_finding("Test HIGH Alert", FindingSeverity.HIGH)

    # Add different types of content to each finding
    add_basic_blocks(finding_info)
    add_complex_table(finding_low)

    # Combine basic and complex content for medium severity
    add_basic_blocks(finding_medium)
    add_complex_table(finding_medium)

    # Add AI callback for high severity
    add_basic_blocks(finding_high)
    create_holmes_callback(finding_high)

    # Send all test findings to Slack
    logging.info(f"Sending INFO finding to Slack channel: {SLACK_CHANNEL}...")
    sender.send_finding_to_slack(finding_info, sink_params, platform_enabled=True)

    logging.info(f"Sending LOW finding to Slack channel: {SLACK_CHANNEL}...")
    sender.send_finding_to_slack(finding_low, sink_params, platform_enabled=True)

    logging.info(f"Sending MEDIUM finding to Slack channel: {SLACK_CHANNEL}...")
    sender.send_finding_to_slack(finding_medium, sink_params, platform_enabled=True)

    logging.info(f"Sending HIGH finding with Holmes callback to Slack channel: {SLACK_CHANNEL}...")
    sender.send_finding_to_slack(finding_high, sink_params, platform_enabled=True)
    """


if __name__ == "__main__":
    main()