from enum import Enum
from typing import Optional


class ErrorCodes(Enum):
    ILLEGAL_TIMESTAMP = 4500
    NO_SIGNING_KEY = 4501
    SIGNATURE_MISMATCH = 4502
    MISSING_AUTH_INPUT = 4503
    MISSING_PRIVATE_KEY = 4504
    AUTH_VALIDATION_FAILED = 4505
    BAD_SIGNING_KEY = 4506
    KEY_VALIDATION_FAILED = 4507

    ACTION_NOT_REGISTERED = 4600
    EXECUTION_EVENT_MISMATCH = 4601
    PARAMS_INSTANTIATION_FAILED = 4602
    ACTION_NOT_FOUND = 4603
    NOT_EXTERNAL_ACTION = 4604
    EVENT_PARAMS_INSTANTIATION_FAILED = 4605
    EVENT_INSTANTIATION_FAILED = 4606
    UNAUTHORIZED_LIGHT_ACTION = 4607

    ACTION_UNEXPECTED_ERROR = 4700
    RESOURCE_NOT_SUPPORTED = 4701
    RESOURCE_NOT_FOUND = 4702

    ALERT_MANAGER_DISCOVERY_FAILED = 5000
    ALERT_MANAGER_REQUEST_FAILED = 5001
    ADD_SILENCE_FAILED = 5002


class ActionException(Exception):
    def __init__(self, error: ErrorCodes, msg: Optional[str] = None):
        super().__init__(msg)
        self.msg: Optional[str] = msg
        self.code: int = error.value
        self.type: str = error.name
