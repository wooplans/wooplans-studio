"""Synchro à partir d'une voix déjà enregistrée (ElevenLabs, sans Whisper) : remplace make_sync.py + align.py.
Entrée : voix/script.json et voix/sync/NN.wav (voix découpée par pièce, silences de bord retirés).
Les mots sont calés par phrases : chaque ponctuation (, . :) est rattachée à la pause détectée la plus proche,
puis les mots sont répartis dans la phrase au prorata des caractères.
Sortie : words.json (format align.py) et voix/sync.json (format make_sync.py)."""
import json, re, subprocess
segs = json.load(open("voix/script.json", encoding="utf-8"))
def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)],capture_output=True,text=True).stdout)
def pauses(f):
    err = subprocess.run(["ffmpeg","-i",f,"-af","silencedetect=noise=-32dB:d=0.12","-f","null","-"],capture_output=True,text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(st, en))
def words_of(text, d, ps):
    toks = text.replace(" :", ":").split()       # « complète : » -> un seul mot
    w = [max(2, len(t)) for t in toks]; tot = sum(w)
    est, acc = [], 0
    for x in w: acc += x; est.append(d * acc / tot)          # fin estimée de chaque mot
    cuts, free = [], list(ps)                                  # (index du mot, début pause, fin pause)
    for i, t in enumerate(toks[:-1]):
        if re.search(r"[,.:;!?]$", t) and free:
            p = min(free, key=lambda p: abs(p[0] - est[i]))
            if abs(p[0] - est[i]) < 1.2:
                cuts.append((i, p[0], p[1])); free.remove(p)
    cuts.sort()
    out, i0, t0 = [], 0, 0.0
    for i, a, b in cuts + [(len(toks) - 1, d, d)]:
        if i < i0 or a <= t0: continue
        ww = w[i0:i + 1]; s = sum(ww); acc = 0
        for k, x in zip(range(i0, i + 1), ww):
            out.append((toks[k], round(t0 + (a - t0) * acc / s, 3), round(t0 + (a - t0) * (acc + x) / s, 3))); acc += x
        i0, t0 = i + 1, b
    return out
GAP, MIN_TRANSIT, NAME_BACK = 0.15, 1.3, 0.3
words, items, S_prev_end, T_free = {}, [], 0.0, 0.0
for i, s in enumerate(segs, 1):
    f = f"voix/sync/{i:02d}.wav"; d = dur(f)
    ws = words_of(s["spoken"], d, pauses(f)); words[s["name"]] = ws
    np_ = len(s["prefix"].replace(" :", ":").split())
    p = ws[np_ - 1][2]                    # fin du préfixe (nom de la pièce)
    if s["name"] == "CTA":                                      # séquence CTA : enchaîne dès la fin du dernier zoom arrière
        start = max(S_prev_end + GAP, T_free)
        items.append({"name": "CTA", "start": round(start,3), "dur": round(d,3), "end": round(start+d,3), "cta": True})
        S_prev_end = start + d
        continue
    if s["name"] == "Final":
        start = max(S_prev_end + GAP, T_free)
        item = {"name": "Final", "start": round(start,3), "dur": round(d,3), "end": round(start+d,3), "final": True,
                "dim1": round(start + max(0.2, p - 0.55), 3)}
        if s.get("prefix2"):
            item["dim2"] = round(start + max(0.2, ws[np_ + len(s["prefix2"].split()) - 1][2] - 0.55), 3)
        items.append(item); S_prev_end = start + d
        continue
    ZIN, ZOUT = (1.2, 1.2) if s.get("zoom") else (0.45, 0.5)
    arr_off = max(0.4, p - NAME_BACK)
    start = max(0.4 if i == 1 else S_prev_end + GAP, T_free + MIN_TRANSIT - arr_off)
    A = start + arr_off; E = start + d
    zout_start = max(A + ZIN + 0.25, E - ZOUT)
    T_free = zout_start + ZOUT; S_prev_end = E
    items.append({"name": s["name"], "zoom": bool(s.get("zoom")), "start": round(start,3), "dur": round(d,3), "arrive": round(A,3),
                  "zout_start": round(zout_start,3), "end": round(E,3)})
    print(f'{s["name"]:18s} zoom={s.get("zoom")!s:5} start {start:6.2f} arrive {A:6.2f} fin {E:6.2f}')
total = items[-1]["end"] + (2.0 if items[-1].get("cta") else 1.0)
json.dump({"total": total, "items": items}, open("voix/sync.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(words, open("words.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("total", round(total, 2))
