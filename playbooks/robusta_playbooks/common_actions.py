from robusta.api import *


class FindingOverrides(ActionParams):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None

    """
    :var title: Overriding finding title.
    :var description: Overriding finding description.
    :var severity: Overriding finding severity. Allowed values: DEBUG, INFO, LOW, MEDIUM, HIGH
    """


@action
def customise_finding(event: ExecutionBaseEvent, params: FindingOverrides):
    """
    Overrides a finding attribute with the provided value.

    All messages from Robusta are represented as a Finding object.
    This action lets you override Finding fields to change that messages Robusta sends.
    This lets you modify messages created by other actions without needing to rewrite those actions.

    This action does not create a new Finding, it just overrides the attributes of an existing Finding.
    It must be placed as the last action in the playbook configuration, to override the attributes created by previous
    actions
    """
    severity: Optional[FindingSeverity] = FindingSeverity[params.severity] if params.severity else None
    event.override_finding_attributes(
        params.title, params.description, severity
    )