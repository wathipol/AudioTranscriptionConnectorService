import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.downloader import download_audio_from_url, save_uploaded_file, DATA_DIR
from app.transcriber.registry import get_transcriber
from loguru import logger
from app.config import config
from fastapi_mcp import add_mcp_server


def verify_api_token(x_api_token: str = Header(default=None), request: Request = None):
    # Skip verification for demo client and root index
    if request and (request.url.path.startswith('/static/demo_client') or request.url.path == '/'):
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


# Статические файлы (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="./app/static"), name="static")


logger.info("Auth token is set: {}".format("✅" if config.master_api_token is not None else "❌"))
logger.info(f"INIT FASTAPI APP FOR PUBLIC SERVER: {config.public_base_url}")


# Mount the MCP server to your app
add_mcp_server(
    app,
    mount_path="/mcp",
    name="MCP Server",
)


@app.post("/download")
def download_from_url(url: str):
    """ Download audio from url like YouTube using yt-dlp. Return token for later transcription """
    try:
        logger.info(f"Downloading audio from {url}")
        token = download_audio_from_url(url)
        logger.info(f"Downloaded audio from {url} to {token}")
        return {"token": token, "download_url": f"/audio/{token}"}
    except Exception as e:
        logger.error(f"Error downloading audio from {url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """ Upload audio file to the server from audio or video file for later transcription. Return token for later transcription """
    try:
        contents = await file.read()
        token = save_uploaded_file(contents, file.filename)
        return {"token": token, "download_url": f"/audio/{token}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.api_route("/audio/{token}", methods=["GET", "HEAD"])
def serve_audio(token: str, request: Request):
    """ Serve audio file from server """
    file_path = DATA_DIR / token / "audio.mp3"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    file_size = os.path.getsize(file_path)

    def file_iterator():
        with open(file_path, "rb") as f:
            yield from f

    return StreamingResponse(
        file_iterator(),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'inline; filename="{token}.mp3"',
            "Content-Length": str(file_size)
        }
    )


@app.get("/transcribe/{token}")
def transcribe_audio(token: str):
    """ Transcribe audio file from server. Return transcription result """
    file_path = DATA_DIR / token / "audio.mp3"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")

    base_url = str(config.public_base_url)
    audio_url = f"{base_url}/audio/{token}"

    transcriber = get_transcriber()
    try:
        result = transcriber.transcribe(audio_url)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
