import subprocess
import tempfile
import os
import logging
from logging.handlers import RotatingFileHandler

import numpy as np
import soundfile as sf

from flask import Flask, request, jsonify
from waitress import serve

import sherpa_onnx


# =========================
# CONFIG
# =========================
MODEL_DIR = r"..\vosk-model-ru-0.54"  # <-- model directory (ONNX + tokens)
HOST = "127.0.0.1"
PORT = 4570
FFMPEG_PATH = r"..\ffmpeg\bin\ffmpeg.exe"  # <-- FFMPEG for optional conversion from 8kHz WAV to temporary 16kHz WAV file


# =========================
# APP + LOGS
# =========================
app = Flask(__name__)
os.makedirs("logs", exist_ok=True)

err_h = RotatingFileHandler(
    "logs/zipformer_error.log",
    maxBytes=5_000_000,
    backupCount=3,
    encoding="utf-8"
)
err_h.setLevel(logging.ERROR)

acc_h = RotatingFileHandler(
    "logs/zipformer_access.log",
    maxBytes=5_000_000,
    backupCount=3,
    encoding="utf-8"
)
acc_h.setLevel(logging.INFO)

app.logger.addHandler(err_h)
app.logger.addHandler(acc_h)
app.logger.setLevel(logging.INFO)


def convert_to_16k_wav(src_path: str) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.close()
    dst_path = tmp.name

    cmd = [
        FFMPEG_PATH,
        "-y",
        "-i", src_path,
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        dst_path
    ]

    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{p.stderr}")

    return dst_path


# =========================
# LOAD MODEL
# =========================
ENCODER = os.path.join(MODEL_DIR, "am-onnx", "encoder.onnx")
DECODER = os.path.join(MODEL_DIR, "am-onnx", "decoder.onnx")
JOINER = os.path.join(MODEL_DIR, "am-onnx", "joiner.onnx")
TOKENS = os.path.join(MODEL_DIR, "lang", "tokens.txt")

missing = [
    p for p in [ENCODER, DECODER, JOINER, TOKENS]
    if not os.path.isfile(p)
]

if missing:
    raise RuntimeError(
        "Zipformer ONNX model files are missing:\n"
        + "\n".join(missing)
        + "\n\nYou need encoder.onnx/decoder.onnx/joiner.onnx + tokens.txt"
    )

app.logger.info(f"Loading Zipformer2 (ONNX) from: {MODEL_DIR}")

recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
    encoder=ENCODER,
    decoder=DECODER,
    joiner=JOINER,
    tokens=TOKENS,
    num_threads=4,
    sample_rate=16000,  # Zipformer usually expects 16kHz audio
)

app.logger.info("Zipformer recognizer loaded successfully")


# =========================
# HELPERS
# =========================
def to_mono_float32(samples: np.ndarray) -> np.ndarray:
    # soundfile may return shape (n, channels)
    if samples.ndim == 2:
        samples = samples.mean(axis=1)

    return samples.astype(np.float32)


# =========================
# ROUTES
# =========================
@app.route("/stt", methods=["POST"])
def recognize_file():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    path = data.get("path")

    if not path:
        return jsonify({"error": "Missing 'path' field"}), 400

    if not os.path.isfile(path):
        return jsonify({"error": f"File not found: {path}"}), 404

    tmp_wav = None

    try:
        # 8kHz WAV -> temporary 16kHz WAV (mono, PCM 16-bit)
        tmp_wav = convert_to_16k_wav(path)

        samples, sr = sf.read(tmp_wav, dtype="float32")
        samples = to_mono_float32(samples)

        stream = recognizer.create_stream()
        stream.accept_waveform(sr, samples)

        recognizer.decode_stream(stream)
        text = stream.result.text

        return jsonify({"text": text})

    except Exception as e:
        app.logger.exception(f"Recognition failed: {path}")
        return jsonify({"error": str(e)}), 500

    finally:
        if tmp_wav and os.path.isfile(tmp_wav):
            try:
                os.remove(tmp_wav)
            except Exception:
                pass


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "engine": "zipformer2/sherpa-onnx",
        "model_dir": MODEL_DIR
    })


if __name__ == "__main__":
    serve(app, host=HOST, port=PORT)