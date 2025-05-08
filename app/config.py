from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Config(BaseSettings):
    data_dir: str = "/data"
    runpod_api_key: str = "abc1234567890"
    runpod_api_url: str = "https://api.runpod.ai/v2/abc1234567890/run"
    public_base_url: str = "http://localhost:8000"
    openai_api_key: str | None = "sk-proj-1234567890"
    use_openai: bool = False
    master_api_token: str | None = None
    setup_cors_middleware: bool = True
    
    # Настройки для защиты от анти-бот проверок
    proxy: str | None = None  # формат: http://user:pass@host:port или socks5://user:pass@host:port
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    cookies_file: str | None = None  # путь к файлу с куками

    class Config:
        env_file = ".env"
        extra = "allow"  # Allow dynamic config variables
        


config = Config()
