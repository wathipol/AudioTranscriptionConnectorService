import requests
import base64
import json
import logging
import tempfile
import os
import shutil
from app.transcriber.base import BaseTranscriber
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Максимальный размер файла для отправки (2.5 МБ в base64)
MAX_AUDIO_FILE_SIZE = 2 * 1024 * 1024  # 2 МБ

# Доступные модели RunPod
RUNPOD_MODELS = [
    "tiny", "base", "small", "medium", 
    "large-v1", "large-v2", "large-v3", 
    "distil-large-v2", "distil-large-v3", "turbo"
]

# Доступные форматы транскрипции
TRANSCRIPTION_FORMATS = ["plain_text", "formatted_text", "srt", "vtt"]

class RunpodTranscriber(BaseTranscriber):
    def __init__(self, api_key: str, endpoint: str):
        self.api_key = api_key
        self.endpoint = endpoint
        
        # Проверяем, что endpoint не заканчивается на /run или /runsync
        if self.endpoint.endswith('/run'):
            self.endpoint = self.endpoint[:-4]
        elif self.endpoint.endswith('/runsync'):
            self.endpoint = self.endpoint[:-8]
            
        # Добавляем /runsync для синхронного запроса
        self.runsync_endpoint = f"{self.endpoint}/runsync"
        
        logger.info(f"RunPod endpoint: {self.endpoint}, runsync: {self.runsync_endpoint}")
    
    def _prepare_input_params(self, 
                            model: str = "large-v3", 
                            language: Optional[str] = None,
                            transcription_format: str = "plain_text",
                            translate: bool = False,
                            enable_vad: bool = True,
                            word_timestamps: bool = False,
                            **kwargs) -> Dict[str, Any]:
        """
        Подготавливает параметры для отправки в RunPod API
        """
        # Проверяем валидность параметров
        if model not in RUNPOD_MODELS:
            logger.warning(f"Модель {model} не найдена в списке доступных моделей RunPod. Используем large-v3.")
            model = "large-v3"
            
        if transcription_format not in TRANSCRIPTION_FORMATS:
            logger.warning(f"Формат транскрипции {transcription_format} не поддерживается. Используем plain_text.")
            transcription_format = "plain_text"
        
        # Базовые параметры
        params = {
            "model": model,
            "transcription": transcription_format,
            "enable_vad": enable_vad,
            "word_timestamps": word_timestamps
        }
        
        # Добавляем язык, если указан
        if language:
            params["language"] = language
            
        # Добавляем параметры перевода, если включен
        if translate:
            params["translate"] = True
            params["translation"] = kwargs.get("translation_format", "plain_text")
            
        # Добавляем дополнительные параметры для продвинутых пользователей
        advanced_params = [
            "temperature", "best_of", "beam_size", "patience", 
            "length_penalty", "suppress_tokens", "initial_prompt",
            "condition_on_previous_text", "temperature_increment_on_fallback",
            "compression_ratio_threshold", "logprob_threshold", "no_speech_threshold"
        ]
        
        for param in advanced_params:
            if param in kwargs and kwargs[param] is not None:
                params[param] = kwargs[param]
                
        return params

    def transcribe(self, audio_url: str, **kwargs) -> dict:
        """
        Транскрибирует аудио по URL с поддержкой дополнительных параметров
        
        Args:
            audio_url: URL аудиофайла
            **kwargs: Дополнительные параметры для транскрипции
                - model: Модель Whisper (tiny, base, small, medium, large-v1, large-v2, large-v3, и т.д.)
                - language: Язык аудио (автоопределение по умолчанию)
                - transcription_format: Формат транскрипции (plain_text, formatted_text, srt, vtt)
                - translate: Перевести аудио на английский (true/false)
                - enable_vad: Использовать VAD для фильтрации тишины (true/false)
                - word_timestamps: Включить временные метки для слов (true/false)
                
        Returns:
            dict: Результат транскрипции
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': self.api_key  # Без префикса Bearer!
        }
        
        # Подготавливаем параметры
        input_params = self._prepare_input_params(**kwargs)
        input_params["audio"] = audio_url
        
        # Структура запроса
        data = {
            'input': input_params
        }

        logger.info(f"Отправляем запрос на RunPod с URL: {audio_url[:50]}...")
        logger.debug(f"Параметры запроса: {json.dumps(input_params, indent=2)}")
        
        # Увеличиваем таймаут для больших файлов
        try:
            response = requests.post(
                self.runsync_endpoint, 
                headers=headers, 
                json=data,
                timeout=300  # 5 минут таймаут
            )
            
            if response.status_code != 200:
                logger.error(f"RunPod API вернул ошибку: {response.status_code}, {response.text}")
                raise ValueError(f"RunPod Error: {response.status_code}, {response.text}")
                
            result = response.json()
            return self._format_response(result)
            
        except requests.exceptions.Timeout:
            logger.error("Таймаут при запросе к RunPod API")
            raise ValueError("Таймаут при запросе к RunPod API")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к RunPod API: {str(e)}")
            raise ValueError(f"Ошибка запроса к RunPod API: {str(e)}")
        
    def transcribe_from_base64(self, audio_base64: str, **kwargs) -> dict:
        """
        Транскрибирует аудио из base64 строки с поддержкой дополнительных параметров
        
        Args:
            audio_base64: Base64-кодированные аудио данные
            **kwargs: Дополнительные параметры для транскрипции
                - model: Модель Whisper (tiny, base, small, medium, large-v1, large-v2, large-v3, и т.д.)
                - language: Язык аудио (автоопределение по умолчанию)
                - transcription_format: Формат транскрипции (plain_text, formatted_text, srt, vtt)
                - translate: Перевести аудио на английский (true/false)
                - enable_vad: Использовать VAD для фильтрации тишины (true/false)
                - word_timestamps: Включить временные метки для слов (true/false)
                
        Returns:
            dict: Результат транскрипции
        """
        try:
            # RunPod API ожидает чистую base64 строку без префиксов
            if audio_base64.startswith('data:'):
                audio_base64 = audio_base64.split(',', 1)[1]
            
            # Для больших файлов - разбиваем на части
            if len(audio_base64) > MAX_AUDIO_FILE_SIZE:
                logger.info(f"Файл слишком большой для прямой отправки: {len(audio_base64)} байт")
                return self._transcribe_large_audio(audio_base64, **kwargs)
                
            headers = {
                'Content-Type': 'application/json',
                'Authorization': self.api_key  # Без префикса Bearer!
            }
            
            # Подготавливаем параметры
            input_params = self._prepare_input_params(**kwargs)
            input_params["audio_base64"] = audio_base64
            
            # Структура запроса
            data = {
                'input': input_params
            }
            
            logger.info(f"Отправляем запрос на RunPod API с base64. Длина: {len(audio_base64)} байт")
            logger.info(f"Endpoint: {self.runsync_endpoint}")
            logger.debug(f"Параметры запроса: {json.dumps({k: v for k, v in input_params.items() if k != 'audio_base64'}, indent=2)}")
            
            # Используем runsync endpoint с увеличенным таймаутом
            response = requests.post(
                self.runsync_endpoint, 
                headers=headers, 
                json=data,
                timeout=300  # 5 минут таймаут
            )
            
            if response.status_code != 200:
                logger.error(f"RunPod API вернул статус: {response.status_code}. Тело: {response.text}")
                raise ValueError(f"RunPod Error: {response.status_code}, Body: {response.text}")
            
            result = response.json()
            logger.info(f"Получен ответ от RunPod API: {str(result)[:200]}...")
            
            return self._format_response(result)
            
        except requests.exceptions.Timeout:
            logger.error("Таймаут при запросе к RunPod API")
            raise ValueError("Таймаут при запросе к RunPod API")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ошибка соединения с RunPod API: {str(e)}")
            raise ValueError(f"Ошибка соединения с RunPod API: {str(e)}")
        except Exception as e:
            error_msg = f"Не удалось транскрибировать аудио через RunPod: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
    def _transcribe_large_audio(self, audio_base64: str, **kwargs) -> dict:
        """Обрабатывает большие аудиофайлы, сохраняя их во временный файл"""
        temp_dir = tempfile.mkdtemp()
        audio_file = os.path.join(temp_dir, "audio.mp3")
        
        try:
            # Декодируем base64 и сохраняем во временный файл
            audio_data = base64.b64decode(audio_base64)
            with open(audio_file, 'wb') as f:
                f.write(audio_data)
                
            logger.info(f"Сохранен временный файл размером {len(audio_data)} байт")
            
            # Так как у нас нет возможности загрузить файл, используем локальное транскрибирование
            # и сегментирование аудио
            transcription = self._transcribe_file_in_chunks(audio_file, **kwargs)
            
            return {
                "output": {
                    "transcription": transcription,
                    "model": kwargs.get("model", "large-v3"),
                    "provider": "runpod"
                },
                "status": "COMPLETED"
            }
        
        finally:
            # Удаляем временную директорию
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    def _transcribe_file_in_chunks(self, audio_file: str, **kwargs) -> str:
        """Транскрибирует большой аудиофайл по частям с помощью ffmpeg"""
        import subprocess
        from pathlib import Path
        
        # Создаем временную директорию для частей
        temp_dir = tempfile.mkdtemp()
        chunks_pattern = os.path.join(temp_dir, "chunk_%03d.mp3")
        
        try:
            # Разбиваем файл на 15-секундные части
            cmd = [
                "ffmpeg", "-y",
                "-i", audio_file,
                "-f", "segment",
                "-segment_time", "15",
                "-c", "copy",
                chunks_pattern
            ]
            
            result = subprocess.run(cmd, capture_output=True, check=False)
            if result.returncode != 0:
                logger.error(f"Ошибка разбиения файла: {result.stderr.decode()}")
                # Если не удалось разбить, просто отрезаем первые 30 секунд
                cmd = [
                    "ffmpeg", "-y",
                    "-i", audio_file,
                    "-t", "30",  # Первые 30 секунд
                    "-acodec", "copy",
                    os.path.join(temp_dir, "chunk_small.mp3")
                ]
                result = subprocess.run(cmd, capture_output=True, check=False)
                chunks = [os.path.join(temp_dir, "chunk_small.mp3")]
            else:
                # Получаем список всех чанков, отсортированных по имени
                chunks = sorted([str(f) for f in Path(temp_dir).glob("chunk_*.mp3")])
            
            logger.info(f"Файл разбит на {len(chunks)} частей")
            
            # Транскрибируем каждую часть
            transcriptions = []
            
            # Подготавливаем базовые параметры
            input_params = self._prepare_input_params(**kwargs)
            
            for i, chunk in enumerate(chunks):
                # Проверяем, что файл существует и не пустой
                if not os.path.exists(chunk) or os.path.getsize(chunk) == 0:
                    continue
                    
                logger.info(f"Транскрибируем часть {i+1}/{len(chunks)}: {chunk}")
                
                # Считываем данные и конвертируем в base64
                with open(chunk, 'rb') as f:
                    chunk_data = f.read()
                    chunk_base64 = base64.b64encode(chunk_data).decode('utf-8')
                
                # Транскрибируем через RunPod API
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': self.api_key
                }
                
                # Копируем параметры и добавляем audio_base64
                chunk_params = input_params.copy()
                chunk_params["audio_base64"] = chunk_base64
                
                data = {
                    'input': chunk_params
                }
                
                try:
                    response = requests.post(
                        self.runsync_endpoint, 
                        headers=headers, 
                        json=data,
                        timeout=60  # 1 минута для каждой части
                    )
                    
                    if response.status_code != 200:
                        logger.warning(f"Ошибка транскрибирования части {i+1}: {response.text}")
                        continue
                        
                    result = response.json()
                    chunk_transcription = self._extract_text_from_result(result)
                    transcriptions.append(chunk_transcription)
                    
                except Exception as e:
                    logger.warning(f"Ошибка транскрибирования части {i+1}: {str(e)}")
                    continue
            
            # Объединяем все транскрипции
            return " ".join(transcriptions)
            
        finally:
            # Удаляем временные файлы
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    def _extract_text_from_result(self, result: dict) -> str:
        """Извлекает текст транскрипции из результата RunPod API"""
        if 'output' in result:
            output = result['output']
            
            if 'transcription' in output:
                return output['transcription']
                
            if 'segments' in output and isinstance(output['segments'], list):
                return " ".join([
                    segment.get('text', '') 
                    for segment in output['segments'] 
                    if 'text' in segment
                ])
                
        return ""
            
    def _format_response(self, result: dict) -> dict:
        """Форматирует ответ от RunPod API в стандартный формат"""
        # Если есть ошибка, выбрасываем исключение
        if 'error' in result:
            raise ValueError(f"RunPod API вернул ошибку: {result['error']}")
            
        # Если есть выходные данные
        if 'output' in result:
            output = result['output']
            
            # Ищем транскрипцию
            transcription = self._extract_text_from_result(result)
            
            # Базовый ответ
            response = {
                "output": {
                    "transcription": transcription,
                    "model": output.get('model', 'large-v3'),
                    "provider": "runpod"
                },
                "status": "COMPLETED"
            }
            
            # Добавляем дополнительные поля, если они есть (перевод, сегменты со временными метками и т.д.)
            if 'segments' in output and isinstance(output['segments'], list):
                response["output"]["segments"] = output['segments']
                
            if 'translation' in output and output['translation']:
                response["output"]["translation"] = output['translation']
                
            if 'detected_language' in output:
                response["output"]["detected_language"] = output['detected_language']
                
            return response
            
        # Если нет ни ошибки, ни выходных данных
        return {
            "output": {
                "transcription": "",
                "model": "large-v3",
                "provider": "runpod"
            },
            "status": "FAILED"
        }
