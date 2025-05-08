import base64
import logging
import shutil
from pathlib import Path
import subprocess
import tempfile
import os
import uuid

import yt_dlp
from app.config import config

logger = logging.getLogger(__name__)

# Определяем поддерживаемые расширения
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mkv", ".mov"}


def download_audio_from_url(url: str) -> str:
    """
    Скачивает аудио с URL (например, YouTube) и возвращает его в формате base64
    """
    temp_dir = tempfile.mkdtemp()
    temp_file_name = os.path.join(temp_dir, "audio")
    
    try:
        # Сначала скачиваем лучшее аудио без постобработки
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': temp_file_name,
            # Отключаем постобработку - сами сделаем конвертацию через ffmpeg
            'postprocessors': [],
            'noplaylist': True,
            'quiet': False,
            'no_warnings': False,
            'retries': 5,
            'fragment_retries': 5,
            'nocheckcertificate': True,
            'ignoreerrors': False
        }
        
        # Добавляем прокси, если указан
        if config.proxy:
            ydl_opts['proxy'] = config.proxy
        
        # Настраиваем User-Agent
        ydl_opts['http_headers'] = {
            'User-Agent': config.user_agent
        }
        
        # Добавляем cookies, если файл указан
        if config.cookies_file and os.path.exists(config.cookies_file):
            ydl_opts['cookiefile'] = config.cookies_file

        # Скачиваем файл с YouTube
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            if not info:
                raise ValueError("Не удалось получить информацию о видео")
                
            # Получаем путь к скачанному файлу
            if 'requested_downloads' in info and info['requested_downloads']:
                downloaded_file = info['requested_downloads'][0]['filepath']
            else:
                # Находим любые скачанные файлы
                downloaded_files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir)]
                if not downloaded_files:
                    raise ValueError("Не удалось найти скачанный файл")
                downloaded_file = downloaded_files[0]
        
        logger.info(f"Файл скачан: {downloaded_file}")
        
        # Теперь конвертируем скачанный файл в mp3 через ffmpeg напрямую
        output_file = os.path.join(temp_dir, "audio.mp3")
        
        # Запускаем ffmpeg для конвертации без ffprobe
        cmd = [
            "ffmpeg", "-y",
            "-i", downloaded_file,
            "-vn",                      # Убираем видео
            "-acodec", "libmp3lame",    # Используем mp3 кодек
            "-ab", "192k",              # Битрейт
            "-ar", "44100",             # Частота дискретизации
            "-ac", "2",                 # Два канала (стерео)
            "-f", "mp3",                # Формат файла
            output_file
        ]
        
        logger.info(f"Запускаем конвертацию: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        
        if result.returncode != 0:
            error = result.stderr.decode()
            logger.error(f"Ошибка ffmpeg: {error}")
            raise ValueError(f"Ошибка конвертации аудио: {error}")
            
        # Проверяем, что файл создан
        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            raise ValueError("Файл не был создан или пустой")
            
        # Читаем файл и конвертируем в base64
        with open(output_file, 'rb') as f:
            audio_data = f.read()
            base64_audio = base64.b64encode(audio_data).decode('utf-8')
            
        return base64_audio
        
    except Exception as e:
        logger.error(f"[download_audio_from_url] Ошибка: {e}")
        raise ValueError(f"Не удалось скачать аудио: {e}")
    finally:
        # Удаляем временную директорию со всеми файлами
        shutil.rmtree(temp_dir, ignore_errors=True)


def process_uploaded_file(file_data: bytes, filename: str) -> str:
    """
    Обрабатывает загруженный аудио/видео файл и возвращает аудио в формате base64
    """
    suffix = Path(filename).suffix.lower()
    temp_dir = tempfile.mkdtemp()
    input_file = os.path.join(temp_dir, f"input{suffix}")
    output_file = os.path.join(temp_dir, "output.mp3")
    
    try:
        # Сохраняем входной файл
        with open(input_file, 'wb') as f:
            f.write(file_data)
        
        if suffix in AUDIO_EXTENSIONS or suffix in VIDEO_EXTENSIONS:
            # Конвертируем файл в mp3
            cmd = [
                "ffmpeg", "-y", 
                "-i", input_file,
                "-vn",                      # Убираем видео
                "-acodec", "libmp3lame",    # Используем mp3 кодек
                "-ab", "192k",              # Битрейт
                "-ar", "44100",             # Частота дискретизации
                "-ac", "2",                 # Два канала (стерео)
                "-f", "mp3",                # Формат файла
                output_file
            ]
            
            logger.info(f"Запускаем конвертацию: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )
            
            if result.returncode != 0:
                error = result.stderr.decode()
                logger.error(f"Ошибка ffmpeg: {error}")
                raise ValueError(f"Ошибка конвертации аудио: {error}")
        else:
            raise ValueError("Неподдерживаемый формат файла")
            
        # Проверяем, что файл создан
        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            raise ValueError("Файл не был создан или пустой")
            
        # Читаем файл и конвертируем в base64
        with open(output_file, 'rb') as f:
            audio_data = f.read()
            base64_audio = base64.b64encode(audio_data).decode('utf-8')
            
        return base64_audio
            
    except Exception as e:
        logger.error(f"[process_uploaded_file] Ошибка: {e}")
        raise ValueError(f"Ошибка при обработке файла: {e}")
    finally:
        # Удаляем временную директорию со всеми файлами
        shutil.rmtree(temp_dir, ignore_errors=True)
