"""Voix (Piper tom) + musique et accents (Audio as Code) + bruitages synthétisés (whoosh, click, pop)
-> hook.m4a, estim.m4a, cta.m4a et bump.json (repères partagés avec scene_bumpers.py)."""
import json, subprocess, os
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
from audio_as_code import Song, Track, Note, render, Reverb, Filter

SR = 44100
PIPER = ["python3", "-m", "piper", "-m", "voix/fr_FR-tom-medium.onnx", "--length-scale", "1.05"]
os.makedirs("aud2", exist_ok=True)

def dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                                capture_output=True, text=True).stdout)

def tts(text, name):
    raw, w = f"aud2/{name}_r.wav", f"aud2/{name}.wav"
    subprocess.run(PIPER + ["-f", raw], input=text, text=True, check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ar", str(SR), "-ac", "1", w], check=True)
    return w, dur(w)

def load(w):
    sr, x = wavfile.read(w)
    x = x.astype(np.float32)
    if x.dtype != np.float32 or np.abs(x).max() > 2:
        x = x / 32768.0
    if x.ndim == 2:
        x = x.mean(axis=1)
    return x

def db(g): return 10 ** (g / 20)

# ---------------------------------------------------------------- bruitages (synthèse numpy)
rng = np.random.default_rng(7)
def whoosh(length=0.7, f0=300, f1=4000, gain=-14, up=True):
    n = int(length * SR); noise = rng.standard_normal(n).astype(np.float32)
    out = np.zeros(n, np.float32); hop = 441
    for i in range(0, n, hop):
        p = i / n
        fc = f0 * (f1 / f0) ** (p if up else 1 - p)
        lo, hi = max(40, fc * 0.6), min(SR / 2 - 100, fc * 1.6)
        sos = butter(2, [lo, hi], btype="band", fs=SR, output="sos")
        seg = noise[max(0, i - 2000):i + hop]
        out[i:i + hop] = sosfilt(sos, seg)[-len(out[i:i + hop]):]
    env = np.sin(np.linspace(0, np.pi, n)) ** 1.6
    out *= env
    return out / (np.abs(out).max() + 1e-9) * db(gain)

def click(gain=-16):
    n = int(0.03 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * 2800 * t) * np.exp(-t * 260)
    s[:90] += rng.standard_normal(90) * np.linspace(1, 0, 90) * 0.6
    sos = butter(2, 900, btype="high", fs=SR, output="sos")
    s = sosfilt(sos, s)
    return (s / np.abs(s).max() * db(gain)).astype(np.float32)

def pop(gain=-17, f0=950, f1=320):
    n = int(0.09 * SR); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 45)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38)
    return (s / np.abs(s).max() * db(gain)).astype(np.float32)

def put(buf, x, t):
    i = int(t * SR); j = min(len(buf), i + len(x))
    if i < len(buf):
        buf[i:j] += x[:j - i]

# ---------------------------------------------------------------- musique + accents (Audio as Code)
def aac(name, total, tracks, lufs=-20.0):
    song = Song(title=name, bpm=60, beats=round(total + 0.5, 3), seed=11, master_gain=0.8, tracks=tuple(tracks),
                effects=(Reverb(decay_seconds=1.4, mix=0.18),))
    path = f"aud2/{name}_music.wav"
    render(song, path, target_lufs=lufs)
    return load(path)

def N(p, s, d=0.4, v=0.7):
    return Note(pitch=p, start=round(float(s), 3), duration=d, velocity=v)

def mix(name, total, voices, music, sfx_events, music_gain=-13, music_fade=None):
    n = int(total * SR); buf = np.zeros(n, np.float32)
    m = np.zeros(n, np.float32); m[:min(n, len(music))] = music[:n]
    if music_fade:
        a, b = music_fade; i, j = int(a * SR), int(b * SR)
        m[i:j] *= np.linspace(1, 0, j - i); m[j:] = 0
    buf += m * db(music_gain)
    for w, t in voices:
        put(buf, load(w), t)
    for x, t in sfx_events:
        put(buf, x, t)
    peak = np.abs(buf).max()
    if peak > 0.97:
        buf *= 0.97 / peak
    wav = f"aud2/{name}_mix.wav"
    wavfile.write(wav, SR, (buf * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-ac", "2",
                    f"out6/{name}.m4a"], check=True)

