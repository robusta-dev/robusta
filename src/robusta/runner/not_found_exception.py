from requests import RequestException


class NotFoundException(RequestException):
    """The resource was not found, and the operation could not be completed"""
