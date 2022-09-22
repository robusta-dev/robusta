from robusta.api import *
from datetime import datetime
from prometheus_api_client import PrometheusConnect, PrometheusApiClientException

"""
This function is copied from the python package prometheus_api_client
git repo: https://github.com/4n4nd/prometheus-api-client-python
It used to return only the result and not the resultType leading for less safe and clear code
"""

def custom_query_range(
    self, query: str, start_time: datetime, end_time: datetime, step: str, params: dict = None
):
    """
    Send a query_range to a Prometheus Host.
    This method takes as input a string which will be sent as a query to
    the specified Prometheus Host. This query is a PromQL query.
    :param query: (str) This is a PromQL query, a few examples can be found
        at https://prometheus.io/docs/prometheus/latest/querying/examples/
    :param start_time: (datetime) A datetime object that specifies the query range start time.
    :param end_time: (datetime) A datetime object that specifies the query range end time.
    :param step: (str) Query resolution step width in duration format or float number of seconds
    :param params: (dict) Optional dictionary containing GET parameters to be
        sent along with the API request, such as "timeout"
    :returns: (dict) A dict of metric data received in response of the query sent
    :raises:
        (RequestException) Raises an exception in case of a connection error
        (PrometheusApiClientException) Raises in case of non 200 response status code
    """
    start = round(start_time.timestamp())
    end = round(end_time.timestamp())
    params = params or {}
    data = None
    query = str(query)
    # using the query_range API to get raw data
    response = self._session.get(
        "{0}/api/v1/query_range".format(self.url),
        params={**{"query": query, "start": start, "end": end, "step": step}, **params},
        verify=self.ssl_verification,
        headers=self.headers,
    )
    if response.status_code == 200:
        data = response.json()["data"]["result"]
    else:
        raise PrometheusApiClientException(
            "HTTP Status Code {} ({!r})".format(response.status_code, response.content)
        )
    return data