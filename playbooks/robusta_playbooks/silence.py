from uuid import UUID
from robusta.integrations.prometheus.utils import  AlertManagerDiscovery
from robusta.api import *

class Matcher(BaseModel):
    isEqual: bool
    isRegex: bool
    name: str
    value: str

class Silence(BaseModel):
    class silence_status(BaseModel):
        state: str

    id: UUID
    status: silence_status
    comment: str
    createdBy: str
    startsAt: datetime
    endsAt: datetime
    matchers: List[Matcher]

    def list(self) -> List[str]:
        return [str(self.id), self.status.state, self.comment, self.createdBy,
                self.startsAt.isoformat(timespec='seconds'), self.endsAt.isoformat(timespec='seconds'), " ".join(str(matcher) for matcher in self.matchers) ]
        

class GetSilenceParams(ActionParams):
    """
    :var alertmanager_url: Alternative Alert Manager url to send requests.
    """
    alertmanager_url: Optional[str]

class DeleteSilenceParams(ActionParams):
    """
    :var id: uuid of the silence.
    :var alertmanager_url: Alternative Alert Manager url to send requests.
    """
    id: str
    alertmanager_url: Optional[str]

class AddSilenceParams(ActionParams):
    """
    :var comment: uuid of the silence.
    :var created_by: uuid of the silence.
    :var starts_at: uuid of the silence.
    :var ends_at: uuid of the silence.
    :var matchers: List of matchers to filter the silence effect.
    :var alertmanager_url: Alternative Alert Manager url to send requests.
    """

    comment: str
    createdBy: str
    startsAt: datetime
    endsAt: datetime
    matchers: List[Matcher]
    alertmanager_url: Optional[str]

@action
def get_silences(event: ExecutionBaseEvent, params: GetSilenceParams):
    alertmanager_url = params.alertmanager_url if params.alertmanager_url else AlertManagerDiscovery.find_alert_manager_url()
    if alertmanager_url is None:
        return

    response = requests.get(
        f"{alertmanager_url}/api/v2/silences",
        headers={"Content-type": "application/json"},
    )

    if response.status_code not in [200, 201]:
        logging.error(response.json())
        return

    silence_list = [list(Silence(**silence).list()) for silence in response.json()]
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
    alertmanager_url = params.alertmanager_url if params.alertmanager_url else AlertManagerDiscovery.find_alert_manager_url()
    if alertmanager_url is None:
        return
    
    res = requests.post(
        f"{alertmanager_url}/api/v2/silences",
        data=params.json(),
        headers= {"Content-type": "application/json"},
    )         
    logging.info(res.json)
    return res.json()

@action
def delete_silence(event: ExecutionBaseEvent, params: DeleteSilenceParams):
    alertmanager_url = params.alertmanager_url if params.alertmanager_url else AlertManagerDiscovery.find_alert_manager_url()
    if alertmanager_url is None:
        return
    

    res=  requests.delete( 
        f"{alertmanager_url}/api/v2/silence/{params.id}",
        headers= {"Content-type": "application/json"},
    )
    logging.info(res.text())
    logging.info(res)
    logging.info(res.json)
    return