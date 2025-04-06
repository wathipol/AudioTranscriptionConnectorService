from app.config import config
from app.transcriber.runpod_connector import RunpodTranscriber
from app.transcriber.openai_connector import OpenAIWhisperTranscriber
from app.transcriber.base import BaseTranscriber


def get_transcriber() -> BaseTranscriber:
    """ Get transcriber based on application config """
    if config.use_openai:
        return OpenAIWhisperTranscriber(api_key=config.openai_api_key)
    else:
        return RunpodTranscriber(
            api_key=config.runpod_api_key,
            endpoint=config.runpod_api_url
        )
