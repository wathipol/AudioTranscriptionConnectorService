import yt_dlp
import uuid
from pathlib import Path
import subprocess
import mimetypes
from app.config import config


DATA_DIR = Path(config.data_dir)
DATA_DIR.mkdir(parents=True, exist_ok=True)


AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mkv", ".mov"}


def generate_token():
    return uuid.uuid4().hex


def download_audio_from_url(url: str) -> str:
    token = generate_token()
    output_dir = DATA_DIR / token
    output_dir.mkdir(parents=True)

    output_path = str(output_dir / "audio.%(ext)s")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'ignoreerrors': True,
        'no_check_certificate': True,
        'prefer_insecure': True,
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'extractor_args': {
            'youtube': {
                'skip': ['dash', 'hls'],
                'player_skip': ['js', 'configs', 'webpage']
            }
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return token


def save_uploaded_file(file_data: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    token = generate_token()
    output_dir = DATA_DIR / token
    output_dir.mkdir(parents=True)

    if suffix in AUDIO_EXTENSIONS:
        # Сохраняем напрямую
        file_path = output_dir / "audio.mp3"
        Path(file_path).write_bytes(file_data)
    elif suffix in VIDEO_EXTENSIONS:
        # Сохраняем временно как video и извлекаем аудио
        video_path = output_dir / f"input{suffix}"
        video_path.write_bytes(file_data)

        audio_path = output_dir / "audio.mp3"
        command = [
            "ffmpeg",
            "-i", str(video_path),
            "-vn",  # no video
            "-acodec", "libmp3lame",
            "-ab", "192k",
            str(audio_path)
        ]
        subprocess.run(command, check=True)
        video_path.unlink()  # удаляем временное видео
    else:
        raise ValueError("Unsupported file type")

    return token
