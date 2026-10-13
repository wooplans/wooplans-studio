"""Synchro voix <-> animation (V6) : voix continue, le point s'arrête pile sur le nom de la pièce.
Génère voix piper (tom), trims, sync.json. Zoom variable (champ zoom du script)."""
import json, subprocess, os
PIPER = ["python3", "-m", "piper", "-m", "voix/fr_FR-tom-medium.onnx", "--length-scale", "1.05"]
segs = json.load(open("voix/script.json", encoding="utf-8"))
os.makedirs("voix/sync", exist_ok=True)
def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)],capture_output=True,text=True).stdout)
def trim_end(src, dst):
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",src,"-af","silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse","-ar","44100",dst],check=True)
def tts(text, wav):
    subprocess.run(PIPER + ["-f", wav], input=text, text=True, check=True, capture_output=True)
GAP, MIN_TRANSIT, NAME_BACK = 0.15, 1.3, 0.3
items, S_prev_end, T_free = [], 0.0, 0.0
for i, s in enumerate(segs, 1):
    raw, full, pre = f"voix/sync/r{i:02d}.wav", f"voix/sync/{i:02d}.wav", f"voix/sync/p{i:02d}.wav"
    tts(s["spoken"], raw); trim_end(raw, full)
    tts(s["prefix"], "voix/sync/_p.wav"); trim_end("voix/sync/_p.wav", pre)
    d, p = dur(full), dur(pre)
    final = s["name"] == "Final"
    ZIN, ZOUT = (1.2, 1.2) if s.get("zoom") else (0.45, 0.5)
    if final:
        start = max(S_prev_end + GAP, T_free)
        item = {"name": s["name"], "start": round(start,3), "dur": round(d,3), "end": round(start+d,3), "final": True,
                "dim1": round(start + max(0.2, p - 0.55), 3)}
        tts(s["prefix2"], "voix/sync/_p2.wav"); trim_end("voix/sync/_p2.wav", "voix/sync/p2.wav")
        item["dim2"] = round(start + max(0.2, dur("voix/sync/p2.wav") - 0.55), 3)
        items.append(item); S_prev_end = start + d
        continue
    arr_off = max(0.4, p - NAME_BACK)
    start = max(0.4 if i == 1 else S_prev_end + GAP, T_free + MIN_TRANSIT - arr_off)
    A = start + arr_off; E = start + d
    zout_start = max(A + ZIN + 0.25, E - ZOUT)
    T_free = zout_start + ZOUT
    S_prev_end = E
    items.append({"name": s["name"], "zoom": bool(s.get("zoom")), "start": round(start,3), "dur": round(d,3), "arrive": round(A,3),
                  "zout_start": round(zout_start,3), "end": round(E,3)})
    print(f'{s["name"]:11s} zoom={s.get("zoom")!s:5} start {start:6.2f} arrive {A:6.2f} fin {E:6.2f}')
total = items[-1]["end"] + 1.0
json.dump({"total": total, "items": items}, open("voix/sync.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("total", total, items[-1])
