# API INTERFACE SPECIFICATION

This specification describes how to interact with an already running audio transcription API instance.

BASE_URL: https://<your-server-domain>/  ← Use actual full URL, not localhost

AUTHENTICATION:
- If the API requires authentication, send a header:
  Header: x-api-token: <your_token>
- If not required, this header can be omitted.

---

### [POST] /download

**Purpose:** Download audio from a video URL (YouTube, X, TikTok, etc.).

**Headers:**
- Content-Type: application/json
- Optional: x-api-token

**Request JSON body:**
```json
{
  "url": "https://www.youtube.com/watch?v=abc"
}
```

**Response JSON:**
```json
{
  "token": "abc1234567890",
  "download_url": "/audio/abc1234567890"
}
```

---

### [POST] /upload

**Purpose:** Upload a local audio or video file. Audio will be extracted automatically if video.

**Headers:**
- Content-Type: multipart/form-data
- Optional: x-api-token

**Form-Data:**
- file: (binary audio or video file)

**Response JSON:**
```json
{
  "token": "xyz987654321",
  "download_url": "/audio/xyz987654321"
}
```

---

### [GET] /audio/{token}

**Purpose:** Retrieve the audio file associated with the token.

**URL Example:**
```
GET /audio/xyz987654321
```

**Returns:**
- Content-Type: audio/mpeg
- Binary audio file content

---

### [GET] /transcribe/{token}

**Purpose:** Transcribe the audio associated with the given token.

**Query Parameters:**
- force (optional, boolean): If true, forces regeneration of transcription.

**URL Examples:**
```
GET /transcribe/xyz987654321
GET /transcribe/xyz987654321?force=true
```

**Returns:**
- Content-Type: text/plain
- The transcription of the audio

---

### Authentication Example:

If the instance requires an API token:

```http
x-api-token: your-secret-token
```

Include this header in all requests.
