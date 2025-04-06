import requests
from io import BytesIO
from app.transcriber.base import BaseTranscriber


class OpenAIWhisperTranscriber(BaseTranscriber):
    def __init__(self, api_key: str, model: str = "whisper-1", language: str = "auto"):
        self.api_key = api_key
        self.model = model
        self.language = language

    def transcribe(self, audio_url: str) -> dict:
        response = requests.get(audio_url)
        response.raise_for_status()
        audio_bytes = BytesIO(response.content)

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        files = {
            "file": ("audio.mp3", audio_bytes, "audio/mpeg")
        }

        data = {
            "model": self.model,
            "language": self.language
        }

        r = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers=headers,
            files=files,
            data=data
        )
        r.raise_for_status()

        return {
            "output": {
                "transcription": r.json().get("text", ""),
                "model": self.model,
                "provider": "openai"
            },
            "status": "COMPLETED"
        }
