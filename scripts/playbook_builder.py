from collections import OrderedDict
from typing import List, Optional

import streamlit as st
import streamlit_pydantic as sp
import yaml
from pydantic import BaseModel, Field

st.set_page_config(
    page_title="Playbook Builder",
    page_icon=":wrench:",
)

st.title(":wrench: Playbook Builder", anchor=None)

if "expander_state" not in st.session_state:
    st.session_state.expander_state = [True, False, False, False, False]

# INITIALIZING ALL EXPANDERS
trigger_expander = st.expander(
    ":zap: Trigger - A trigger is an event that starts your Playbook", expanded=st.session_state.expander_state[0]
)
trigger_parameter_expander = st.expander("Configure Trigger", expanded=st.session_state.expander_state[1])
action_expander = st.expander(
    ":boom: Action - An action is an event a Playbook performs after it starts",
    expanded=st.session_state.expander_state[2],
)
action_parameter_expander = st.expander("Configure Action", expanded=st.session_state.expander_state[3])
playbook_expander = st.expander(":scroll: Playbook", expanded=st.session_state.expander_state[4])


# Temporary code
class K8sBaseTrigger(BaseModel):
    kind: str
    name_prefix: str = Field(None, description="Give it a value")
    namespace_prefix: str = Field(None, description="Name of a specific namespace")
    labels_selector: str = None


class SomeOtherTriggerParams(BaseModel):
    namespace_prefix: str = None
    labels_selector: str = None


class PrometheusParams(BaseModel):
    """
    :var prometheus_url: Prometheus url. If omitted, we will try to find a prometheus instance in the same cluster
    :var prometheus_auth: Prometheus auth header to be used in Authorization header. If omitted, we will not add any auth header

    :example prometheus_url: "http://prometheus-k8s.monitoring.svc.cluster.local:9090"
    :example prometheus_auth: Basic YWRtaW46cGFzc3dvcmQ=
    """

    prometheus_url: Optional[str] = None
    prometheus_auth: Optional[str] = None


class ResourceGraphEnricherParams(PrometheusParams):
    """
    :var resource_type: one of: CPU, Memory, Disk (see ResourceChartResourceType)
    :var graph_duration_minutes: Graph duration is minutes. Default is 60.

    :example resource_type: Memory
    """

    resource_type: str
    graph_duration_minutes: int = 60

    previous: bool = Field(False, description="descr text")


class CustomGraphEnricherParams(PrometheusParams):
    """
    :var promql_query: Promql query. You can use $pod, $node and $node_internal_ip to template (see example). For more information, see https://prometheus.io/docs/prometheus/latest/querying/basics/
    :var graph_title: A nicer name for the Prometheus query.
    :var graph_duration_minutes: Graph duration is minutes.
    :var chart_values_format: Customize the y-axis labels with one of: Plain, Bytes, Percentage (see ChartValuesFormat)

    :example promql_query: instance:node_cpu_utilisation:rate5m{job="node-exporter", instance=~"$node_internal_ip:[0-9]+", cluster=""} != 0
    :example graph_title: CPU Usage for this nod
    """

    promql_query: str
    graph_title: Optional[str] = None
    graph_duration_minutes: int = 60
    chart_values_format: str = "Plain"


class ActionParams(BaseModel):
    """
    Base class for all Action parameter classes.
    """

    def post_initialization(self):
        """
        This function can be used to run post initialization logic on the action params
        """
        pass

    pass


class GitAuditParams(ActionParams):
    """
    :var cluster_name: This cluster name. Changes will be audited under this cluster name.
    :var git_url: Audit Git repository url.
    :var git_key: Git repository deployment key with *write* access. To set this up `generate a private/public key pair for GitHub <https://docs.github.com/en/developers/overview/managing-deploy-keys#setup-2>`_.
    :var ignored_changes: List of changes that shouldn't be audited.

    :example git_url: "git@github.com:arikalon1/robusta-audit.git"
    """

    cluster_name: str
    git_url: str = Field(..., description="Example: https://hello.dev")
    git_key: str
    ignored_changes: str


class LogEnricherParams(ActionParams):
    """
    :var container_name: Specific container to get logs from
    :var warn_on_missing_label: Send a warning if the alert doesn't have a pod label
    :var regex_replacer_patterns: regex patterns to replace text, for example for security reasons (Note: Replacements are executed in the given order)
    :var regex_replacement_style: one of SAME_LENGTH_ASTERISKS or NAMED (See RegexReplacementStyle)
    :var filter_regex: only shows lines that match the regex
    """

    container_name: Optional[str]
    warn_on_missing_label: bool = False
    regex_replacer_patterns: Optional[List] = None
    regex_replacement_style: Optional[str] = None
    previous: bool = False
    filter_regex: Optional[str] = None


triggers = {
    "on_oom_kill": {
        "about": "Fires when a Pod is crash looping. It has the following parameters:",
        "available_actions": ["logs_enricher", "template_enricher"],
        "params": K8sBaseTrigger,
    },
    "pod_restart": {
        "about": "Fires when a Pod is updated. Creations and deletions are excluded.",
        "available_actions": ["template_enricher"],
        "params": K8sBaseTrigger,
    },
}

actions = {
    "logs_enricher": {
        "about": """Fetch and attach Pod logs. The pod to fetch logs for is determined by the alert’s pod label from Prometheus.
                 By default, if the alert has no pod this enricher will silently do nothing.""",
        "params": LogEnricherParams,
    },
    "template_enricher": {
        "about": """Enrich the finding with the node's status conditions.
                 Can help troubleshooting Node issues.""",
        "params": PrometheusParams,
    },
}

# End temporary code


# TRIGGER
with trigger_expander:

    trigger_name = st.selectbox("Type to search", triggers.keys(), key="trigger")
    st.markdown(triggers[trigger_name]["about"])

    if st.button("Continue", key="button1"):
        st.session_state.expander_state = [False, True, False, False, False]
        st.experimental_rerun()


# TRIGGER PARAMETER
with trigger_parameter_expander:
    # st.header("Available Parameters")
    trigger_data = sp.pydantic_input(key=f"trigger_form-{trigger_name}", model=triggers[trigger_name]["params"])

    if st.button("Continue", key="button2"):
        st.session_state.expander_state = [False, False, True, False, False]
        st.experimental_rerun()


# ACTION
with action_expander:

    action_name = st.selectbox("Choose an action", triggers[trigger_name]["available_actions"], key="actions")

    st.markdown(actions[action_name]["about"])

    if st.button("Continue", key="button3"):
        st.session_state.expander_state = [False, False, False, True, False]
        st.experimental_rerun()


# ACTION PARAMETER
with action_parameter_expander:

    action_data = sp.pydantic_input(key=f"action_form-{action_name}", model=actions[action_name]["params"])

    if st.button("Continue", key="button4"):
        st.session_state.expander_state = [False, False, False, False, True]
        st.experimental_rerun()


# DISPLAY PLAYBOOK
with playbook_expander:
    st.markdown(
        "Add this code to your **generated_values.yaml** and [upgrade Robusta](https://docs.robusta.dev/external-prom-docs/setup-robusta/upgrade.html)"
    )

    playbook = {
        "customPlaybooks": [
            OrderedDict([("triggers", [{trigger_name: trigger_data}]), ("actions", [{action_name: action_data}])])
        ]
    }

    yaml.add_representer(
        OrderedDict, lambda dumper, data: dumper.represent_mapping("tag:yaml.org,2002:map", data.items())
    )

    st.code(yaml.dump(playbook))
