import requests
from app.transcriber.base import BaseTranscriber


class RunpodTranscriber(BaseTranscriber):
    def __init__(self, api_key: str, endpoint: str):
        self.api_key = api_key
        self.endpoint = endpoint

    def transcribe(self, audio_url: str) -> dict:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        data = {
            'input': {"audio": audio_url}
        }

        response = requests.post(self.endpoint, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