B = {"band": "Duplex D5-016  ·  5 chambres", "start_pos": [396.40625, 812.328125], "body_cut": 8.48, "body_end": 111.70}

# ================================================================= HOOK
h1, d1 = tts("Combien faut-il pour construire cette maison de cinq chambres ?", "hook0")
h2, d2 = tts("Commençons par examiner son plan.", "hook1")
v1s = 0.35; v2s = round(v1s + d1 + 0.45, 3); total = round(v2s + d2 + 0.6, 3)
cue = {"facade": 0.0, "tag": 0.45, "w1": 0.8, "w2": 1.15, "w3": 1.95, "chip": 2.75, "pulse": 3.15,
       "trans": round(v2s - 0.1, 3), "dot": round(v2s + 0.75, 3)}
B["hook"] = {"items": [{"start": v1s, "dur": round(d1, 3)}, {"start": v2s, "dur": round(d2, 3)}], "total": total, "cues": cue}
tr = cue["trans"]
music = aac("hook", total, [
    Track(name="Pad", instrument="wavetable_pad", gain=0.45, notes=(N("A2", 0, tr + 0.6, 0.5), N("E3", 0, tr + 0.6, 0.45), N("C4", 0, tr + 0.6, 0.4))),
    Track(name="Pulse", instrument="sub_bass", gain=0.5, notes=tuple(N("A1", x, 0.35, 0.6) for x in (0.0, 1.0, 2.0, 3.0))),
    Track(name="Ticks", instrument="metal_hat", gain=0.18, notes=tuple(N(42, round(0.5 + 0.25 * k, 3), 0.05, 0.5) for k in range(int((tr - 0.5) / 0.25)))),
    Track(name="Accents", instrument="kalimba", gain=0.6, notes=(N("A4", cue["w1"], 0.5), N("C5", cue["w2"], 0.6, 0.85), N("E5", cue["w3"], 0.5), N("A5", cue["chip"], 0.6, 0.6))),
    Track(name="Boom", instrument="kick_808", gain=0.7, notes=(N(36, cue["pulse"], 0.6, 0.9),)),
    Track(name="Bell", instrument="fm_bell", gain=0.3, notes=(N("E6", cue["dot"], 1.0, 0.5),)),
])
mix("hook", total, [(h1, v1s), (h2, v2s)], music, [
    (whoosh(0.6, 250, 3500, -16), 0.0), (pop(-19), cue["tag"]), (pop(-18), cue["w1"]), (pop(-16, 1100, 380), cue["w2"]),
    (pop(-18), cue["w3"]), (click(-18), cue["chip"]), (whoosh(0.85, 200, 6000, -12), tr - 0.05), (click(-15), cue["dot"]),
], music_gain=-12, music_fade=(tr + 0.2, tr + 1.1))

# ================================================================= ESTIMATION
e1, d1 = tts("Selon le devis de ce plan, comptez quarante-trois millions huit cent soixante-quatre mille francs, clé en main.", "estim0")
e2, d2 = tts("Le coût réel dépend du terrain, des techniciens et des matériaux.", "estim1")
v1s = 0.6; v2s = round(v1s + d1 + 0.25, 3); total = round(v2s + d2 + 0.12, 3)
cs, ce = 1.1, 5.6
cue = {"sheet": 0.0, "lab": 0.7, "count0": cs, "count1": ce, "pill": 2.3, "bar": 3.0, "impact": round(ce + 0.1, 3), "note": v2s}
B["estim"] = {"items": [{"start": v1s, "dur": round(d1, 3)}, {"start": v2s, "dur": round(d2, 3)}], "total": total, "cues": cue}
ticks = []
k_prev = 0
for i in range(int((ce - cs) * 100)):
    x = i / ((ce - cs) * 100); p = 1 - (1 - x) ** 3; k = int(p * 28)
    if k > k_prev:
        ticks.append(round(cs + x * (ce - cs), 3)); k_prev = k
