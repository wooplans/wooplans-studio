import json, subprocess
import numpy as np
def load(f):
    raw=subprocess.run(["ffmpeg","-v","error","-i",f,"-f","f32le","-ac","1","-ar","16000","-"],capture_output=True).stdout
    return np.frombuffer(raw,dtype=np.float32)
from faster_whisper import WhisperModel
m = WhisperModel("base", device="cpu", compute_type="int8")
segs = json.load(open("voix/script.json", encoding="utf-8"))
out = {}
for i, s in enumerate(segs, 1):
    it, _ = m.transcribe(load(f"voix/sync/{i:02d}.wav"), language="fr", word_timestamps=True, beam_size=5)
    out[s["name"]] = [(w.word.strip(), round(w.start,3), round(w.end,3)) for seg in it for w in seg.words]
    print(s["name"], out[s["name"]])
json.dump(out, open("words.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
