import requests
import json

class IncidentIoClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def request(self, method: str, url: str, payload: dict) -> requests.Response:
        """
        Perform an HTTP request to the Incident.io API.
        """
        response = requests.request(method, url, headers=self.headers, data=json.dumps(payload))

        return response
