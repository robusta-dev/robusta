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


def get_times_from_duration(duration: Union[PrometheusDateRange, PrometheusDuration]):
    if isinstance(duration, PrometheusDateRange):
        return parse_timestamp_string(duration.starts_at), parse_timestamp_string(duration.ends_at)
    elif isinstance(duration, PrometheusDuration):
        starts_at = datetime.utcnow() - timedelta(minutes=duration.duration_minutes)
        ends_at = datetime.utcnow()
        return starts_at, ends_at

@action
def prometheus_enricher(event: ExecutionBaseEvent, params: PrometheusQueryParams):
    """
        Enriches the finding with a prometheus query

        for example prometheus queries see here:
        https://prometheus.io/docs/prometheus/latest/querying/examples/
    """
    starts_at, ends_at = get_times_from_duration(params.duration)
    if not starts_at or not ends_at:
        logging.error(f"Unparsable time params for prometheus_enricher starts_at: '{params.duration}', verify the times are of format '%Y-%m-%d %H:%M:%S%Z'")
        return

    prometheus_result= run_prometheus_query(prometheus_base_url=params.prometheus_url, promql_query=params.promql_query, starts_at=starts_at, ends_at=ends_at)
    event.add_enrichment(
        [PrometheusBlock(data=prometheus_result, query=params.promql_query)],
    )
