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

    alertmanager_flavor: str = None
    alertmanager_url: Optional[str]
    grafana_api_key: str = None


class DeleteSilenceParams(BaseSilenceParams):
    """
    :var id: uuid of the silence.
    """

    id: str


class AddSilenceParams(BaseSilenceParams):
    """
    :var id: uuid of the silence. use for update, empty on create.
    :var comment: text comment of the silence.
    :var createdBy: author of the silence.
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
    alertmanager_url = _get_alertmanager_url(params)
    if alertmanager_url is None:
        return

    response = requests.get(
        f"{alertmanager_url}{_get_url_path(SilenceOperation.LIST, params)}",
        headers=_gen_headers(params),
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
    alertmanager_url = _get_alertmanager_url(params)
    if alertmanager_url is None:
        return

    res = requests.post(
        f"{alertmanager_url}{_get_url_path(SilenceOperation.CREATE, params)}",
        data=params.json(),
        headers=_gen_headers(params),
    )

    res.raise_for_status()
    silence_id = res.json().get("silenceID") or res.json().get("id")  # on grafana alertmanager the 'id' is returned
    if not silence_id:
        return

    event.add_enrichment(
        [
            TableBlock(
                rows=[[silence_id]],
                headers=["id"],
                table_name="New Silence",
            ),
        ]
    )


@action
def delete_silence(event: ExecutionBaseEvent, params: DeleteSilenceParams):
    alertmanager_url = _get_alertmanager_url(params)
    if alertmanager_url is None:
        return

    res = requests.delete(
        f"{alertmanager_url}{_get_url_path(SilenceOperation.DELETE, params)}/{params.id}",
        headers=_gen_headers(params),
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


SilenceOperation = Enum("SilenceOperation", "CREATE DELETE LIST")


def _gen_headers(params: BaseSilenceParams) -> Dict:
    headers = {"Content-type": "application/json"}
    if params.grafana_api_key:
        headers.update({"Authorization": "Bearer {0}".format(params.grafana_api_key)})
    return headers


def _get_url_path(operation: SilenceOperation, params: BaseSilenceParams) -> str:
    prefix = ""
    if "grafana" == params.alertmanager_flavor:
        prefix = "/api/alertmanager/grafana"

    if operation == SilenceOperation.DELETE:
        return f"{prefix}/api/v2/silence"
    else:
        return f"{prefix}/api/v2/silences"


def _get_alertmanager_url(params: BaseSilenceParams) -> str:
    if params.alertmanager_url:
        return params.alertmanager_url

    if "grafana" == params.alertmanager_flavor:
        return ServiceDiscovery.find_url(
            selectors=["app.kubernetes.io/name=grafana"], error_msg="Failed to find grafana url"
        )

    return AlertManagerDiscovery.find_alert_manager_url()
