import json
from http import HTTPStatus

import requests

from ...core.reporting.base import *


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    PUT = "PUT"
    DELETE = "DELETE"


_MAPPER_TYPE_TO_METHOD = {
    HttpMethod.GET: requests.get,
    HttpMethod.POST: requests.post,
    HttpMethod.PATCH: requests.patch,
    HttpMethod.DELETE: requests.delete,
    HttpMethod.PUT: requests.put
}


def map_type_to_method(http_type: HttpMethod):
    try:
        return _MAPPER_TYPE_TO_METHOD[http_type]
    except KeyError:
        raise ValueError("Wrong http method provided!")


def check_response_succeed(response):
    return response and response.status_code in [
        HTTPStatus.OK,
        HTTPStatus.CREATED,
    ]


def process_request(url: str, method: HttpMethod, **kwargs) \
        -> requests.Response:
    """
    Function to abort request if request to external
    uri was not successful or if there were any
    connection errors (then returns 503 Service Unavailable)
    :param url: external API URI
    :type url: str
    :param method: HTTP method to send (GET, POST etc)
    :type method: HttpMethod
    :param kwargs: parameters to request (headers, params, body etc)
    :type kwargs: dict
    :return: response
    :rtype: requests.Response
    """
    try:
        http_method = map_type_to_method(method)
        logging.debug(f"Try to proceed {method.name} request to {url}")
        response = http_method(url, **kwargs)
        response.raise_for_status()
    except requests.RequestException as e:
        response = e.response
        logging.error(f"Error while {method.name} request to {url}")
        logging.exception(e)
        if response:
            logging.error(json.dumps(response.json()), exc_info=True)

    return response
