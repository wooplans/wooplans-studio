"""Génère les voix Gradium d'un job YouTube : youtube_plan/jobs/<job>/voix_script.json -> voix/<seq>.wav (48 kHz mono) + <seq>.chunks.json.
Clé : variable d'environnement GRADIUM_API_KEY (secret GitHub), jamais affichée.
usage : python gen_voix.py <job>   (saute les séquences déjà générées)"""
import base64, json, os, subprocess, sys, time, urllib.request
from pathlib import Path

VOICE = "TsRKBRWZGYldAeEI"
URL = "https://api.gradium.ai/api/post/speech/tts"


def tts(text, key):
    req = urllib.request.Request(URL, data=json.dumps({"text": text, "voice_id": VOICE, "output_format": "wav", "only_audio": False}).encode(),
                                 headers={"x-api-key": key, "Content-Type": "application/json"})
    audio, chunks = b"", []
    with urllib.request.urlopen(req, timeout=170) as r:
        for ln in r:
            ln = ln.strip()
            if not ln:
                continue
            m = json.loads(ln)
            t = m.get("type")
            if t == "audio":
                audio += base64.b64decode(m["audio"])
            elif t == "text":
                chunks.append({"text": m.get("text"), "start_s": m.get("start_s"), "stop_s": m.get("stop_s")})
            elif t == "error":
                raise RuntimeError(str(m)[:200])
    return audio, chunks


def main():
    job = Path(__file__).resolve().parents[1] / "jobs" / sys.argv[1]
    key = os.environ.get("GRADIUM_API_KEY", "").strip()
    if not key:
        print("MANQUANT : secret GRADIUM_API_KEY (voir SECRETS.md)")
        return 2
    clips = json.loads((job / "voix_script.json").read_text(encoding="utf-8"))
    out = job / "voix"
    out.mkdir(exist_ok=True)
    bad = 0
    for name, text in clips.items():
        if (out / f"{name}.wav").exists() and (out / f"{name}.wav").stat().st_size > 1000:
            print("deja", name)
            continue
        for attempt in range(3):
            try:
                audio, ch = tts(text, key)
                raw = out / f"{name}.raw"
                raw.write_bytes(audio)
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-ar", "48000", "-ac", "1", str(out / f"{name}.wav")], check=True)
                raw.unlink()
                (out / f"{name}.chunks.json").write_text(json.dumps(ch, ensure_ascii=False), encoding="utf-8")
                print("ok", name, ch[-1]["stop_s"] if ch else "?")
                break
            except Exception as e:
                print("retry", name, attempt, str(e)[:120])
                time.sleep(3)
        else:
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
