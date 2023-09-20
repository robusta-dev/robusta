from hikaru.model.rel_1_26 import Container, DaemonSet, Deployment, Pod, ReplicaSet, StatefulSet, Volume

from robusta.core.discovery.discovery import (
    extract_containers_k8,
    extract_ready_pods,
    extract_total_pods,
    extract_volumes_k8,
    is_pod_finished,
    is_release_managed_by_helm,
    should_report_pod,
)
from robusta.core.discovery.resource_names import ResourceNameLister
from robusta.core.model.base_params import (
    ActionParams,
    AlertResourceGraphEnricherParams,
    BashParams,
    ChartValuesFormat,
    CustomGraphEnricherParams,
    EventEnricherParams,
    FindingKeyParams,
    GrafanaAnnotationParams,
    GrafanaParams,
    LogEnricherParams,
    NamedRegexPattern,
    PodResourceGraphEnricherParams,
    PodRunningParams,
    ProcessParams,
    PrometheusDateRange,
    PrometheusDuration,
    PrometheusParams,
    PrometheusQueryParams,
    RateLimitParams,
    ResourceChartItemType,
    ResourceChartResourceType,
    ResourceGraphEnricherParams,
    TimedPrometheusParams,
    VideoEnricherParams,
)
from robusta.core.model.env_vars import (
    ALERT_BUILDER_WORKERS,
    CLUSTER_STATUS_PERIOD_SEC,
    CUSTOM_PLAYBOOKS_ROOT,
    DEFAULT_PLAYBOOKS_PIP_INSTALL,
    DEFAULT_PLAYBOOKS_ROOT,
    DEFAULT_TIMEZONE,
    DISCORD_TABLE_COLUMNS_LIMIT,
    DISCOVERY_PERIOD_SEC,
    ENABLE_TELEMETRY,
    FLOAT_PRECISION_LIMIT,
    GIT_MAX_RETRIES,
    GRAFANA_READ_TIMEOUT,
    GRAFANA_RENDERER_URL,
    INCOMING_EVENTS_QUEUE_MAX_SIZE,
    INCOMING_REQUEST_TIME_WINDOW_SECONDS,
    INSTALLATION_NAMESPACE,
    INTERNAL_PLAYBOOKS_ROOT,
    NUM_EVENT_THREADS,
    PLAYBOOKS_CONFIG_FILE_PATH,
    PLAYBOOKS_ROOT,
    PORT,
    PRINTED_TABLE_MAX_WIDTH,
    PROMETHEUS_ENABLED,
    PROMETHEUS_REQUEST_TIMEOUT_SECONDS,
    RELAY_EXTERNAL_ACTIONS_URL,
    RELEASE_NAME,
    RESOURCE_UPDATES_CACHE_TTL_SEC,
    ROBUSTA_LOGO_URL,
    ROBUSTA_TELEMETRY_ENDPOINT,
    ROBUSTA_UI_DOMAIN,
    RSA_KEYS_PATH,
    RUNNER_VERSION,
    SEND_ADDITIONAL_TELEMETRY,
    SERVICE_CACHE_MAX_SIZE,
    SERVICE_CACHE_TTL_SEC,
    SLACK_TABLE_COLUMNS_LIMIT,
    SUPABASE_LOGIN_RATE_LIMIT_SEC,
    TEAMS_IMAGE_WIDTH,
    TELEMETRY_PERIODIC_SEC,
    TRACE_INCOMING_REQUESTS,
    WEBSOCKET_PING_INTERVAL,
    WEBSOCKET_PING_TIMEOUT,
)
from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.model.k8s_operation_type import K8sOperationType
from robusta.core.model.pods import (
    ContainerResources,
    PodContainer,
    PodResources,
    ResourceAttributes,
    find_most_recent_oom_killed_container,
    format_unit,
    get_oom_kill_time,
    get_oom_killed_container,
    is_state_in_oom_status,
    k8s_memory_factors,
    pod_limits,
    pod_most_recent_oom_killed_container,
    pod_other_requests,
    pod_requests,
    pod_resources,
    pod_restarts,
)
from robusta.core.model.services import ContainerInfo, EnvVar, Resources, ServiceConfig, ServiceInfo, VolumeInfo
from robusta.core.persistency.in_memory import get_persistent_data
from robusta.core.playbooks.actions_registry import Action, action
from robusta.core.playbooks.common import get_event_timestamp, get_resource_events, get_resource_events_table
from robusta.core.playbooks.container_playbook_utils import create_container_graph
from robusta.core.playbooks.job_utils import CONTROLLER_UID, get_job_all_pods, get_job_latest_pod, get_job_selector
from robusta.core.playbooks.node_playbook_utils import create_node_graph_enrichment
from robusta.core.playbooks.pod_utils.crashloop_utils import get_crash_report_blocks
from robusta.core.playbooks.pod_utils.imagepull_utils import (
    get_image_pull_backoff_blocks,
    get_image_pull_backoff_container_statuses,
)
from robusta.core.playbooks.pod_utils.pending_pod_utils import get_pending_pod_blocks
from robusta.core.playbooks.prometheus_enrichment_utils import (
    XAxisLine,
    create_chart_from_prometheus_query,
    create_graph_enrichment,
    create_resource_enrichment,
    get_node_internal_ip,
    run_prometheus_query,
)
from robusta.core.playbooks.trigger import (
    BaseTrigger,
    CustomTriggers,
    K8sTriggers,
    PrometheusAlertTriggers,
    ScheduledTriggers,
    Trigger,
)
from robusta.core.reporting import (
    BaseBlock,
    CallbackBlock,
    CallbackChoice,
    DividerBlock,
    Emojis,
    Enrichment,
    FileBlock,
    Filterable,
    Finding,
    FindingSeverity,
    FindingStatus,
    FindingSubject,
    HeaderBlock,
    JsonBlock,
    KubernetesDiffBlock,
    KubernetesFieldsBlock,
    ListBlock,
    MarkdownBlock,
    PrometheusBlock,
    ScanReportBlock,
    ScanReportRow,
    TableBlock,
    VideoLink,
)
from robusta.core.reporting.action_requests import (
    ActionRequestBody,
    ExternalActionRequest,
    OutgoingActionRequest,
    PartialAuth,
    sign_action_request,
)
from robusta.core.reporting.callbacks import ExternalActionRequestBuilder
from robusta.core.reporting.consts import (
    EnrichmentAnnotation,
    FindingAggregationKey,
    FindingSource,
    FindingSubjectType,
    FindingType,
    ScanType,
    SlackAnnotations,
)
from robusta.core.reporting.custom_rendering import RendererType, charts_style, render_value
from robusta.core.reporting.finding_subjects import KubeObjFindingSubject, PodFindingSubject
from robusta.core.schedule.model import (
    DynamicDelayRepeat,
    FixedDelayRepeat,
    JobState,
    JobStatus,
    ScheduledJob,
    SchedulingInfo,
)
from robusta.core.sinks import SinkBase, SinkBaseParams, SinkConfigBase
from robusta.core.sinks.kafka import KafkaSink, KafkaSinkConfigWrapper, KafkaSinkParams
from robusta.core.triggers.helm_releases_triggers import HelmReleasesEvent, HelmReleasesTriggerEvent
from robusta.integrations.argocd.argocd_client import ArgoCDClient
from robusta.integrations.git.git_repo import ClusterChanges, GitRepo, GitRepoManager, SingleChange
from robusta.integrations.grafana import Grafana
from robusta.integrations.kubernetes.api_client_utils import (
    exec_commands,
    exec_shell_command,
    get_pod_logs,
    list_available_services,
    parse_kubernetes_datetime,
    parse_kubernetes_datetime_to_ms,
    parse_kubernetes_datetime_with_ms,
    prepare_pod_command,
    to_kubernetes_name,
    upload_file,
    wait_for_pod_status,
    wait_until,
    wait_until_job_complete,
)
from robusta.integrations.kubernetes.autogenerated.events import (
    KIND_TO_EVENT_CLASS,
    LOADERS_MAPPINGS,
    ClusterRoleAttributes,
    ClusterRoleBindingAttributes,
    ClusterRoleBindingChangeEvent,
    ClusterRoleBindingEvent,
    ClusterRoleChangeEvent,
    ClusterRoleEvent,
    ConfigMapAttributes,
    ConfigMapChangeEvent,
    ConfigMapEvent,
    DaemonSetAttributes,
    DaemonSetChangeEvent,
    DaemonSetEvent,
    DeploymentAttributes,
    DeploymentChangeEvent,
    DeploymentEvent,
    EventAttributes,
    EventChangeEvent,
    EventEvent,
    HorizontalPodAutoscalerAttributes,
    HorizontalPodAutoscalerChangeEvent,
    HorizontalPodAutoscalerEvent,
    JobAttributes,
    JobChangeEvent,
    JobEvent,
    KubernetesAnyChangeEvent,
    KubernetesResourceEvent,
    NamespaceAttributes,
    NamespaceChangeEvent,
    NamespaceEvent,
    NodeAttributes,
    NodeChangeEvent,
    NodeEvent,
    PersistentVolumeAttributes,
    PersistentVolumeChangeEvent,
    PersistentVolumeEvent,
    PodAttributes,
    PodChangeEvent,
    PodEvent,
    ReplicaSetAttributes,
    ReplicaSetChangeEvent,
    ReplicaSetEvent,
    ResourceAttributes,
    ResourceLoader,
    ServiceAccountAttributes,
    ServiceAccountChangeEvent,
    ServiceAccountEvent,
    ServiceAttributes,
    ServiceChangeEvent,
    ServiceEvent,
    StatefulSetAttributes,
    StatefulSetChangeEvent,
    StatefulSetEvent,
)
from robusta.integrations.kubernetes.autogenerated.models import VERSION_KIND_TO_MODEL_CLASS, get_api_version
from robusta.integrations.kubernetes.custom_models import (
    JobSecret,
    Process,
    ProcessList,
    RegexReplacementStyle,
    RobustaDeployment,
    RobustaEvent,
    RobustaJob,
    RobustaPod,
    build_selector_query,
    does_daemonset_have_toleration,
    does_node_have_taint,
    extract_image_list,
    extract_images,
    get_images,
    list_pods_using_selector,
)
from robusta.integrations.kubernetes.process_utils import ProcessFinder, ProcessType
from robusta.integrations.prometheus.models import (
    SEVERITY_MAP,
    AlertManagerEvent,
    PrometheusAlert,
    PrometheusKubernetesAlert,
)
from robusta.integrations.prometheus.utils import (
    AlertManagerDiscovery,
    PrometheusDiscovery,
    ServiceDiscovery,
    get_prometheus_connect,
)
from robusta.integrations.resource_analysis.cpu_analyzer import CpuAnalyzer
from robusta.integrations.resource_analysis.memory_analyzer import MemoryAnalyzer, pretty_size
from robusta.integrations.resource_analysis.node_cpu_analyzer import NodeCpuAnalyzer
from robusta.integrations.scheduled.event import ScheduledExecutionEvent
from robusta.integrations.scheduled.playbook_scheduler_manager_impl import (
    PlaybooksSchedulerManagerImpl,
    ScheduledIntegrationParams,
)
from robusta.integrations.scheduled.trigger import DynamicDelayRepeatTrigger, FixedDelayRepeatTrigger
from robusta.integrations.slack.sender import SlackSender
from robusta.runner.object_updater import update_item_attr
from robusta.utils.base64_utils import is_base64_encoded
from robusta.utils.cluster_provider_discovery import cluster_provider
from robusta.utils.common import duplicate_without_fields, is_matching_diff
from robusta.utils.error_codes import ActionException, ErrorCodes
from robusta.utils.function_hashes import action_hash
from robusta.utils.parsing import load_json
from robusta.utils.rate_limiter import RateLimiter
from robusta.utils.silence_utils import (
    AddSilenceParams,
    BaseSilenceParams,
    DeleteSilenceParams,
    Silence,
    SilenceOperation,
    gen_alertmanager_headers,
    get_alertmanager_url,
    get_alertmanager_url_path,
)
