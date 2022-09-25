from robusta.api import *
from robusta.core.reporting.blocks import PrometheusBlock


def parse_timestamp_string(date_string: str) -> Optional[datetime]:
    try:
        if date_string:
            return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S %Z")
        return None
    except Exception:
        logging.error(f"Failed parsing time string {date_string}", exc_info=True)
        return None


def parse_duration(duration: Union[PrometheusDateRange, PrometheusDuration]) -> (Optional[datetime], Optional[datetime]):
    if isinstance(duration, PrometheusDateRange):
        return parse_timestamp_string(duration.starts_at), parse_timestamp_string(duration.ends_at)
    elif isinstance(duration, PrometheusDuration):
        starts_at = datetime.utcnow() - timedelta(minutes=duration.duration_minutes)
        ends_at = datetime.utcnow()
        return starts_at, ends_at
    logging.error("Non supported duration provided")
    return None, None


@action
def prometheus_enricher(event: ExecutionBaseEvent, params: PrometheusQueryParams):
    """
        Enriches the finding with a prometheus query

        for example prometheus queries see here:
        https://prometheus.io/docs/prometheus/latest/querying/examples/
    """
    # verifies params.promql_query is not an empty string ""
    if not params.promql_query:
        raise Exception(f"Invalid request, prometheus_enricher requires a promql query.")
    starts_at, ends_at = parse_duration(params.duration)
    if not starts_at or not ends_at:
        raise Exception(f"Invalid request, verify the duration times are of format '%Y-%m-%d %H:%M:%S %Z'")
        return

    prometheus_result = run_prometheus_query(prometheus_base_url=params.prometheus_url, promql_query=params.promql_query, starts_at=starts_at, ends_at=ends_at)
    event.add_enrichment(
        [PrometheusBlock(data=prometheus_result, query=params.promql_query)],
    )
