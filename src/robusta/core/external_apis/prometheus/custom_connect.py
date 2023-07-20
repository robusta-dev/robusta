from typing import Any, Dict, Optional

import requests
from botocore.auth import *
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
from prometheus_api_client.exceptions import PrometheusApiClientException
from prometheus_api_client.prometheus_connect import PrometheusConnect

from robusta.core.external_apis.prometheus.models import PrometheusQueryResult
from robusta.core.model.base_params import PrometheusParams


class AWSPrometheusConnect(PrometheusConnect):
    def __init__(self, access_key: str, secret_key: str, region: str, service_name: str, **kwargs):
        super().__init__(**kwargs)
        self._credentials = Credentials(access_key, secret_key)
        self._sigv4auth = S3SigV4Auth(self._credentials, service_name, region)

    def signed_request(self, method, url, data=None, params=None, verify=False, headers=None):
        request = AWSRequest(method=method, url=url, data=data, params=params, headers=headers)
        self._sigv4auth.add_auth(request)
        return requests.request(method=method, url=url, headers=dict(request.headers), verify=verify, data=data)

    def custom_query(self, query: str, params: dict = None):
        """
        Send a custom query to a Prometheus Host.

        This method takes as input a string which will be sent as a query to
        the specified Prometheus Host. This query is a PromQL query.

        :param query: (str) This is a PromQL query, a few examples can be found
            at https://prometheus.io/docs/prometheus/latest/querying/examples/
        :param params: (dict) Optional dictionary containing GET parameters to be
            sent along with the API request, such as "time"
        :returns: (list) A list of metric data received in response of the query sent
        :raises:
            (RequestException) Raises an exception in case of a connection error
            (PrometheusApiClientException) Raises in case of non 200 response status code
        """
        params = params or {}
        data = None
        query = str(query)
        # using the query API to get raw data
        response = self.signed_request(
            method="POST",
            url="{0}/api/v1/query".format(self.url),
            data={**{"query": query}, **params},
            params={},
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

    def custom_query_range(
        self,
        prometheus_params: PrometheusParams,
        query: str,
        start_time: datetime,
        end_time: datetime,
        step: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> PrometheusQueryResult:
        """
        Send a query_range to a Prometheus Host.
        This method takes as input a string which will be sent as a query to
        the specified Prometheus Host. This query is a PromQL query.
        :param query: (str) This is a PromQL query, a few examples can be found
            at https://prometheus.io/docs/prometheus/latest/querying/examples/
        :param start_time: (datetime) A datetime object that specifies the query range start time.
        :param end_time: (datetime) A datetime object that specifies the query range end time.
        :param step: (str) Query resolution step width in duration format or float number of seconds - i.e 100s, 3d, 2w, 170.3
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

        prometheus_result = None
        query = str(query)
        response = self.signed_request(
            method="POST",
            url="{0}/api/v1/query_range".format(self.url),
            data={**{"query": query, "start": start, "end": end, "step": step}, **params},
            params={},
            headers=self.headers,
        )
        if response.status_code == 200:
            prometheus_result = PrometheusQueryResult(data=response.json()["data"])
        else:
            raise PrometheusApiClientException(
                "HTTP Status Code {} ({!r})".format(response.status_code, response.content)
            )
        return prometheus_result
