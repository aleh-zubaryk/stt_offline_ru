# Russian Speech Offline Recognition Service

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-green)
![API](https://img.shields.io/badge/API-REST-orange)
![Status](https://img.shields.io/badge/status-active-success)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Local speech-to-text service for Russian language audio recognition based on the Zipformer2 model.

The service runs as a Windows Service and exposes a local HTTP API on:

http://127.0.0.1:4570

---

## Features

- Local offline speech recognition
- Russian language support
- REST API for integration with external systems
- Windows Service support via NSSM
- Automatic WAV conversion to 16 kHz using ffmpeg
- Based on Zipformer2 / Sherpa-ONNX

---

## Technology Stack

- Python 3.11
- Flask
- Waitress
- Sherpa-ONNX
- ffmpeg
- NSSM

---

## Components

### Python 3.11

Python versions above 3.11 are not recommended.

https://www.python.org/ftp/python/3.11.6/python-3.11.6-amd64.exe

---

### ffmpeg

Used for converting WAV audio files to 16 kHz if required.

https://www.ffmpeg.org/download.html#build-windows

---

### Speech Recognition Model

https://huggingface.co/alphacep/vosk-model-ru

---

### NSSM

Required version: 2.24.101 or newer.

https://nssm.cc/download

---

## Quick Start

### Install dependencies

```bash
pip install -r requirements.txt
```

---

### Project structure

```text
Recognizer/
├── ffmpeg/
├── vosk-model-ru-0.54/
└── Service/
    └── service.py
```

---

### Create Windows Service

```bash
nssm install Recognizer
```

Configuration:

| Field | Value |
|---|---|
| Path | `C:\Python311\python.exe` |
| Startup directory | `Recognizer\Service` |
| Arguments | `service.py` |

---

## API Usage

### Speech-to-Text Endpoint

```http
POST /stt
```

Request body:

```json
{
    "path": "C:\\Records\\call.wav"
}
```

---

## cURL Example

```bash
curl -X POST http://127.0.0.1:4570/stt ^
-H "Content-Type: application/json" ^
-d "{\"path\":\"C:\\\\Records\\\\call.wav\"}"
```

---

## Example Response

```json
{
    "text": "Здравствуйте, чем могу помочь?"
}
```

---

## Health Check

```text
http://127.0.0.1:4570/health
```

Example response:

```json
{
    "status": "ok",
    "engine": "zipformer2/sherpa-onnx"
	"model_dir":"..\\vosk-model-ru-0.54"
}
```

---

## HTTP Response Codes

| Code | Description |
|---|---|
| 200 | Recognition successful |
| 400 | Invalid request |
| 404 | Audio file not found |
| 500 | Internal recognition error |

---

## Logs

Log files are stored in:

```text
logs/
```

Available logs:
- `zipformer_access.log`
- `zipformer_error.log`

---

## Release Notes

### v1.0.0

Initial release:
- Offline Russian speech recognition
- REST API support
- Windows Service support
- WAV auto-conversion to 16 kHz
- Sherpa-ONNX + Zipformer2 integration

---

## Notes

- Audio files should preferably be WAV format.
- Automatic conversion to 16 kHz is supported.
- The API is intended for local usage on localhost.
- Internet connection is not required after installation.
