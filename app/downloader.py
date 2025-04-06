import uuid
import shutil
import logging
from pathlib import Path
from typing import Optional

import yt_dlp
import subprocess

from app.config import config

logger = logging.getLogger(__name__)

DATA_DIR = Path(config.data_dir)
DATA_DIR.mkdir(parents=True, exist_ok=True)

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mkv", ".mov"}


def generate_token() -> str:
    return uuid.uuid4().hex


def get_output_dir(token: str) -> Path:
    output_dir = DATA_DIR / token
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def cleanup_dir(path: Path):
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def download_audio_from_url(url: str) -> str:
    token = generate_token()
    output_dir = get_output_dir(token)
    output_path = str(output_dir / "audio.%(ext)s")

    ydl_opts = {
        'format': 'bestaudio[ext=mp3]/bestaudio[ext=m4a]/bestaudio',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'retries': 5,
        'fragment_retries': 5,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'default_search': 'auto',
        'force_ipv4': True,
        'source_address': '0.0.0.0',
        'cachedir': False
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise ValueError("Не удалось извлечь информацию о видео")

            if info.get("is_live"):
                raise ValueError("Live-трансляции не поддерживаются")

            ydl.download([url])

        audio_file = output_dir / "audio.mp3"
        if not audio_file.exists():
            raise FileNotFoundError("Файл audio.mp3 не создан после загрузки")

        return token

    except Exception as e:
        cleanup_dir(output_dir)
        logger.error(f"[download_audio_from_url] Ошибка: {e}")
        raise ValueError(f"Не удалось скачать аудио: {e}")


def save_uploaded_file(file_data: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    token = generate_token()
    output_dir = get_output_dir(token)

    try:
        if suffix in AUDIO_EXTENSIONS:
            audio_path = output_dir / "audio.mp3"
            audio_path.write_bytes(file_data)

        elif suffix in VIDEO_EXTENSIONS:
            video_path = output_dir / f"input{suffix}"
            video_path.write_bytes(file_data)

            audio_path = output_dir / "audio.mp3"
            command = [
                "ffmpeg", "-i", str(video_path),
                "-vn", "-acodec", "libmp3lame", "-ab", "192k",
                str(audio_path)
            ]

            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )

            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr.decode()}")

            video_path.unlink(missing_ok=True)

        else:
            raise ValueError("Неподдерживаемый формат файла")

        return token

    except Exception as e:
        cleanup_dir(output_dir)
        logger.error(f"[save_uploaded_file] Ошибка: {e}")
        raise ValueError(f"Ошибка при сохранении файла: {e}")
