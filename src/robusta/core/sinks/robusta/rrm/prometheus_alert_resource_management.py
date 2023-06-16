from typing import Optional

from pydantic import BaseModel

from robusta.core.sinks.robusta.rrm.resource_state import ResourceState


class PrometheusAlertAnnotations(BaseModel):
    description: Optional[str]
    runbook_url: Optional[str]
    summary: Optional[str]


class PrometheusAlertLabels(BaseModel):
    severity: Optional[str]


class PrometheusAlertRule(BaseModel):
    alert: str
    annotations: Optional[PrometheusAlertAnnotations]
    expr: str
    duration: Optional[str]
    labels: Optional[PrometheusAlertLabels]

    @staticmethod
    def from_dict(data: dict):
        return PrometheusAlertRule(
            alert=data.get("alert"),
            annotations=data.get("annotations"),
            expr=data.get("expr"),
            duration=data.get("for"),
            labels=data.get("labels"),
        )

    def to_dict(self):
        result = self.dict()
        result["for"] = self.duration

        return result


class PrometheusAlertResourceState(ResourceState):
    rule: PrometheusAlertRule

    @staticmethod
    def from_dict(data: dict):
        rule = PrometheusAlertRule.from_dict(data.get("rule"))
        return PrometheusAlertResourceState(rule=rule)
