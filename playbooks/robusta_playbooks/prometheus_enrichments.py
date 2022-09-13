from robusta.api import *

@action
def prometheus_enricher(event: ExecutionBaseEvent, params: PrometheusQueryParams):
    if not params.promql_query or not params.graph_duration_minutes:
        logging.error(f"invalid params for prometheus_enricher: {params}")
        return
    result = run_prometheus_query(prometheus_base_url=params.prometheus_url, promql_query=params.promql_query, starts_at=None, graph_duration_minutes=params.graph_duration_minutes)
    event.add_enrichment(
        [FileBlock(f"prometeus_query.log", f"{result}".encode())],
    )