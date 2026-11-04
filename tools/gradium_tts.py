"""Voix off Gradium (décision de Tao du 4 nov. 2026) : texte -> WAV + repères de mots (chunks), sans Whisper.

  python tools/gradium_tts.py "texte" sortie_prefixe [voice_id]
Écrit <prefixe>.wav et <prefixe>.chunks.json ([{text, start_s, stop_s}]). Clé : GRADIUM_API_KEY (.env ou secrets GitHub)."""
import base64
import io
import json
import os
import sys
import wave

import requests

URL = "https://api.gradium.ai/api/post/speech/tts"
VOICE = "TsRKBRWZGYldAeEI"       # voix Gradium utilisée pour les vidéos WooPlans (YouTube D4-004)


def api_key() -> str:
    key = os.environ.get("GRADIUM_API_KEY", "")
    if not key and os.path.exists(".env"):
        for line in open(".env", encoding="utf-8", errors="ignore"):
            if line.startswith("GRADIUM_API_KEY="):
                key = line.split("=", 1)[1].strip().strip("\"'")
    if not key:
        raise SystemExit("GRADIUM_API_KEY manquante")
    return key


def tts(text: str, prefix: str, voice: str = VOICE):
    r = requests.post(URL, headers={"x-api-key": api_key()}, stream=True, timeout=170,
                      json={"text": text, "voice_id": voice, "output_format": "wav", "only_audio": False})
    r.raise_for_status()
    audio, chunks = b"", []
    for line in r.iter_lines():
        if not line:
            continue
        m = json.loads(line)
        t = m.get("type")
        if t == "audio":
            audio += base64.b64decode(m["audio"])
        elif t == "text":
            chunks.append({"text": m.get("text"), "start_s": m.get("start_s"), "stop_s": m.get("stop_s")})
        elif t == "error":
            raise RuntimeError(str(m)[:300])
    open(prefix + ".wav", "wb").write(audio)
    json.dump(chunks, open(prefix + ".chunks.json", "w", encoding="utf-8"), ensure_ascii=False)
    return audio, chunks


if __name__ == "__main__":
    a, ch = tts(sys.argv[1], sys.argv[2], *(sys.argv[3:4]))
    print(len(a), "octets,", len(ch), "chunks")
