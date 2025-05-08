import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Header, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.downloader import download_audio_from_url, process_uploaded_file
from app.transcriber.registry import get_transcriber, get_transcriber_for_base64
from loguru import logger
from app.config import config
from typing import Optional, Dict, Any
from pydantic import BaseModel


# Модели для запросов API
class TranscriptionParams(BaseModel):
    # Опциональные параметры для транскрипции
    model: Optional[str] = None
    language: Optional[str] = None
    transcription_format: Optional[str] = "plain_text"
    translate: Optional[bool] = False
    enable_vad: Optional[bool] = True
    word_timestamps: Optional[bool] = False
    temperature: Optional[float] = 0.0
    
    # Дополнительные параметры
    response_format: Optional[str] = None
    prompt: Optional[str] = None
    initial_prompt: Optional[str] = None
    
    # Другие расширенные параметры
    best_of: Optional[int] = None
    beam_size: Optional[int] = None
    patience: Optional[float] = None
    length_penalty: Optional[float] = None
    suppress_tokens: Optional[str] = None
    condition_on_previous_text: Optional[bool] = None
    temperature_increment_on_fallback: Optional[float] = None
    compression_ratio_threshold: Optional[float] = None
    logprob_threshold: Optional[float] = None
    no_speech_threshold: Optional[float] = None


class TranscribeUrlRequest(TranscriptionParams):
    url: str


def verify_api_token(x_api_token: str = Header(default=None), request: Request = None):
    # Skip verification for demo client and root index
    if request and (request.url.path == '/' or request.url.path == '/index.html'):
        return
        
    if config.master_api_token is None:
        return  # If token is not set, skip verification

    if x_api_token != config.master_api_token:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API token")


app = FastAPI(dependencies=[Depends(verify_api_token)])
if config.setup_cors_middleware:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # или конкретные источники
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Jinja2 шаблоны
templates = Jinja2Templates(directory="app/templates")

# Статические файлы (CSS, JS)
app.mount("/static", StaticFiles(directory="./app/static"), name="static")


logger.info("Auth token is set: {}".format("✅" if config.master_api_token is not None else "❌"))
logger.info(f"INIT FASTAPI APP")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Рендерит главную страницу с интерфейсом транскрипции"""
    auth_required = config.master_api_token is not None
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "auth_required": auth_required,
            # Также передаем информацию о доступных моделях и форматах
            "runpod_models": ["tiny", "base", "small", "medium", "large-v1", "large-v2", "large-v3", "distil-large-v2", "distil-large-v3", "turbo"],
            "openai_models": ["whisper-1"],
            "transcription_formats": ["plain_text", "formatted_text", "srt", "vtt"]
        }
    )


@app.post("/transcribe/url")
async def transcribe_from_url(request: TranscribeUrlRequest):
    """
    Скачивает аудио с URL (например, YouTube) и сразу транскрибирует его
    с поддержкой дополнительных параметров.
    """
    try:
        url = request.url
        logger.info(f"Downloading and transcribing audio from URL: {url}")
        
        # Извлекаем все параметры из запроса в словарь
        kwargs = request.dict(exclude_unset=True)
        kwargs.pop("url", None)  # Удаляем URL из параметров
        
        # Убираем None значения для более чистого лога
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        
        # Логируем параметры транскрипции
        if kwargs:
            logger.info(f"Transcription parameters: {kwargs}")
        
        # Скачиваем аудио и получаем его в формате base64
        base64_audio = download_audio_from_url(url)
        
        # Транскрибируем аудио с дополнительными параметрами
        transcriber = get_transcriber_for_base64()
        result = transcriber.transcribe_from_base64(base64_audio, **kwargs)
        
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error transcribing from URL {url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transcribe/file")
async def transcribe_from_file(
    file: UploadFile = File(...),
    model: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    transcription_format: Optional[str] = Form("plain_text"),
    translate: Optional[bool] = Form(False),
    enable_vad: Optional[bool] = Form(True),
    word_timestamps: Optional[bool] = Form(False),
    temperature: Optional[float] = Form(0.0)
):
    """
    Принимает аудио/видео файл, обрабатывает его и сразу транскрибирует
    с поддержкой основных дополнительных параметров.
    """
    try:
        logger.info(f"Processing and transcribing uploaded file: {file.filename}")
        
        # Собираем все переданные параметры
        kwargs = {
            "model": model,
            "language": language,
            "transcription_format": transcription_format,
            "translate": translate,
            "enable_vad": enable_vad,
            "word_timestamps": word_timestamps,
            "temperature": temperature
        }
        
        # Убираем None значения
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        
        # Логируем параметры транскрипции
        if kwargs:
            logger.info(f"Transcription parameters: {kwargs}")
        
        # Читаем содержимое файла
        contents = await file.read()
        
        # Обрабатываем файл и получаем аудио в формате base64
        base64_audio = process_uploaded_file(contents, file.filename)
        
        # Транскрибируем аудио с дополнительными параметрами
        transcriber = get_transcriber_for_base64()
        result = transcriber.transcribe_from_base64(base64_audio, **kwargs)
        
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error transcribing file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
