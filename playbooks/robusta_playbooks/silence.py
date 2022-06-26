from robusta.integrations.prometheus.utils import AlertManagerDiscovery
from robusta.api import *


class Matcher(BaseModel):
    # https://github.com/prometheus/alertmanager/blob/main/api/v2/models/matcher.go
    isEqual: bool
    isRegex: bool
    name: str
    value: str


class SilenceStatus(BaseModel):
    # https://github.com/prometheus/alertmanager/blob/main/api/v2/models/silence_status.go
    state: str


class Silence(BaseModel):
    # https://github.com/prometheus/alertmanager/blob/main/api/v2/models/silence.go
    id: UUID
    status: SilenceStatus
    comment: str
    createdBy: str
    startsAt: datetime
    endsAt: datetime
    matchers: List[Matcher]

    def to_list(self) -> List[str]:
        return [
            str(self.id),
            self.status.json(),
            self.comment,
            self.createdBy,
            self.startsAt.isoformat(timespec="seconds"),
            self.endsAt.isoformat(timespec="seconds"),
            json.dumps([matcher.dict() for matcher in self.matchers]),
        ]


class BaseSilenceParams(ActionParams):
    """
    :var alertmanager_url: Alternative Alert Manager url to send requests.
    """

    alertmanager_url: Optional[str]


class DeleteSilenceParams(BaseSilenceParams):
    """
    :var id: uuid of the silence.
    """

    id: str


class AddSilenceParams(BaseSilenceParams):
    """
    :var id: uuid of the silence. use for update, empty on create.
    :var comment: text comment of the silence.
    :var created_by: author of the silence.
    :var startsAt: date.
    :var endsAt: date.
    :var matchers: List of matchers to filter the silence effect.
    """

    id: Optional[str]
    comment: str
    createdBy: str
    startsAt: datetime
    endsAt: datetime
    matchers: List[Matcher]


@action
def get_silences(event: ExecutionBaseEvent, params: BaseSilenceParams):
    alertmanager_url = (
        params.alertmanager_url
        if params.alertmanager_url
        else AlertManagerDiscovery.find_alert_manager_url()
    )
    if alertmanager_url is None:
        return

    response = requests.get(
        f"{alertmanager_url}/api/v2/silences",
        headers={"Content-type": "application/json"},
    )

    response.raise_for_status()

    silence_list = [(Silence(**silence).to_list()) for silence in response.json()]
    if len(silence_list) == 0:
        event.add_enrichment([MarkdownBlock("*There are no silences*")])
        return

    event.add_enrichment(
        [
            TableBlock(
                rows=silence_list,
                headers=[*Silence.__fields__],
                table_name="Silences",
            ),
        ]
    )


@action
def add_silence(event: ExecutionBaseEvent, params: AddSilenceParams):
    alertmanager_url = (
        params.alertmanager_url
        if params.alertmanager_url
        else AlertManagerDiscovery.find_alert_manager_url()
    )
    if alertmanager_url is None:
        return

    res = requests.post(
        f"{alertmanager_url}/api/v2/silences",
        data=params.json(),
        headers={"Content-type": "application/json"},
    )

    res.raise_for_status()
    if not res.json()["silenceID"]:
        return

    event.add_enrichment(
        [
            TableBlock(
                rows=[[res.json()["silenceID"]]],
                headers=["id"],
                table_name="New Silence",
            ),
        ]
    )


@action
def delete_silence(event: ExecutionBaseEvent, params: DeleteSilenceParams):
    alertmanager_url = (
        params.alertmanager_url
        if params.alertmanager_url
        else AlertManagerDiscovery.find_alert_manager_url()
    )
    if alertmanager_url is None:
        return

    res = requests.delete(
        f"{alertmanager_url}/api/v2/silence/{params.id}",
        headers={"Content-type": "application/json"},
    )

    res.raise_for_status()
    event.add_enrichment(
        [
            TableBlock(
                rows=[[params.id]],
                headers=["id"],
                table_name="Deleted Silence",
            ),
        ]
    )
