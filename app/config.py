from pydantic_settings import BaseSettings


class Config(BaseSettings):
    data_dir: str = "/data"
    runpod_api_key: str = "abc1234567890"
    runpod_api_url: str = "https://api.runpod.ai/v2/abc1234567890/run"
    public_base_url: str = "http://localhost:8000"
    openai_api_key: str = "sk-proj-1234567890"
    use_openai: bool = False
    master_api_token: str | None = None
    setup_cors_middleware: bool = True

    class Config:
        env_file = ".env"
        extra = "allow"  # Allow dynamic config variables
        


config = Config()
