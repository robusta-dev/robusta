from robusta.api import *


class FindingOverrides(ActionParams):
    title: str = ""
    description: str = ""
    severity: str = ""

    """
    :var title: Overriding finding title.
    :var description: Overriding finding description.
    :var severity: Overriding finding severity. Allowed values: DEBUG, INFO, LOW, MEDIUM, HIGH
    """


@action
def customise_finding(event: ExecutionBaseEvent, params: FindingOverrides):
    """
    Overrides the created finding attribute with the provided attributes overrides.

    This action does not create a new Finding, it just override the attributes of an existing Finding.
    It must be placed as the last action in the playbook configuration, to override the attributes created by previous
    actions
    """
    severity: Optional[FindingSeverity] = FindingSeverity[params.severity] if params.severity else None
    event.override_finding_attributes(
        params.title, params.description, severity
    )