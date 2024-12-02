from urllib.parse import urljoin

class AlertEventsApi:
    """
    Class to interact with the incident.io alert events API.
    https://api-docs.incident.io/tag/Alert-Events-V2
    """
    
    # API Endpoint
    _endpoint = 'alert_events/http'

    def __init__ (self, base_url: str, source_config_id: str):
        self.base_url = base_url
        self.source_config_id = source_config_id

    def build_url(self) -> str:
        """
        Build the full URL for the change_events API.
        """
        return urljoin(self.base_url, f'{self._endpoint}/{self.source_config_id}')
    