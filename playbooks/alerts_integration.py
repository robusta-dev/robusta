from robusta.api import *
from node_cpu_analysis import do_node_cpu_analysis


class GenParams(BaseModel):
    name: str
    params: Dict[Any,Any] = None

class Silencer:
    params: Dict[Any,Any]

    def __init__(self, params: Dict[Any,Any]):
        self.params = params

    def silence(self, alert: PrometheusKubernetesAlert) -> bool:
        pass


class NodeRestartSilencer(Silencer):

    post_restart_silence: int = 300

    def __init__(self, params: Dict[Any, Any]):
        super().__init__(params)
        if params and params.get("post_restart_silence"):
            self.post_restart_silence = self.params.get("post_restart_silence")

    def silence(self, alert: PrometheusKubernetesAlert) -> bool:
        if not alert.obj or not alert.obj.kind == "Pod":
            return False # Silencing only pod alerts on NodeRestartSilencer

        node: Node = Node.readNode(alert.obj.spec.nodeName).obj
        if not node:
            logging.warning(f"Node {alert.obj.spec.nodeName} not found for NodeRestartSilencer for {alert}")
            return False

        last_transition_times = [condition.lastTransitionTime for condition in node.status.conditions if condition.type == "Ready"]
        if last_transition_times and last_transition_times[0]:
            node_start_time_str =  last_transition_times[0]
        else: # if no ready time, take creation time
            node_start_time_str = node.metadata.creationTimestamp

        node_start_time = datetime.strptime(node_start_time_str, '%Y-%m-%dT%H:%M:%SZ')
        return datetime.utcnow().timestamp() < (node_start_time.timestamp() + self.post_restart_silence)


class Enricher:
    params: Dict[Any, Any] = None

    def __init__(self, params: Dict[Any,Any]):
        self.params = params

    def enrich(self, alert: PrometheusKubernetesAlert):
        pass


class DefaultEnricher (Enricher):

    def enrich(self, alert: PrometheusKubernetesAlert):
        alert_name = alert.alert.labels.get("alertname", "")
        labels = alert.alert.labels
        annotations = alert.alert.annotations

        if "summary" in annotations:
            alert.report_title = f'{alert_name}: {annotations["summary"]}'
        else:
            alert.report_title = alert_name

        alert.report_attachment_blocks.append(TableBlock(labels.items(), ["label", "value"]))
        if "description" in annotations:
            alert.report_attachment_blocks.append(MarkdownBlock(annotations["description"]))


class NodeCPUEnricher (Enricher):

    def enrich(self, alert: PrometheusKubernetesAlert):
        alert.report_blocks.extend(do_node_cpu_analysis(alert.obj.metadata.name))

DEFAULT_ENRICHER = "AlertDefaults"

silencers = {}
silencers["NodeRestartSilencer"] = NodeRestartSilencer

enrichers = {}
enrichers[DEFAULT_ENRICHER] = DefaultEnricher
enrichers["NodeCPUAnalysis"] = NodeCPUEnricher


class AlertConfig(BaseModel):
    alert_name: str
    silencers: List[GenParams] = []
    enrichers: List[GenParams] = []


class AlertsIntegrationParams(BaseModel):
    slack_channel: str
    default_enricher: str = DEFAULT_ENRICHER
    alerts_config: List[AlertConfig]


def default_alert_config(alert_name, config: AlertsIntegrationParams) -> AlertConfig:
    return AlertConfig(alert_name=alert_name, silencers=[], enrichers=[GenParams(name=config.default_enricher)])

@on_pod_prometheus_alert(status="firing")
def alerts_integration(alert: PrometheusKubernetesAlert, config: AlertsIntegrationParams):
    logging.info(f'running alerts_integration alert - alert: {alert.alert} pod: {alert.obj.metadata.name if alert.obj is not None else "None!"}')

    alert.slack_channel = config.slack_channel
    alert_name = alert.alert.labels.get("alertname")

    # filter out the dummy watchdog alert that prometheus constantly sends so that you know it is alive
    if alert_name == "Watchdog" and alert.alert.labels.get("severity") == "none":
        logging.debug(f"skipping watchdog alert {alert}")
        return

    logging.info(
        f'running alerts_integration alert - alert: {alert.alert} pod: {alert.obj.metadata.name if alert.obj is not None else "None!"}')

    alert_configs = [alert_config for alert_config in config.alerts_config if alert_config.alert_name == alert_name]
    if not alert_configs:
        alert_configs = [default_alert_config(alert_name, config)]

    for alert_config in alert_configs:
        for silencer_config in alert_config.silencers:
            silencer_class = silencers.get(silencer_config.name)
            if silencer_class is None:
                logging.error(f"Silencer {silencer_config.name} for alert {alert_name} does not exist. Silence not enforced")
                continue
            if silencer_class(silencer_config.params).silence(alert):
                return

        for enricher_config in alert_config.enrichers:
            enricher_class = enrichers.get(enricher_config.name)
            if enricher_class is None:
                logging.error(f"Enricher {enricher_config.name} for alert {alert_name} does not exist. No enrichment")
                continue
            enricher_class(enricher_config.params).enrich(alert)

    if alert.report_blocks or alert.report_title or alert.report_attachment_blocks:
        send_to_slack(alert)
