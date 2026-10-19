"""Préparation du job « visite sans 3D » du plan 3 chambres (voix test Edge TTS, timings des mots par WordBoundary).
usage: python3 prep_nf_pl3c.py <dossier_job> <dossier_visite_plan>
Produit dans le job : sync.json, segments.json, voice_mix.m4a, subs_body.ass, hook.m4a, cta.m4a, bump.json."""
import asyncio, json, os, re, shutil, subprocess, sys, unicodedata
from pathlib import Path
import edge_tts

JOB = Path(sys.argv[1]).resolve(); VP = Path(sys.argv[2]).resolve()
WORK = Path("/tmp/pl3c_work"); shutil.rmtree(WORK, ignore_errors=True); (WORK / "voix/sync").mkdir(parents=True)
os.chdir(WORK)
VOICE = "fr-FR-DeniseNeural"

HOOK = ("Trois chambres, trois salles d'eau, un dressing et même un coin bureau, le tout de plain-pied. "
        "Cette maison, vous la prendriez ? Regardons son plan ensemble.")
CTA = "Pour découvrir d'autres modèles, rendez-vous sur wooplans.com."
SEGS = [
 dict(name="Porche d'entrée", zoom=False, spoken="On entre par le porche d'entrée,", prefix="On entre par le porche d'entrée"),
 dict(name="Salon", zoom=True, spoken="qui ouvre directement sur un grand salon, avec de larges ouvertures sur l'extérieur.", prefix="qui ouvre directement sur un grand salon"),
 dict(name="Salle à manger", zoom=False, spoken="Juste à côté, la salle à manger, avec une grande table pour recevoir toute la famille.", prefix="Juste à côté, la salle à manger"),
 dict(name="Cuisine", zoom=True, spoken="Elle communique avec une cuisine bien spacieuse,", prefix="Elle communique avec une cuisine"),
 dict(name="Porche arrière", zoom=False, spoken="qui donne sur une véranda bien pratique au quotidien.", prefix="qui donne sur une véranda"),
 dict(name="Couloir", zoom=False, spoken="Depuis la salle à manger, on rejoint le couloir, qui dessert toute la partie nuit.", prefix="Depuis la salle à manger, on rejoint le couloir"),
 dict(name="Chambre 2", zoom=True, spoken="Première porte : la chambre 2,", prefix="Première porte : la chambre 2", sub="Première porte la chambre 2,"),
 dict(name="Salle de bain 2", zoom=False, spoken="avec sa salle d'eau intégrée juste à côté.", prefix="avec sa salle d'eau"),
 dict(name="Chambre 3", zoom=False, spoken="Un peu plus haut, la chambre 3, avec son placard de rangement.", prefix="Un peu plus haut, la chambre 3"),
 dict(name="Salle de bain 1", zoom=False, spoken="Ici, nous avons la salle d'eau commune.", prefix="Ici, nous avons la salle d'eau"),
 dict(name="Chambre parentale", zoom=True, spoken="Et au fond, ici, nous avons la chambre parentale,", prefix="Et au fond, ici, nous avons la chambre parentale"),
 dict(name="Coin bureau", zoom=False, spoken="avec un coin bureau pour travailler au calme,", prefix="avec un coin bureau"),
 dict(name="Dressing", zoom=False, spoken="un grand dressing,", prefix="un grand dressing"),
 dict(name="Salle de bain 3", zoom=False, spoken="et sa salle de bain avec baignoire et douche.", prefix="et sa salle de bain"),
 dict(name="Final", zoom=False, spoken="Donnez votre avis sur ce plan, en commentaire.", prefix="Donnez votre avis", prefix2="Donnez votre avis sur ce plan"),
]
for s in SEGS:
    s.setdefault("sub", s["spoken"])


def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if unicodedata.category(c) != "Mn"))


def ff(*a):
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *map(str, a)], check=True)


def dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                capture_output=True, text=True).stdout.strip())


