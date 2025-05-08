import requests
import base64
from io import BytesIO
import logging
from typing import Dict, Any, Optional
from app.transcriber.base import BaseTranscriber

logger = logging.getLogger(__name__)

# Доступные модели OpenAI
OPENAI_MODELS = ["whisper-1"]

# Доступные форматы ответа
RESPONSE_FORMATS = ["json", "text", "srt", "verbose_json", "vtt"]

# Соответствие форматов транскрипции 
FORMAT_MAPPING = {
    "plain_text": "text",
    "formatted_text": "text",
    "srt": "srt",
    "vtt": "vtt"
}

class OpenAIWhisperTranscriber(BaseTranscriber):
    def __init__(self, api_key: str, model: str = "whisper-1"):
        self.api_key = api_key
        self.model = model
        
        logger.info(f"Инициализирован OpenAI Whisper транскрибер с моделью {model}")

    def _prepare_input_params(self, 
                            model: str = None, 
                            language: Optional[str] = None,
                            transcription_format: str = "plain_text",
                            response_format: str = None,
                            prompt: str = None,
                            temperature: float = 0,
                            **kwargs) -> Dict[str, Any]:
        """
        Подготавливает параметры для отправки в OpenAI API, совместимые с RunPod параметрами
        """
        # Используем модель из инициализации, если не указана иная
        use_model = model if model and model in OPENAI_MODELS else self.model
        
        # Преобразуем формат транскрипции RunPod в формат OpenAI
        if transcription_format in FORMAT_MAPPING:
            openai_format = FORMAT_MAPPING[transcription_format]
        else:
            openai_format = "text"
            
        # Предпочитаем явно указанный response_format, если он есть
        if response_format and response_format in RESPONSE_FORMATS:
            openai_format = response_format
        
        # Базовые параметры
        params = {
            "model": use_model,
            "response_format": openai_format,
            "temperature": temperature
        }
        
        # Добавляем язык, если указан
        if language:
            params["language"] = language
            
        # Добавляем prompt, если указан (из prompt или initial_prompt)
        if prompt:
            params["prompt"] = prompt
        elif "initial_prompt" in kwargs and kwargs["initial_prompt"]:
            params["prompt"] = kwargs["initial_prompt"]
            
        return params

    def transcribe(self, audio_url: str, **kwargs) -> dict:
        """
        Транскрибирует аудио по URL с поддержкой параметров OpenAI API
        
        Args:
            audio_url: URL аудиофайла
            **kwargs: Дополнительные параметры для транскрипции
                - model: Модель Whisper (whisper-1)
                - language: Язык аудио (автоопределение по умолчанию)
                - transcription_format: Формат транскрипции (plain_text, formatted_text, srt, vtt)
                - response_format: Формат ответа API (json, text, srt, verbose_json, vtt)
                - prompt: Подсказка для улучшения транскрипции
                - temperature: Температура сэмплирования (0-1)
                
        Returns:
            dict: Результат транскрипции
        """
        # Скачиваем аудио
        response = requests.get(audio_url)
        response.raise_for_status()
        audio_bytes = BytesIO(response.content)

        # Отправляем на транскрипцию
        return self._send_transcribe_request(audio_bytes, **kwargs)

    def transcribe_from_base64(self, audio_base64: str, **kwargs) -> dict:
        """
        Транскрибирует аудио из base64 строки с поддержкой параметров OpenAI API
        
        Args:
            audio_base64: Base64-кодированные аудио данные
            **kwargs: Дополнительные параметры для транскрипции
                - model: Модель Whisper (whisper-1)
                - language: Язык аудио (автоопределение по умолчанию)
                - transcription_format: Формат транскрипции (plain_text, formatted_text, srt, vtt)
                - response_format: Формат ответа API (json, text, srt, verbose_json, vtt)
                - prompt: Подсказка для улучшения транскрипции
                - temperature: Температура сэмплирования (0-1)
                
        Returns:
            dict: Результат транскрипции
        """
        # Удаляем префикс MIME-типа, если он есть
        if audio_base64.startswith('data:'):
            audio_base64 = audio_base64.split(',', 1)[1]
            
        # Декодируем base64 в байты
        audio_bytes = BytesIO(base64.b64decode(audio_base64))
        
        # Отправляем на транскрипцию
        return self._send_transcribe_request(audio_bytes, **kwargs)
    
    def _send_transcribe_request(self, audio_bytes: BytesIO, **kwargs) -> dict:
        """Общий метод для отправки запроса на транскрипцию в OpenAI API"""
        try:
            # Подготавливаем параметры запроса
            api_params = self._prepare_input_params(**kwargs)
            
            logger.info(f"Отправляем запрос на OpenAI Whisper API с параметрами: {api_params}")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }

            files = {
                "file": ("audio.mp3", audio_bytes, "audio/mpeg")
            }

            response = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                files=files,
                data=api_params
            )
            
            if response.status_code != 200:
                logger.error(f"OpenAI API вернул ошибку: {response.status_code}, {response.text}")
                raise ValueError(f"OpenAI Error: {response.status_code}, {response.text}")
                
            result = response.json()
            
            # Обрабатываем и возвращаем результат
            return self._format_response(result, api_params)
            
        except Exception as e:
            error_msg = f"Не удалось транскрибировать аудио через OpenAI Whisper: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _format_response(self, result: dict, params: dict) -> dict:
        """
        Форматирует ответ от OpenAI API в стандартный формат,
        совместимый с ответом RunPod для унификации интерфейса
        """
        # Транскрипция в формате простого текста
        if "text" in result:
            transcription = result["text"]
        else:
            transcription = ""
            
        # Определяем формат вывода
        output_format = params.get("response_format", "json")
            
        # Базовый ответ
        response = {
            "output": {
                "transcription": transcription,
                "model": params.get("model", self.model),
                "provider": "openai"
            },
            "status": "COMPLETED"
        }
        
        # Если в ответе есть дополнительные данные (например, segments в vtt формате),
        # добавляем их в output
        for key in result:
            if key != "text" and key not in response["output"]:
                response["output"][key] = result[key]
                
        # Если запрошен формат srt/vtt, добавляем его как исходный формат
        if output_format in ["srt", "vtt"]:
            response["output"]["raw_format"] = output_format
            
        return response
