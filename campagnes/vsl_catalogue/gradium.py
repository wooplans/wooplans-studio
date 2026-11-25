"""Voix Gradium de la VSL du Catalogue Premium (demande de Tao, 23 nov. 2026), exécuté par le workflow `vsl-voix`
(clé GRADIUM_API_KEY dans les secrets GitHub, jamais affichée). Lit campagnes/vsl_catalogue/voix/REQUEST.json :

  {"action": "design", "prompt": "...", "n": 4, "line": "phrase d'essai (100 caractères max)"}
      → crée des voix candidates (Voice Design) et une écoute de chacune : voix/candidats/<id>.wav + candidats.json
  {"action": "convert", "embedding_id": "vox_emb_...", "name": "..."}
      → transforme la candidate choisie en voix permanente : voix/voice.json (uid)
  {"action": "tts", "voice_id": "...", "script": "campagnes/vsl_catalogue/voix_script.json"}
      → génère chaque séquence : voix/tts/<seq>.wav (48 kHz mono) + <seq>.chunks.json (mots horodatés)
"""
import base64, json, os, subprocess, sys, time, urllib.request
from pathlib import Path

BASE = "https://api.gradium.ai/api"
HERE = Path(__file__).resolve().parent
VOIX = HERE / "voix"


def call(method, path, body=None, raw=False, timeout=170):
    req = urllib.request.Request(f"{BASE}{path}", method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"x-api-key": os.environ["GRADIUM_API_KEY"].strip(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if raw else json.loads(data or b"{}")


def wav(path, data):
    raw = path.with_suffix(".raw")
    raw.write_bytes(data)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-ar", "48000", "-ac", "1", str(path)], check=True)
    raw.unlink()


def design(req):
    out = VOIX / "candidats"
    out.mkdir(parents=True, exist_ok=True)
    res = call("POST", "/voice-generator/generate", {"prompt": req["prompt"], "language": "fr", "n_samples": int(req.get("n", 4))})
    ids = [e["embedding_id"] for e in res["embeddings"]]
    for eid in ids:
        for _ in range(60):
            found = call("GET", f"/voice-generator/embeddings?embedding_id={eid}")["embeddings"]
            if found and found[0].get("ready"):
                break
            time.sleep(2)
        audio = call("POST", "/speech/tts", {"text": req["line"][:100], "voice_id": eid, "model_name": "default", "output_format": "wav", "only_audio": True}, raw=True)
        wav(out / f"{eid}.wav", audio)
        print("candidate", eid)
    meta = json.loads((out / "candidats.json").read_text()) if (out / "candidats.json").exists() else []
    meta.append({"prompt": req["prompt"], "line": req["line"], "ids": ids})
    (out / "candidats.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))


def audition(req):
    """Réécoute de candidats déjà créés (ids donnés), sans nouveau design."""
    out = VOIX / "candidats"
    out.mkdir(parents=True, exist_ok=True)
    for eid in req["ids"]:
        audio = call("POST", "/speech/tts", {"text": req["line"][:100], "voice_id": eid, "model_name": "default", "output_format": "wav", "only_audio": True}, raw=True)
        wav(out / f"{eid}.wav", audio)
        print("candidate", eid)


def convert(req):
    res = call("POST", "/voices/from-embedding", {"voxium_embedding_id": req["embedding_id"], "name": req.get("name", "WooPlans VSL"), "description": "Narrateur VSL WooPlans"})
    (VOIX / "voice.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print("voix", res.get("uid"))


def tts(req):
    out = VOIX / "tts"
    out.mkdir(parents=True, exist_ok=True)
    clips = json.loads((HERE.parents[1] / req["script"]).read_text(encoding="utf-8"))
    for name, text in clips.items():
        if (out / f"{name}.wav").exists() and not req.get("force"):
            continue
        body = {"text": text, "voice_id": req["voice_id"], "output_format": "wav", "only_audio": False}
        if req.get("json_config"):
            body["json_config"] = json.dumps(req["json_config"])
        r = urllib.request.Request(f"{BASE}/post/speech/tts", data=json.dumps(body).encode(),
                                   headers={"x-api-key": os.environ["GRADIUM_API_KEY"].strip(), "Content-Type": "application/json"})
        audio, chunks = b"", []
        with urllib.request.urlopen(r, timeout=170) as resp:
            for ln in resp:
                ln = ln.strip()
                if not ln:
                    continue
                m = json.loads(ln)
                if m.get("type") == "audio":
                    audio += base64.b64decode(m["audio"])
                elif m.get("type") == "text":
                    chunks.append({"text": m.get("text"), "start_s": m.get("start_s"), "stop_s": m.get("stop_s")})
                elif m.get("type") == "error":
                    raise RuntimeError(str(m)[:200])
        wav(out / f"{name}.wav", audio)
        (out / f"{name}.chunks.json").write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
        print("ok", name, chunks[-1]["stop_s"] if chunks else "?")


def main():
    if not os.environ.get("GRADIUM_API_KEY", "").strip():
        print("MANQUANT : secret GRADIUM_API_KEY")
        return 2
    req = json.loads((VOIX / "REQUEST.json").read_text(encoding="utf-8"))
    {"design": design, "audition": audition, "convert": convert, "tts": tts}[req["action"]](req)
    return 0


if __name__ == "__main__":
    sys.exit(main())
