# 🎧 FastAPI Audio Transcription Service

A containerized FastAPI application for downloading, uploading, and transcribing audio files using services like OpenAI Whisper or RunPod (Faster-Whisper). The application supports persistent storage, token-based audio access, and secure API authentication.

---

## 🚀 Features

- 🎙 Download audio from YouTube, X (Twitter), TikTok and more (via `yt-dlp`)
- 🎧 Upload your own audio/video files and extract audio
- 📝 Transcribe audio via:
  - 🔗 [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
  - ⚡️ [RunPod (Faster-Whisper)](https://www.runpod.io/)
- 🗂 Persistent `/data` directory per audio token
- 🛡 Optional `MASTER_API_TOKEN` protection
- 🌐 Fully accessible over public internet using `ngrok`

---

## ⚙️ Requirements

- Docker
- Docker Compose
- Ngrok account (free) with `NGROK_AUTHTOKEN`

---

## 📦 Installation

Clone the repository and set up environment variables:

```bash
cp .env.example .env
# Edit the .env file and insert your API keys and NGROK_AUTHTOKEN
```

---

## 🧪 Quick Start

```bash
docker-compose up --build
```

This will:

1. Start `ngrok` tunnel on port `8428`
2. Automatically fetch the public URL from `ngrok`
3. Inject the public URL into `.env` (`PUBLIC_BASE_URL`)
4. Start FastAPI app on `localhost:8428`, publicly available via `ngrok`

---

## 🔐 API Token Authentication

If `MASTER_API_TOKEN` is set in `.env`, all requests **must** include this header:

```http
x-api-token: YOUR_SECRET_TOKEN
```

---

## 📡 API Endpoints

### `POST /download`
Download audio from video URL

```json
{
  "url": "https://www.youtube.com/watch?v=..."
}
```

**Returns:**
```json
{
  "token": "abc123",
  "download_url": "/audio/abc123"
}
```

---

### `POST /upload`
Upload audio/video file and save as `.mp3`

**Form Data:**
- `file`: upload `.mp3`, `.wav`, `.mp4`, etc.

---

### `GET /audio/{token}`
Download audio file by token

---

### `GET /transcribe/{token}?force=true`
Transcribe audio by token using the selected provider (`OpenAI` or `RunPod`)

- If transcription exists → returns `.txt`
- If not → calls external API and caches the result
- `force=true` re-generates transcription

---

## ⚙️ Configuration (`.env`)

| Variable            | Description                                    |
|---------------------|------------------------------------------------|
| `NGROK_AUTHTOKEN`   | Your ngrok account token                       |
| `PUBLIC_BASE_URL`   | Overwritten automatically on startup           |
| `RUNPOD_API_KEY`    | API key for RunPod (Faster-Whisper)           |
| `RUNPOD_API_URL`    | RunPod endpoint URL                            |
| `OPENAI_API_KEY`    | OpenAI API key                                 |
| `USE_OPENAI`        | `true` to use OpenAI Whisper, else RunPod      |
| `MASTER_API_TOKEN`  | If set, enables API token authentication       |

---


### 🔧 OpenAI Whisper Configuration

To use the official OpenAI Whisper model for transcription:

1. Go to [https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)
2. Create a new API key and set it in your `.env`:

```env
USE_OPENAI=true
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
```

3. The app will now use OpenAI Whisper (`whisper-1`) for transcription via:

```
POST https://api.openai.com/v1/audio/transcriptions
```

> ⚠️ Note: OpenAI charges per minute of transcription. See pricing: https://openai.com/pricing

---

### ⚡ RunPod (Faster-Whisper) Configuration

To use a **serverless Faster-Whisper endpoint** hosted on [RunPod.io](https://www.runpod.io):

> Faster-Whisper runpod worker repo: [link](https://github.com/runpod-workers/worker-faster_whisper)

1. Sign up at [https://www.runpod.io/](https://www.runpod.io/)
2. Go to **"Serverless > Templates"** and search for `faster-whisper` or `whisper-api`
3. Deploy a **Serverless vLLM Endpoint**
4. Once deployed:
   - Copy your **API endpoint URL**
   - Copy your **API Key**
5. In your `.env` file:

```env
USE_OPENAI=false
RUNPOD_API_KEY=your-runpod-api-key
RUNPOD_API_URL=https://api.runpod.ai/v2/<your-endpoint-id>/run
```

> 💡 Make sure to **top up your RunPod balance** to avoid errors or failed jobs.

When this configuration is active, the app sends transcription requests like this:

```json
POST https://api.runpod.ai/v2/<your-endpoint-id>/run
Authorization: Bearer <RUNPOD_API_KEY>
{
  "input": {
    "prompt": "<PUBLIC AUDIO URL>"
  }
}
```

The response is parsed and cached in `.txt` per token.

---


## 🧊 License

MIT — use freely and modify to fit your needs.
