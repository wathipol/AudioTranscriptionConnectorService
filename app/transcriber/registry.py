from app.config import config
from app.transcriber.base import BaseTranscriber
from app.transcriber.runpod_connector import RunpodTranscriber
from app.transcriber.openai_connector import OpenAIWhisperTranscriber
import logging

logger = logging.getLogger(__name__)

def get_transcriber() -> BaseTranscriber:
    """
    Возвращает экземпляр транскрибера на основе настроек конфигурации.
    """
    if config.use_openai:
        logger.info("Using OpenAI Whisper transcriber")
        return OpenAIWhisperTranscriber(api_key=config.openai_api_key)
    else:
        logger.info("Using RunPod Faster-Whisper transcriber")
        return RunpodTranscriber(api_key=config.runpod_api_key, endpoint=config.runpod_api_url)

def get_transcriber_for_base64() -> BaseTranscriber:
    """
    Возвращает транскрибер для работы с base64 аудио.
    RunPod может работать с base64, но если возникнут проблемы, 
    в самом транскрибере есть логика переключения на OpenAI.
    """
    # Используем тот же транскрибер, что указан в настройках
    if config.use_openai:
        logger.info("Using OpenAI Whisper transcriber for base64 audio")
        return OpenAIWhisperTranscriber(api_key=config.openai_api_key)
    else:
        logger.info("Using RunPod Faster-Whisper transcriber for base64 audio")
        return RunpodTranscriber(api_key=config.runpod_api_key, endpoint=config.runpod_api_url)
