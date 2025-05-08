# 🎧 FastAPI Audio Transcription Service

Сервис для транскрипции аудио с YouTube и других источников, а также для загруженных файлов. Поддерживает защиту от анти-бот проверок и различные провайдеры транскрипции.

> 🚫 Not suitable for production

---

## 🚀 Особенности

- 🎙 Поддержка YouTube, X (Twitter), TikTok и других сервисов через `yt-dlp`
- 🎧 Загрузка аудио/видео файлов для транскрипции
- 📝 Поддержка транскрипции через:
  - 🔗 [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
  - ⚡️ [RunPod (Faster-Whisper)](https://www.runpod.io/)
- 🤖 Защита от анти-бот проверок с поддержкой прокси
- 🏎 Прямая потоковая обработка без хранения данных
- 🛡 Опциональная защита API с помощью `MASTER_API_TOKEN`

---

## ⚙️ Требования

- Docker
- Docker Compose

---

## 📦 Установка

Клонируйте репозиторий и настройте переменные окружения:

```bash
cp .env.example .env
# Отредактируйте файл .env и добавьте ваши API ключи
```

---

## 🧪 Быстрый старт

```bash
docker-compose up --build
```

Сервис будет доступен по адресу `http://localhost:8428`

---

## 🤖 Защита от анти-бот проверок

YouTube и другие сервисы применяют анти-бот проверки, которые могут блокировать скачивание. Эта версия включает меры, которые помогают обойти такие ограничения:

### Настройка прокси

В файле `.env` можно указать прокси-сервер:

```env
PROXY=http://user:pass@host:port
# или
PROXY=socks5://user:pass@host:port
```

### Рекомендации по прокси:

1. **Жилые IP**: Используйте "жилые" (residential) IP-адреса, так как они вызывают меньше подозрений.
2. **Геолокация**: Выбирайте прокси из тех же регионов, что и контент, который вы скачиваете.
3. **Ротация**: Используйте прокси с ротацией IP для избежания блокировок.
4. **Провайдеры прокси**:
   - [Bright Data](https://brightdata.com/) - высококачественные residential прокси
   - [Oxylabs](https://oxylabs.io/) - большой выбор residential и datacenter прокси
   - [IPRoyal](https://iproyal.com/) - доступное решение с residential IP

### User-Agent и Cookies

Для еще большей защиты можно указать собственный User-Agent и файл с cookies:

```env
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
COOKIES_FILE=/path/to/cookies.txt
```

Чтобы получить cookies с YouTube:
1. Войдите в свой YouTube аккаунт через браузер
2. Используйте расширение типа "Cookie-Editor" для экспорта cookies
3. Сохраните файл в формате NETSCAPE или JSON

---

## 🔐 Аутентификация API

Если в файле `.env` установлена переменная `MASTER_API_TOKEN`, все запросы должны включать следующий заголовок:

```http
x-api-token: YOUR_SECRET_TOKEN
```

---

## 📡 API Endpoints

### `POST /transcribe/url`
Скачивает аудио с URL (например, YouTube) и сразу возвращает транскрипцию

**Параметры:**
```json
{
  "url": "https://www.youtube.com/watch?v=..."
}
```

**Возвращает:**
```json
{
  "output": {
    "transcription": "текст транскрипции...",
    "model": "whisper-1",
    "provider": "openai"
  },
  "status": "COMPLETED"
}
```

---

### `POST /transcribe/file`
Принимает загруженный аудио/видео файл, обрабатывает его и сразу возвращает транскрипцию

**Форма:**
- `file`: загрузите `.mp3`, `.wav`, `.mp4` и т.д.

**Возвращает:**
```json
{
  "output": {
    "transcription": "текст транскрипции...",
    "model": "whisper-1",
    "provider": "openai"
  },
  "status": "COMPLETED"
}
```

---

## ⚙️ Конфигурация (`.env`)

| Переменная         | Описание                                     |
|--------------------|----------------------------------------------|
| `RUNPOD_API_KEY`   | API ключ для RunPod (Faster-Whisper)        |
| `RUNPOD_API_URL`   | URL эндпоинта RunPod                        |
| `OPENAI_API_KEY`   | API ключ OpenAI                             |
| `USE_OPENAI`       | `true` для использования OpenAI Whisper     |
| `MASTER_API_TOKEN` | Если указан, включает защиту API            |
| `PROXY`            | HTTP или SOCKS5 прокси для yt-dlp           |
| `USER_AGENT`       | Пользовательский User-Agent                 |
| `COOKIES_FILE`     | Путь к файлу с cookies                      |

---

### 🔧 Настройка OpenAI Whisper

Для использования официальной модели OpenAI Whisper:

1. Перейдите на страницу [https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)
2. Создайте новый API ключ и добавьте его в файл `.env`:

```env
USE_OPENAI=true
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
```

> ⚠️ OpenAI взимает плату за каждую минуту транскрипции. Подробнее о ценах: https://openai.com/pricing

---

### ⚡ Настройка RunPod (Faster-Whisper)

Для использования **серверлесс Faster-Whisper endpoint** на [RunPod.io](https://www.runpod.io):

> Репозиторий с Faster-Whisper для RunPod: [link](https://github.com/runpod-workers/worker-faster_whisper)

1. Зарегистрируйтесь на [https://www.runpod.io/](https://www.runpod.io/)
2. Перейдите в **"Serverless > Templates"** и найдите `faster-whisper` или `whisper-api`
3. Разверните **Serverless vLLM Endpoint**
4. После развертывания:
   - Скопируйте ваш **API endpoint URL**
   - Скопируйте ваш **API Key**
5. В файле `.env`:

```env
USE_OPENAI=false
RUNPOD_API_KEY=your-runpod-api-key
RUNPOD_API_URL=https://api.runpod.ai/v2/<your-endpoint-id>/run
```

> 💡 Убедитесь, что на вашем счете RunPod достаточно средств.

---

## 🧊 Лицензия

MIT — используйте свободно и изменяйте под свои нужды.