async def tts(text, mp3):
    c = edge_tts.Communicate(text, VOICE, boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append((ch["text"], round(ch["offset"] / 1e7, 3), round((ch["offset"] + ch["duration"]) / 1e7, 3)))
    return words


def prefix_end(words, prefix):
    n, acc = len(norm(prefix)), 0
    for w, s, e in words:
        acc += len(norm(w))
        if acc >= n:
            return e
    return words[-1][2]


def trim_end(src, dst):
    ff("-i", src, "-af", "silenceremove=stop_periods=1:stop_threshold=-45dB:stop_silence=0.15", "-ar", 44100, "-ac", 1, dst)


# ---------------------------------------------------------------- voix du corps
words_all, pre = {}, {}
for i, s in enumerate(SEGS, 1):
    mp3 = f"voix/sync/r{i:02d}.mp3"
    w = asyncio.run(tts(s["spoken"], mp3))
    trim_end(mp3, f"voix/sync/{i:02d}.wav")
    words_all[s["name"]] = w
    pre[s["name"]] = (prefix_end(w, s["prefix"]), prefix_end(w, s["prefix2"]) if "prefix2" in s else None)
json.dump(words_all, open("words.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump([{k: v for k, v in s.items() if k in ("name", "sub", "zoom", "spoken", "prefix", "prefix2")} for s in SEGS],
          open("voix/script.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- calage (logique de make_sync.py)
GAP, MIN_TRANSIT, NAME_BACK = 0.15, 1.3, 0.3
items, S_prev_end, T_free = [], 0.0, 0.0
for i, s in enumerate(SEGS, 1):
    d = dur(f"voix/sync/{i:02d}.wav"); p, p2 = pre[s["name"]]
    if s["name"] == "Final":
        start = max(S_prev_end + GAP, T_free)
        items.append({"name": "Final", "start": round(start, 3), "dur": round(d, 3), "end": round(start + d, 3), "final": True,
                      "dim1": round(start + max(0.2, p - 0.55), 3), "dim2": round(start + max(0.2, p2 - 0.55), 3)})
        S_prev_end = start + d
        continue
    ZIN, ZOUT = (1.2, 1.2) if s["zoom"] else (0.45, 0.5)
    arr_off = max(0.4, p - NAME_BACK)
    start = max(0.4 if i == 1 else S_prev_end + GAP, T_free + MIN_TRANSIT - arr_off)
    A = start + arr_off; E = start + d
    zo = max(A + ZIN + 0.25, E - ZOUT)
    T_free = zo + ZOUT; S_prev_end = E
    items.append({"name": s["name"], "zoom": s["zoom"], "start": round(start, 3), "dur": round(d, 3), "arrive": round(A, 3),
                  "zout_start": round(zo, 3), "end": round(E, 3)})
total = round(items[-1]["end"] + 1.0, 3)
json.dump({"total": total, "items": items}, open("voix/sync.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("corps total", total)

# ---------------------------------------------------------------- voix mixée + sous-titres (build_final.py prep)
subprocess.run([sys.executable, str(VP / "build_final.py"), "prep"], check=True)
old = (JOB.parent / "V4Z-sansB-v1" / "subs_body.ass").read_text(encoding="utf-8")
head = old.split("[Events]")[0]
new = Path("final/subs.ass").read_text(encoding="utf-8")
events = new.split("[Events]")[1]
(JOB / "subs_body.ass").write_text(head + "[Events]" + events, encoding="utf-8")
shutil.copy("final/voice_mix.m4a", JOB / "voice_mix.m4a")
shutil.copy("voix/sync.json", JOB / "sync.json")

# ---------------------------------------------------------------- hook et CTA
wh = asyncio.run(tts(HOOK, "hook.mp3"))
ff("-i", "hook.mp3", "-af", "loudnorm=I=-17:TP=-1.5:LRA=7", "-c:a", "aac", "-b:a", "192k", JOB / "hook.m4a")
hd = dur("hook.mp3")
def wstart(ws, key, nth=0):
    hits = [w for w in ws if norm(w[0]).startswith(norm(key))]
    return hits[nth][1]
def wend(ws, key, nth=0):
    hits = [w for w in ws if norm(w[0]).startswith(norm(key))]
    return hits[nth][2]
t2 = wstart(wh, "Cette"); trans = wstart(wh, "Regardons")
hook = {"items": [], "cues": {"draw1": 1.9, "t1": 0.2, "t2": round(t2, 2), "t3": round(t2 + 0.55, 2),
                              "pulse": round(wend(wh, "prendriez") + 0.05, 2), "trans": round(trans, 2), "dot": round(trans + 1.0, 2)},
        "total": round(max(trans + 1.0 + 0.9, hd + 0.2), 2), "t1_text": "3 CHAMBRES, 3 SALLES D'EAU", "t2_text": "VOUS LA PRENDRIEZ ?"}

wc = asyncio.run(tts(CTA, "cta.mp3"))
ff("-i", "cta.mp3", "-af", "loudnorm=I=-17:TP=-1.5:LRA=7", "-c:a", "aac", "-b:a", "192k", JOB / "cta.m4a")
cd = dur("cta.mp3")
tap = max(cd - 0.1, wstart(wc, "rendez") + 1.4)
btn = min(wstart(wc, "rendez"), tap - 1.5)
cta = {"items": [], "cues": {"logo": 0.0, "h1": round(max(0.3, wstart(wc, "découvrir") - 0.1), 2), "h2": round(wstart(wc, "d'autres") - 0.05, 2),
                             "button": round(btn, 2), "cursor": round(btn + 0.45, 2), "tap": round(tap, 2), "bar": round(tap + 0.4, 2),
                             "s1": round(tap + 0.55, 2), "s2": round(tap + 0.9, 2)},
       "total": round(tap + 1.5, 2), "h1_text": "DÉCOUVREZ", "h2_text": "D'AUTRES MODÈLES"}
paths = json.loads((JOB / "paths.json").read_text(encoding="utf-8"))
bump = {"band": "Villa 3 chambres  ·  plain-pied", "start_pos": paths["start"], "body_cut": 0.0, "body_end": total,
        "hook": hook, "cta": cta}
(JOB / "bump.json").write_text(json.dumps(bump, indent=1, ensure_ascii=False), encoding="utf-8")
print("hook", hook["total"], hook["cues"]); print("cta", cta["total"], cta["cues"])
