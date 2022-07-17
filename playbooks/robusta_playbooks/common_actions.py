from robusta.api import *


class FindingOverrides(ActionParams):
    """
    :var title: Overriding finding title.
    :var description: Overriding finding description.
    :var severity: Overriding finding severity. Allowed values: DEBUG, INFO, LOW, MEDIUM, HIGH
    :example severity: DEBUG
    """

    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None


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
    severity: Optional[FindingSeverity] = (
        FindingSeverity[params.severity] if params.severity else None
    )
    event.override_finding_attributes(params.title, params.description, severity)


class FindingFields(ActionParams):
    """
    :var title: Finding title. Title can be templated with name/namespace/kind/node of the resource, if applicable
    :var aggregation_key: Identifier of this finding
    :var description: Finding description. Description can be templated
    :var severity: Finding severity. Allowed values: DEBUG, INFO, LOW, MEDIUM, HIGH

    :example title: "Job $name on namespace $namespace failed"
    :example aggregation_key: "Job Failure"
    :example severity: DEBUG
    """

    title: str
    aggregation_key: str
    description: Optional[str] = None
    severity: Optional[str] = "HIGH"


@action
def create_finding(event: ExecutionBaseEvent, params: FindingFields):
    """
    Create a new finding.

    All messages from Robusta are represented as a Finding object.

    This action lets create a Finding that Robusta sends.

    """
    subject = event.get_subject()
    labels = defaultdict(lambda: "<missing>")
    labels.update({
        "name": subject.name,
        "kind": subject.subject_type,
        "namespace": subject.namespace if subject.namespace else "<missing>",
        "node": subject.node if subject.node else "<missing>",
    })

    event.add_finding(Finding(
        title=Template(params.title).safe_substitute(labels),
        description=Template(params.description).safe_substitute(labels) if params.description else None,
        aggregation_key=params.aggregation_key,
        severity=FindingSeverity.from_severity(params.severity),
        source=event.get_source(),
    ))