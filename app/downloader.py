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
        },
        'format_sort': ['ext:mp3:m4a', 'quality'],
        'format': 'bestaudio[ext=mp3]/bestaudio[ext=m4a]/bestaudio',
        'merge_output_format': 'mp3',
        'audioformat': 'mp3',
        'audioquality': '192',
        'nocheckcertificate': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
        'force_ipv4': True,
        'cachedir': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        },
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        'geo_bypass_ip_block': True,
        'geo_verification_proxy': None,
        'socket_timeout': 30,
        'proxy': None,
        'extract_flat': 'in_playlist',
        'playlist_items': '1',
        'no_playlist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if not info or isinstance(info, bool):
                    raise ValueError("Could not extract video info")
                
                if info.get('is_live'):
                    raise ValueError("Live streams are not supported")
                
                ydl.download([url])
                
                audio_file = output_dir / "audio.mp3"
                if not audio_file.exists():
                    raise ValueError("Audio file was not created")
                    
                return token
            except yt_dlp.utils.DownloadError as e:
                raise ValueError(f"Download error: {str(e)}")
            except Exception as e:
                raise ValueError(f"Error processing video: {str(e)}")
    except Exception as e:
        import shutil
        if output_dir.exists():
            shutil.rmtree(output_dir)
        raise ValueError(f"Failed to download audio: {str(e)}")


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
