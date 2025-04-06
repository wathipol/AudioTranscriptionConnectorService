import time
import requests
from pathlib import Path
from dotenv import dotenv_values, set_key


def wait_for_ngrok():
    for _ in range(30):
        try:
            r = requests.get("http://ngrok:4040/api/tunnels")  # внутри docker
            tunnels = r.json()["tunnels"]
            for t in tunnels:
                if t["proto"] == "https":
                    return t["public_url"]
        except Exception:
            time.sleep(1)
    raise RuntimeError("Ngrok tunnel not found")


def update_env(public_url: str):
    env_path = Path(".env")
    if not env_path.exists():
        raise FileNotFoundError(".env not found")
    set_key(str(env_path), "PUBLIC_BASE_URL", public_url)
    print(f"✅ Updated PUBLIC_BASE_URL to {public_url}")


if __name__ == "__main__":
    print("⏳ Waiting for ngrok tunnel...")
    public_url = wait_for_ngrok()
    update_env(public_url)
