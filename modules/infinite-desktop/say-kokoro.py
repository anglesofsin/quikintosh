#!/usr/bin/env python3
"""Kokoro TTS daemon — keeps model loaded in memory for fast TTS."""
import os
import sys
import json
import wave
import tempfile
import subprocess
import struct
import urllib.request
import numpy as np
from kokoro import KPipeline

FIFO_PATH = "/tmp/say-kokoro.fifo"
SINK_NAME = "say_sink"
RVC_CONFIG_PATH = os.path.expanduser("~/.config/say-rvc/config.json")

def rvc_enabled():
    try:
        with open(RVC_CONFIG_PATH) as f:
            cfg = json.load(f)
        return cfg.get("rvc_enabled", False)
    except:
        return False

def convert_with_rvc(wav_path):
    cfg_path = RVC_CONFIG_PATH
    try:
        with open(cfg_path) as f:
            cfg = json.load(f)
        api_url = cfg.get("rvc_api_url", "http://127.0.0.1:5050")
        pitch = cfg.get("rvc_pitch", 0)
    except:
        return None
    try:
        with open(wav_path, "rb") as f:
            wav_data = f.read()
        req = urllib.request.Request(
            f"{api_url}/convert",
            data=wav_data,
            headers={
                "Content-Type": "audio/wav",
                "X-Pitch": str(pitch)
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            conv_path = wav_path.replace(".wav", "_rvc.wav")
            with open(conv_path, "wb") as f:
                f.write(resp.read())
        return conv_path
    except Exception as e:
        print(f"rvc-convert error: {e}", file=sys.stderr)
        return None

os.umask(0)
if os.path.exists(FIFO_PATH):
    os.remove(FIFO_PATH)
os.mkfifo(FIFO_PATH, 0o666)

pipelines = {}

while True:
    try:
        with open(FIFO_PATH, "r") as fifo:
            raw = fifo.read()
        if not raw:
            continue

        parts = raw.split("\0", 3)
        if len(parts) < 4:
            continue

        lang = parts[0]
        voice = parts[1]
        speed = float(parts[2])
        text = parts[3]

        if lang not in pipelines:
            pipelines[lang] = KPipeline(lang_code=lang)

        pipeline = pipelines[lang]

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name
            with wave.open(wav_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(24000)

                for result in pipeline(text, voice=voice, speed=speed, split_pattern=r"\n+"):
                    if result.audio is None:
                        continue
                    audio_bytes = (result.audio.numpy() * 32767).astype(np.int16).tobytes()
                    wav_file.writeframes(audio_bytes)

        play_path = wav_path
        if rvc_enabled():
            conv = convert_with_rvc(wav_path)
            if conv and os.path.exists(conv):
                play_path = conv

        subprocess.run(
            ["bash", "-c",
             f"cat '{play_path}' | tee >(pw-play --latency 20 -) | pw-play --target={SINK_NAME} --latency 20 -"],
            check=False
        )
        os.unlink(wav_path)
        if play_path != wav_path and os.path.exists(play_path):
            os.unlink(play_path)

    except Exception as e:
        print(f"kokoro-daemon error: {e}", file=sys.stderr)
