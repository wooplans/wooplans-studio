"""Voix off calée + sous-titres 1 mot à la fois (surfaces = 2 mots, ex. "27 m²").
usage:  python3 build_final.py prep                          -> final/voice_mix.m4a + final/subs.ass  (+ copie dans le job)
        python3 build_final.py burn video.mp4 out.mp4 job/   -> vidéo finale (sous-titres brûlés + voix)
Exécuter 'prep' dans le dossier de travail (voix/script.json, voix/sync/*.wav, voix/sync.json, words.json)."""
import json, re, shutil, subprocess, sys, unicodedata, difflib
from pathlib import Path
MODE = sys.argv[1]
FONTS = str(Path(__file__).parent / "fonts")

def dur(f):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)],capture_output=True,text=True).stdout.strip())

if MODE == "burn":
    video, out, job = sys.argv[2], sys.argv[3], Path(sys.argv[4])
    total = dur(job / "voice_mix.m4a")
    Path("final").mkdir(exist_ok=True); shutil.copy(job / "subs.ass", "final/subs.ass"); shutil.copytree(FONTS, "final/fonts", dirs_exist_ok=True)
    vf = "[0:v]tpad=stop_mode=clone:stop_duration=10"
    extra = []
    cta = [i for i in json.loads((job / "sync.json").read_text(encoding="utf-8"))["items"] if i.get("cta")]
    stop = cta[0]["start"] + 0.6 if cta else total + 10        # filigrane et bande masqués pendant le CTA
    k = 2
    if (job / "wm_logo.png").exists():               # filigrane fixe en fond
        extra += ["-loop", "1", "-i", str(job / "wm_logo.png")]
        vf += f"[b{k}];[b{k}][{k}:v]overlay=(W-w)/2:(H-h)/2+50:shortest=1:enable='lt(t,{stop:.2f})'"; k += 1
    if (job / "band.png").exists():                  # bande verte du bas : logo + CTA wooplans.com (glisse depuis le bas)
        extra += ["-loop", "1", "-i", str(job / "band.png")]
        vf += (f"[b{k}];[b{k}][{k}:v]overlay=0:'H-h+h*max(0,1-(t-0.3)/0.5)':shortest=1:eval=frame"
               f":enable='lt(t,{stop:.2f})'"); k += 1
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",video,"-i",str(job / "voice_mix.m4a")] + extra + [
        "-filter_complex", f"{vf},subtitles=final/subs.ass:fontsdir=final/fonts[v]",
        "-map","[v]","-map","1:a","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p",
        "-c:a","copy","-t",f"{total:.2f}",out], check=True)
    print("OK", out, total); sys.exit(0)

tl = json.loads(Path("voix/sync.json").read_text(encoding="utf-8"))
segs = json.loads(Path("voix/script.json").read_text(encoding="utf-8"))
words = json.loads(Path("words.json").read_text(encoding="utf-8"))
Path("final").mkdir(exist_ok=True)
def norm(w):
    w = unicodedata.normalize("NFD", w.lower()); w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9²]", "", w)

# ---- voix : mp3 normalisés, calés à leur instant (adelay) -----------------------
for i in range(1, len(segs)+1):
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",f"voix/sync/{i:02d}.wav","-af","loudnorm=I=-16:TP=-1.5:LRA=11","-ar","44100","-b:a","192k",f"final/v{i:02d}.mp3"],check=True)
inputs, filters, labels = [], [], []
names = [s["name"] for s in segs]
for k, it in enumerate(tl["items"]):
    idx = names.index(it["name"]) + 1
    inputs += ["-i", f"final/v{idx:02d}.mp3"]
    ms = int(it["start"]*1000)
    filters.append(f"[{k}:a]adelay={ms}|{ms}[a{k}]"); labels.append(f"[a{k}]")
fc = ";".join(filters) + ";" + "".join(labels) + f"amix=inputs={len(labels)}:normalize=0,apad[aout]"
subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error"] + inputs + ["-filter_complex", fc, "-map","[aout]",
    "-t", f"{tl['total']:.2f}", "-c:a","aac","-b:a","192k","final/voice_mix.m4a"], check=True)