music = aac("estim", total, [
    Track(name="Pad", instrument="wavetable_pad", gain=0.4, notes=(N("F2", 0, 5.6, 0.45), N("C3", 0, 5.6, 0.4), N("A3", 0, 5.6, 0.35),
                                                                  N("C3", 5.7, total - 5.7, 0.45), N("G3", 5.7, total - 5.7, 0.4), N("E4", 5.7, total - 5.7, 0.35))),
    Track(name="Ticks", instrument="metal_hat", gain=0.3, notes=tuple(N(42, t, 0.04, 0.6) for t in ticks)),
    Track(name="Accents", instrument="marimba", gain=0.55, notes=(N("C5", cue["lab"], 0.4), N("G5", cue["pill"], 0.4), N("E5", 4.1, 0.4, 0.5), N("C5", cue["note"], 0.5, 0.5))),
    Track(name="Impact", instrument="kick_808", gain=0.75, notes=(N(36, cue["impact"], 0.7, 0.95),)),
    Track(name="Ding", instrument="fm_bell", gain=0.45, notes=(N("C6", cue["impact"], 1.6, 0.7), N("G6", cue["impact"] + 0.12, 1.4, 0.5))),
    Track(name="Crash", instrument="cymbal", gain=0.18, notes=(N(49, cue["impact"], 1.5, 0.5),)),
])
mix("estim", total, [(e1, v1s), (e2, v2s)], music, [
    (whoosh(0.7, 180, 5000, -13), 0.0), (click(-18), cue["lab"]), (pop(-18), 1.1), (pop(-17), cue["pill"]),
    (whoosh(1.0, 400, 3000, -20), cue["bar"]),
], music_gain=-14)

# ================================================================= CTA
c1, d1 = tts("Abonnez-vous pour découvrir d'autres plans.", "cta0")
v1s = 0.2
cue = {"logo": 0.0, "button": 0.1, "cursor": 0.75, "tap": 1.3, "bar": 1.75, "s1": 1.95, "s2": 2.3, "url": 2.75}
total = round(max(cue["url"] + 1.3, v1s + d1 + 0.5), 3)
B["cta"] = {"items": [{"start": v1s, "dur": round(d1, 3)}], "total": total, "cues": cue}
music = aac("cta", total, [
    Track(name="Pad", instrument="wavetable_pad", gain=0.4, notes=(N("C3", 0, total, 0.45), N("G3", 0, total, 0.4), N("E4", 0, total, 0.35))),
    Track(name="Shimmer", instrument="glockenspiel", gain=0.35, notes=(N("C6", 0.05, 0.8, 0.5), N("G6", 0.2, 0.8, 0.45), N("E6", 0.35, 0.8, 0.4))),
    Track(name="Pluck", instrument="trance_pluck", gain=0.25, notes=tuple(N(p, round(0.6 + 0.5 * i, 3), 0.25, 0.5) for i, p in enumerate(["C4", "E4", "G4", "C5", "G4", "E4"]))),
    Track(name="Accents", instrument="marimba", gain=0.55, notes=(N("G5", cue["button"], 0.4), N("C5", cue["s1"], 0.4), N("E5", cue["s2"], 0.6))),
    Track(name="Boom", instrument="kick_808", gain=0.6, notes=(N(36, cue["button"], 0.5, 0.8),)),
])
mix("cta", total, [(c1, v1s)], music, [
    (whoosh(0.6, 300, 4500, -15), 0.0), (pop(-16, 1000, 300), cue["button"]), (whoosh(0.4, 800, 2500, -24), cue["cursor"]),
    (click(-12), cue["tap"]), (click(-19), cue["bar"]), (pop(-18), cue["url"]),
], music_gain=-13)

json.dump(B, open("out6/bump.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(B, ensure_ascii=False, indent=1))
