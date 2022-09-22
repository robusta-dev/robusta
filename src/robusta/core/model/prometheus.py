import logging

from pydantic import BaseModel
from typing import List, Dict, Optional


"""
    Known returned string fields for PrometheusMetric
    __name__: the name of the outer function in prometheus 
    Known Optional string fields for PrometheusMetric
    [container, created_by_kind, created_by_name, endpoint, host_ip, host_network, instance, job, namespace, node, pod,
    pod_ip,,service, uid]
"""
PrometheusMetric = Dict[str, str]


class PrometheusScalarValue(BaseModel):
    """
        While usually this is a list of size 2 in the form of [float_timestamp, str_returned_value]
        the list size and return value types are not guaranteed
    """
    timestamp: float
    value: str

    RawScalarValue = list  # List[float, str]

    def __init__(self, raw_scalar: RawScalarValue):
        if len(raw_scalar) != 2:
            raise Exception(f"Invalid prometheus scalar value {raw_scalar}")
        timestamp = float(raw_scalar[0])
        value = str(raw_scalar[1])
        super().__init__(timestamp=timestamp, value=value)


class PrometheusVector(BaseModel):

    metric: PrometheusMetric
    value: PrometheusScalarValue


class PrometheusMatrix(BaseModel):
    metric: PrometheusMetric
    values: List[PrometheusScalarValue]

    def __init__(self, **kwargs):
        metric = kwargs.pop("metric", {})
        raw_values = kwargs.pop("values", None)
        if not raw_values:
            raise Exception("values missing")
        values = [PrometheusScalarValue(raw_value) for raw_value in raw_values]
        super().__init__(metric=metric, values=values)


class PrometheusQueryResult(BaseModel):
    """
        var: result_type can be of type "vector", "matrix", "scalar", "string" depending on the query
        If there is an issue with the return types not fitting this schema an exception will be thrown
    """
    result_type: str
    vector_result: Optional[List[PrometheusVector]]
    matrix_result: Optional[List[PrometheusMatrix]]
    scalar_result: Optional[PrometheusScalarValue]
    string_result: Optional[str]

    def __init__(self, data):
        logging.warning(f"{data}")
        result = data.get("result", None)
        result_type = data.get("resultType", None)
        vector_result = None
        matrix_result = None
        scalar_result = None
        string_result = None
        if not result_type:
            raise Exception("resultType missing")
        elif not result:
            raise Exception("result object missing")
        elif result_type == "string":
            string_result = str(result)
        elif result_type == "scalar":
            scalar_result = PrometheusScalarValue(**result)
        elif result_type == "vector" and isinstance(result, list):
            vector_result = [PrometheusVector(**vector_result) for vector_result in result]
        elif result_type == "matrix" and isinstance(result, list):
            matrix_result = [PrometheusMatrix(**matrix_result) for matrix_result in result]
        else:
            raise Exception("result or returnType is invalid")

        super().__init__(result_type=result_type,
                         vector_result=vector_result,
                         matrix_result=matrix_result,
                         scalar_result=scalar_result,
                         string_result=string_result)