# ---- sous-titres ---------------------------------------------------------------
ORANGE, GREEN, WHITE = "&H2E8AF0&", "&H595B0F&", "&HFFFFFF&"
def ts(t):
    h=int(t//3600); m=int(t%3600//60); s=t%60
    return f"{h}:{m:02d}:{s:05.2f}"
TOK = re.compile(r"\d+(?:,\d+)? m²[.,;:!?]?|\d+,\d+ m|\S+")
def merge_whisper(ws):
    """fusionne '27 mètres carrés' / '99 m²' / '11 m 60' en une seule unité (comme l'affichage)."""
    out, i = [], 0
    while i < len(ws):
        w, s, e = ws[i]; n = norm(w)
        if n.isdigit() and i+2 < len(ws) and norm(ws[i+1][0]) == "m" and norm(ws[i+2][0]).isdigit():
            out.append((f"{n},{norm(ws[i+2][0])} m", s, ws[i+2][2])); i += 3; continue
        if n.isdigit() and i+1 < len(ws) and norm(ws[i+1][0]) in ("metres","m²","m2"):
            j = i+1
            if norm(ws[j][0]) == "metres" and j+1 < len(ws) and norm(ws[j+1][0]).startswith("carre"): j += 1
            out.append((f"{n} m²", s, ws[j][2])); i = j+1; continue
        out.append((w, s, e)); i += 1
    return out

events = []
for it, seg in zip(tl["items"], segs):
    toks = TOK.findall(seg["sub"])
    ws = merge_whisper([(w, s, e) for w, s, e in words[seg["name"]]])
    a = [norm(t) for t in toks]; b = [norm(w[0]) for w in ws]
    pos = [None]*len(toks)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            pos[blk.a+k] = (ws[blk.b+k][1], ws[blk.b+k][2])
    d = dur(f"final/v{names.index(it['name'])+1:02d}.mp3")
    i = 0
    while i < len(toks):               # mots non appariés : interpolation proportionnelle aux caractères
        if pos[i] is not None: i += 1; continue
        j = i
        while j < len(toks) and pos[j] is None: j += 1
        t0 = pos[i-1][1] if i > 0 else 0.0
        t1 = pos[j][0] if j < len(toks) else d
        wts = [max(2, len(norm(toks[k]))) for k in range(i, j)]; tot = sum(wts); acc = 0
        for k in range(i, j):
            pos[k] = (t0 + (t1-t0)*acc/tot, t0 + (t1-t0)*(acc+wts[k-i])/tot); acc += wts[k-i]
        i = j
    for t, (s, e) in zip(toks, pos):
        events.append((it["start"] + s, it["start"] + e, t))
events.sort()
WM = "--wm" in sys.argv                         # filigrane « wooplans.com » qui défile (jusqu'au CTA)
cta_start = next((i["start"] for i in tl["items"] if i.get("cta")), tl["total"])
lines = []
for k, (s, e, t) in enumerate(events):
    nxt = events[k+1][0] if k+1 < len(events) else e + 0.3
    end = nxt if nxt - e < 0.45 else e + 0.12      # pas de clignotement entre mots proches
    end = max(end, s + 0.18)
    txt = re.sub(r"[.,;:!?…]+$", "", t).upper().replace("M²", "m²")
    surf = bool(re.search(r"(m²|\d+,\d+ M)$", txt, re.I)) or bool(re.match(r"\d", txt))
    col = ORANGE if surf else WHITE
    lines.append(f"Dialogue: 0,{ts(s)},{ts(end)},Hormozi,,0,0,0,,{{\\c{col}\\fscx92\\fscy92\\t(0,90,\\fscx100\\fscy100)}}{txt}")
ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Hormozi,Poppins,76,{WHITE},{WHITE},{GREEN},&H80000000&,-1,0,0,0,100,100,0,0,1,9,3,2,60,60,{300 if "--band" in sys.argv else 120},1
Style: WM,Poppins,58,&H80595B0F,&H80595B0F,&HA0FFFFFF,&HFF000000,-1,0,0,0,100,100,2,0,1,3,0,5,0,0,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
""" + "\n".join(lines) + "\n"
if WM:                                          # traverse l'écran de droite à gauche, hauteur alternée
    k, t0, P = 0, 0.8, 7.0
    while t0 < cta_start - 3.0:
        y = (430, 1150, 800, 1380)[k % 4]
        t1 = min(t0 + P, cta_start)
        x1 = 1500 - (1500 + 420) * (t1 - t0) / P
        ass += f"Dialogue: 1,{ts(t0)},{ts(t1)},WM,,0,0,0,,{{\\move(1500,{y},{x1:.0f},{y})}}wooplans.com\n"
        k += 1; t0 += P + 2.0
Path("final/subs.ass").write_text(ass, encoding="utf-8")
print("prep OK :", len(events), "mots, total", tl["total"])
