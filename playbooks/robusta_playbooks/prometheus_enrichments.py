from robusta.api import *


def parse_timestamp_string(date_string: str) -> datetime:
    try:
        if date_string:
            return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        return None
    except Exception:
        logging.error(f"Failed parsing time string {date_string}", exc_info=True)
        return None


@action
def prometheus_enricher(event: ExecutionBaseEvent, params: PrometheusQueryParams):
    """
        Enriches the finding with a prometheus query

        for example prometheus queries see here:
        https://prometheus.io/docs/prometheus/latest/querying/examples/
    """
    if not params.promql_query or (not params.graph_duration_minutes and not params.starts_at):
        logging.error(f"invalid params for prometheus_enricher: {params}")
        return
    starts_at = parse_timestamp_string(params.starts_at)
    end_time = parse_timestamp_string(params.end_time)
    if not starts_at and params.graph_duration_minutes:
        starts_at = datetime.now() - timedelta(minutes=params.graph_duration_minutes)
    if (params.starts_at and not starts_at) or (params.end_time and not end_time):
        logging.error(f"unparsable time params for prometheus_enricher starts_at: '{params.starts_at}' ends_at: '{params.ends_at}'")
        return

    result = run_prometheus_query(prometheus_base_url=params.prometheus_url, promql_query=params.promql_query, starts_at=starts_at, graph_duration_minutes=params.graph_duration_minutes, end_time=end_time)
    # we return the whole result list (instead of the first element) since some queries can have multiple results,
    # for example the "up" query returns an object for each service,
    # whereas querying resources usually returns one json object in the list
    json_str = json.dumps(
        {
            "data": result
        }
    )
    event.add_enrichment(
        [JsonBlock(json_str)],
    )
