"""VSL Catalogue Premium (acheteurs de l'extrait) : piste audio mixée (voix Gradium + témoignages + musique)
et composition HyperFrames 9:16 (index.html). Usage : python3 build_vsl.py  (depuis vslhf/)."""
import json, math, subprocess
from pathlib import Path

P = Path(__file__).resolve().parent / "vsl"
A = P / "assets"
V = A / "voix"
GAP, PRE = 0.35, 0.4


def dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)], capture_output=True, text=True).stdout)


def ff(*a):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *map(str, a)], check=True)


# ---------- Témoignages (extraits, texte corrigé à la main d'après la transcription) ----------
TEMO = [
    ("ibrahim_a", "Ibrahim Sako", "Mali", [
        (0.0, 5.1, "J'ai galéré pendant des mois à trouver des modèles de plans sur internet."),
        (5.1, 10.4, "Mais un ami m'a parlé du Catalogue Premium de WooPlans."),
        (10.4, 15.5, "Et quand je l'ai obtenu, j'ai tout simplement été émerveillé."),
    ]),
    ("bassirou_a", "Mamadou Bassirou", "Sénégal", [
        (0.0, 5.0, "Ce qui est bien, c'est que dès que je fais le paiement,"),
        (5.0, 13.5, "j'ai eu immédiatement, instantanément, les accès pour consulter tous les plans."),
    ]),
    ("bassirou_b", "Mamadou Bassirou", "Sénégal", [
        (0.0, 9.1, "Je confirme honnêtement que ce sont de beaux plans, faits par de véritables professionnels."),
    ]),
    ("francis_a", "Francis Bilong", "Cameroun", [
        (0.0, 4.0, "Bonjour à tous, j'espère que vous allez bien."),
        (4.0, 11.0, "J'ai obtenu mon Catalogue Premium WooPlans et je vous le recommande."),
        (11.0, 19.0, "J'ai été très satisfait par la qualité des vues et des plans."),
    ]),
    ("renaud_a", "Renaud Traoré", "Côte d'Ivoire", [
        (0.0, 4.6, "J'ai fait une découverte que je ne voudrais pas garder pour moi seul."),
        (4.6, 9.0, "Vous avez le rêve de bâtir ? De construire la maison de vos rêves ?"),
    ]),
    ("renaud_b", "Renaud Traoré", "Côte d'Ivoire", [
        (0.0, 6.0, "Vous aurez divers plans, avec plusieurs modes de visualisation."),
        (6.0, 12.0, "Vous aurez des projections de devis estimatifs."),
    ]),
]

# ---------- Timeline ----------
segs = [f"s{i:02d}" for i in range(13)]
T = {}
t = PRE
for s in segs[:12]:
    d = dur(V / f"{s}.wav")
    T[s] = (t, d)
    t += d + GAP
t += 0.4
TT = {}
for name, *_ in TEMO:
    d = dur(A / f"{name}.mp4")
    TT[name] = (t, d)
    t += d + 0.3
t += 0.2
T["s12"] = (t, dur(V / "s12.wav"))
t += T["s12"][1] + 0.6
END = (t, 6.0)
TOTAL = round(t + 6.0, 2)

chunks = {s: json.loads((V / f"{s}.chunks.json").read_text()) for s in segs}


def at(seg, word, nth=0):
    """Temps absolu du n-ième chunk qui commence par `word` dans le segment."""
    k = 0
    for c in chunks[seg]:
        if c["text"].strip().lower().startswith(word.lower()):
            if k == nth:
                return round(T[seg][0] + c["start_s"], 2)
            k += 1
    raise KeyError((seg, word))


# ---------- Audio ----------
def build_audio():
    W = A / "_mix"
    W.mkdir(exist_ok=True)
    inputs, filt, labels = [], [], []
    k = 0
    for s in segs:
        inputs += ["-i", V / f"{s}.wav"]
        ms = int(T[s][0] * 1000)
        filt.append(f"[{k}:a]aresample=48000,loudnorm=I=-16:TP=-1.5:LRA=11,aformat=channel_layouts=stereo,adelay={ms}|{ms}[a{k}]")
        labels.append(f"[a{k}]"); k += 1
    for name, *_ in TEMO:
        inputs += ["-i", A / f"{name}.mp4"]
        ms = int(TT[name][0] * 1000)
        filt.append(f"[{k}:a]aresample=48000,highpass=f=80,loudnorm=I=-17:TP=-1.5:LRA=11,aformat=channel_layouts=stereo,afade=t=in:d=0.08,adelay={ms}|{ms}[a{k}]")
        labels.append(f"[a{k}]"); k += 1
    # Musique : basse sous la voix, encore plus basse pendant les témoignages, remonte sur la carte de fin.
    t0 = min(v[0] for v in TT.values()); t1 = max(v[0] + v[1] for v in TT.values())
    vol = (f"volume='if(between(t,{t0:.2f},{t1:.2f}),0.035,if(gte(t,{END[0]:.2f}),0.16,0.075))':eval=frame")
    inputs += ["-stream_loop", "-1", "-i", A / "music.mp3"]
    filt.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{TOTAL},{vol},afade=t=in:d=1.5,afade=t=out:st={TOTAL-2.5:.2f}:d=2.5[m]")
    labels.append("[m]")
    filt.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:dropout_transition=0,atrim=0:{TOTAL},alimiter=limit=0.95[out]")
    ff(*inputs, "-filter_complex", ";".join(filt), "-map", "[out]", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", A / "mix.m4a")


# ---------- Sous-titres ----------
WEAK = set("le la les l' de des du d' un une à au aux et ou que qui en ne pas vous votre vos nos notre son sa ses il on ce c'est pour par sur avec dans plus".split())
def caption_groups():
    out = []
    for s in segs:
        st = T[s][0]
        cur, c0, c1 = [], None, None
        for c in chunks[s]:
            for w in c["text"].split():
                pass
        # Les chunks sont des mots ou des petits groupes : on regroupe en lignes de ~24 caractères.
        words = []
        for c in chunks[s]:
            ws = c["text"].split()
            if not ws:
                continue
            span = (c["stop_s"] - c["start_s"]) / len(ws)
            for i, w in enumerate(ws):
                w = w.replace("Mobaïle", "Mobile")
                words.append((w, c["start_s"] + i * span, c["start_s"] + (i + 1) * span))
        for w, a, b in words:
            if not cur:
                c0 = a
            cur.append(w); c1 = b
            line = " ".join(cur)
            weak = w.lower().strip(",") in WEAK
            if (w[-1] in ".?!:;…") or (w[-1] == "," and len(line) >= 14) or (len(line) >= 30 and not weak):
                out.append((round(st + c0, 2), round(st + c1, 2), line)); cur = []
        if cur:
            out.append((round(st + c0, 2), round(st + c1, 2), " ".join(cur)))
    for name, _n, _p, lines in TEMO:
        t0 = TT[name][0]
        for a, b, text in lines:
            # découpe en morceaux de ~5 mots répartis sur la durée
            ws = text.split(); n = max(1, math.ceil(len(ws) / 5)); per = (b - a) / n
            for i in range(n):
                out.append((round(t0 + a + i * per, 2), round(t0 + a + (i + 1) * per, 2), " ".join(ws[i * 5:(i + 1) * 5])))
    s = "s12"; st = T[s][0]
    out.sort()
    merged = []
    for a, b, x in out:
        if merged and len(x.split()) == 1 and len(x) <= 9 and a - merged[-1][1] < 0.2 and len(merged[-1][2]) + len(x) <= 44:
            pa, _pb, px = merged[-1]; merged[-1] = (pa, b, px + " " + x)
        else:
            merged.append((a, b, x))
    out = merged
    # fermer les trous courts pour éviter le clignotement
    res = []
    for i, (a, b, x) in enumerate(out):
        if i + 1 < len(out) and out[i + 1][0] - b < 0.3:
            b = out[i + 1][0]
        res.append((a, max(b, a + 0.35), x))
    return res


# ---------- Plans visuels ----------
shots = []   # (start, dur, kind, src, extra)
texts = []   # (start, dur, html, cls)


def img(a, b, src, cls="kb-in", note=None):
    shots.append((a, b - a, "img", src, cls))
    if note:
        texts.append((a + 0.3, b - a - 0.3, note, "note"))


def vid(a, b, src, mstart=0.0):
    shots.append((a, b - a, "vid", src, mstart))


def seg_end(s):
    return round(T[s][0] + T[s][1] + GAP, 2)


HOOK = ["hook/h01-d4-019.jpg", "hook/h03-d5-019.jpg", "hook/h05-d5-018.jpg", "hook/h04-d4-017.jpg", "hook/h07-d4-016.jpg",
        "hook/h08-d4-009.jpg", "hook/h10-d4-001.jpg", "hook/h02-d4-019n.jpg", "hook/h09-d4-009n.jpg",
        "hook/h04-d4-017.jpg", "rendu1.jpg"]


def build_shots():
    # Accroche (refaite, remarque de Tao) : nos plus beaux duplex. 1) trois maisons empilées qui défilent,
    # 2) coupes rapides plein écran avec zoom, 3) la question sur une façade de nuit.
    s = "s00"; e = seg_end(s)
    q = e - 3.0
    shots.append((0.0, 3.4, "tri", None, HOOK[:9]))
    PUNCH = ["hook/h10-d4-001.jpg", "hook/h02-d4-019n.jpg", "hook/h05-d5-018.jpg", "hook/h09-d4-009n.jpg"]
    step = (q - 3.4) / len(PUNCH)
    for i, p in enumerate(PUNCH):
        img(3.4 + i * step, 3.4 + (i + 1) * step, p, "kb-punch")
    img(q, e, "hook/h06-d5-018n.jpg", "kb-in dim")
    texts.append((q + 0.05, e - q - 0.05, "Et si vous choisissiez<br><em>la mauvaise maison&nbsp;?</em>", "hook"))
    # Preuve : catalogue de Tao + compteurs.
    s = "s01"; a = seg_end("s00"); e = seg_end(s)
    vid(a, at(s, "Plus"), "c00.mp4")
    img(at(s, "Plus"), at(s, "Et"), "chantier-arrete.png", "kb-in")
    img(at(s, "Et"), e, "maison-abidjan-d4-001.png", "kb-out", "Illustration d'après le modèle D4-001")
    texts.append((a + 0.6, e - a - 0.6, "", "counters"))
    # Douleurs.
    s = "s02"; a = seg_end("s01"); e = seg_end(s)
    p1, p2, p3 = at(s, "Un"), at(s, "Deux"), at(s, "Trois")
    img(a, p2, "telephone-nuit.png", "kb-in")
    img(p2, p3, "devis-compare.png", "kb-out")
    img(p3, e, "bureau-architecte.png", "kb-in")
    texts.append((p1, p2 - p1, "<b>1</b>Le manque d'idées", "pain"))
    texts.append((p2, p3 - p2, "<b>2</b>Des devis gonflés", "pain"))
    texts.append((p3, e - p3, "<b>3</b>L'architecte&nbsp;: 2 ou 3 propositions, payantes", "pain"))
    # Histoire.
    s = "s03"; a = seg_end("s02"); e = seg_end(s)
    m1 = at(s, "Puis"); m2 = at(s, "Ce")
    img(a, m1, "bureau-architecte.png", "kb-out gray")
    vid(m1, m1 + 4.6, "c03.mp4")
    img(m1 + 4.6, m2, "rendu1.jpg", "kb-in")
    img(m2, e, "villa-douala-v3-037.png", "kb-out", "Illustration d'après le modèle V3-037")
    texts.append((a + 0.3, 3.5, "L'histoire d'un client", "kicker"))
    # Promesse, 3 étapes, image du succès.
    s = "s04"; a = seg_end("s03"); e = seg_end(s)
    u1, u2, u3, im = at(s, "Un,"), at(s, "Deux,"), at(s, "Trois,"), at(s, "Imaginez")
    img(a, u1, "couple-tablette-douala.png", "kb-in")
    shots.append((u1, im - u1, "steps", None, (u1, u2, u3)))
    img(im, e, "maison-abidjan-d4-001.png", "kb-out", "Illustration d'après le modèle D4-001")
    # Mécanisme unique.
    s = "s05"; a = seg_end("s04"); e = seg_end(s)
    w1 = at(s, "Avec"); w2 = at(s, "Pour"); w3 = at(s, "On", 1)
    shots.append((a, w1 - a, "split", None, None))
    img(w1, w2, "couple-tablette-douala.png", "kb-out")
    texts.append((w1 + 0.2, 3.2, "Avec WooPlans, on inverse tout", "kicker"))
    third = (w3 - w2) / 3
    vid(w2, w2 + third, "c10.mp4")
    vid(w2 + third, w2 + 2 * third, "c11.mp4")
    vid(w2 + 2 * third, w3, "c08.mp4")
    img(w3, e, "villa-douala-v3-037.png", "kb-in", "Illustration d'après le modèle V3-037")
    # Objections.
    objs = [
        ("s06", "« C'est trop cher »", [("brouette.png", None), ("billets.png", None)]),
        ("s07", "« Des plans gratuits sur internet&nbsp;? »", [("rendu2.jpg", "blur"), ("c07.mp4", None), ("c09.mp4", None)]),
        ("s08", "« Les prix ne sont pas ceux de mon pays »", [("devis-compare.png", None), ("c04.mp4", None)]),
        ("s09", "« Je construis directement avec&nbsp;? »", [("c01.mp4", None), ("c03.mp4", None)]),
        ("s10", "« Et si c'est une arnaque&nbsp;? »", [("couple-tablette-douala.png", "dim")]),
    ]
    prev = "s05"
    for s, title, media in objs:
        a = seg_end(prev); e = seg_end(s); prev = s
        n = len(media); step = (e - a) / n
        for i, (m, opt) in enumerate(media):
            if m.endswith(".mp4"):
                vid(a + i * step, a + (i + 1) * step, m)
            else:
                img(a + i * step, a + (i + 1) * step, m, "kb-in " + (opt or ""))
        texts.append((a + 0.1, min(4.5, e - a - 0.2), title, "objection"))
    s = "s06"
    texts.append((at(s, "vingt-neuf") if any(c["text"].lower().startswith("vingt") for c in chunks[s]) else T[s][0] + 4, 5.0, "29&nbsp;000 FCFA<small>moins qu'une brouette (≈ 35&nbsp;000 FCFA)</small>", "bigprice"))
    s = "s10"
    texts.append((T[s][0] + 4.0, seg_end(s) - T[s][0] - 4.0, "Remboursé sous 7 jours<small>un simple message, sans question</small>", "badge"))
    # Appel principal.
    s = "s11"; a = seg_end("s10"); e = TT["ibrahim_a"][0]
    shots.append((a, e - a, "offer", None, None))
    # Témoignages.
    for name, who, country, _l in TEMO:
        a0, d0 = TT[name]
        if name.startswith("renaud"):
            shots.append((a0 - 0.15, d0 + 0.45, "audio-temo", name, (who, country)))
        else:
            shots.append((a0 - 0.15, d0 + 0.45, "temo", name, (who, country)))
    # Chiffres en rafale entre les témoignages : petits bandeaux.
    # Fin.
    a = TT["renaud_b"][0] + TT["renaud_b"][1] + 0.3
    img(a, END[0], "maison-abidjan-d4-001.png", "kb-in")
    shots.append((END[0], END[1], "offer-end", None, None))


def html():
    caps = caption_groups()
    build_shots()
    parts, js = [], []
    for i, (a, d, kind, src, ex) in enumerate(sorted(shots, key=lambda x: x[0])):
        sid = f"sh{i}"
        common = f'id="{sid}" class="clip shot" data-start="{a:.2f}" data-duration="{d:.2f}"'
        if kind == "img":
            parts.append(f'<div {common}><img class="bg {ex}" src="assets/{src}"></div>')
            cls = ex.split()[0]
            fr, to = {"kb-in": (1.0, 1.12), "kb-out": (1.14, 1.0), "kb-fast": (1.0, 1.18), "kb-punch": (1.28, 1.05)}.get(cls, (1.0, 1.1))
            js.append(f'tl.fromTo("#{sid} .bg",{{scale:{fr}}},{{scale:{to},duration:{d:.2f},ease:"none"}},{a:.2f});')
            js.append(f'tl.fromTo("#{sid}",{{opacity:0}},{{opacity:1,duration:{0.06 if cls == "kb-punch" else 0.25}}},{a:.2f});')
            if cls == "kb-punch":
                js.append(f'tl.fromTo("#{sid} .bg",{{filter:"brightness(2.2)"}},{{filter:"brightness(1)",duration:0.22}},{a:.2f});')
        elif kind == "vid":
            parts.append(f'<video {common} class="clip shot vid" src="assets/{src}" data-media-start="{ex}" muted playsinline></video>'.replace(f'class="clip shot" ', ""))
        elif kind == "tri":
            pics = ex
            rows = "".join(f'<div class="row r{r}">' + "".join(f'<img src="assets/{pics[r*3+k]}">' for k in range(3)) + "</div>" for r in range(3))
            parts.append(f'<div {common} style="background:#000"><div class="tri">{rows}</div></div>')
            for r in range(3):
                sign = -1 if r % 2 == 0 else 1
                for k in range(3):
                    t0 = a + r * 0.12 + k * 1.05
                    js.append(f'tl.fromTo("#{sid} .r{r} img:nth-child({k+1})",{{xPercent:{-100*sign},scale:1.15}},{{xPercent:0,scale:1,duration:0.38,ease:"expo.out"}},{t0:.2f});')
            js.append(f'tl.fromTo("#{sid} .tri",{{scale:1}},{{scale:1.06,duration:{d:.2f},ease:"none"}},{a:.2f});')
        elif kind == "black":
            parts.append(f'<div {common} style="background:#050807"></div>')
        elif kind == "steps":
            u1, u2, u3 = ex
            parts.append(f'''<div {common} style="background:var(--ground)"><div class="steps">
<div class="step" id="st1"><b>1</b><span>Vous obtenez le catalogue</span></div>
<div class="step" id="st2"><b>2</b><span>Vous choisissez votre modèle, nos architectes l'adaptent avec vous</span></div>
<div class="step" id="st3"><b>3</b><span>Vous recevez votre plan complet, personnalisé</span></div></div></div>''')
            for k, u in enumerate((u1, u2, u3), 1):
                js.append(f'tl.fromTo("#st{k}",{{opacity:0,x:-80}},{{opacity:1,x:0,duration:0.5,ease:"power3.out"}},{u:.2f});')
        elif kind == "split":
            parts.append(f'''<div {common} style="background:#050807"><div class="split">
<div class="half before"><img src="assets/bureau-architecte.png"><span>Avant</span><ul><li>Une avance à payer</li><li>Un seul plan</li><li>Aucune idée du coût réel</li></ul></div>
<div class="half after"><img src="assets/couple-tablette-douala.png"><span>Avec WooPlans</span><ul><li>Tout le catalogue chez vous</li><li>Le devis de chaque maison</li><li>Vous choisissez, puis on adapte</li></ul></div></div></div>''')
            js.append(f'tl.fromTo("#{sid} .before",{{x:-600,opacity:0}},{{x:0,opacity:1,duration:0.6,ease:"power3.out"}},{a+0.2:.2f});')
            js.append(f'tl.fromTo("#{sid} .after",{{x:600,opacity:0}},{{x:0,opacity:1,duration:0.6,ease:"power3.out"}},{a+d*0.55:.2f});')
            js.append(f'tl.fromTo("#{sid} .before li",{{opacity:0,y:20}},{{opacity:1,y:0,stagger:{d*0.12:.2f},duration:0.3}},{a+0.8:.2f});')
            js.append(f'tl.fromTo("#{sid} .after li",{{opacity:0,y:20}},{{opacity:1,y:0,stagger:0.5,duration:0.3}},{a+d*0.55+0.6:.2f});')
        elif kind in ("offer", "offer-end"):
            end = kind == "offer-end"
            parts.append(f'''<div {common} style="background:{'rgba(5,8,7,.78)' if end else 'var(--ground)'}"><div class="offer">
<div class="o-kicker">Votre prix réservé</div>
<div class="o-old">Prix public&nbsp;: <s>39&nbsp;000 FCFA</s></div>
<div class="o-new">29&nbsp;000 <i>FCFA</i></div>
<div class="o-when">Réduction valable 7 jours</div>
<div class="o-pay">Mobile Money ou carte · accès immédiat</div></div></div>''')
            base = a + 0.2
            seq = [(".o-kicker", 0), (".o-old", 0.5), (".o-new", 1.6), (".o-when", 4.6), (".o-pay", 7.0)] if not end else [(".o-kicker", 0), (".o-old", 0.2), (".o-new", 0.4), (".o-when", 0.7), (".o-pay", 1.0)]
            for sel, off in seq:
                js.append(f'tl.fromTo("#{sid} {sel}",{{opacity:0,y:40}},{{opacity:1,y:0,duration:0.45,ease:"power3.out"}},{base+off:.2f});')
            js.append(f'tl.fromTo("#{sid} .o-old s",{{"--strike":"0%"}},{{"--strike":"100%",duration:0.5}},{base+(1.2 if not end else 0.5):.2f});')
            js.append(f'tl.to("#{sid} .o-new",{{scale:1.05,duration:0.6,yoyo:true,repeat:{max(1, int((d - 3) // 1.2))},ease:"sine.inOut"}},{base+2.4:.2f});')
        elif kind == "temo":
            who, country = ex
            parts.append(f'<video id="{sid}" class="clip vid" src="assets/{src}.mp4" data-start="{a:.2f}" data-duration="{d:.2f}" data-media-start="0" muted playsinline></video>')
            parts.append(f'<div id="{sid}w" class="clip overlay" data-start="{a:.2f}" data-duration="{d:.2f}"><div class="who"><b>{who}</b><span>{country} · client WooPlans</span></div></div>')
            js.append(f'tl.fromTo("#{sid}w .who",{{opacity:0,x:-60}},{{opacity:1,x:0,duration:0.5}},{a+0.4:.2f});')
        elif kind == "audio-temo":
            who, country = ex
            parts.append(f'''<div {common}><img class="bg blurbg" src="assets/renaud.jpg"><img class="portrait" src="assets/renaud.jpg">
<div class="wave">{''.join('<i></i>' for _ in range(28))}</div><div class="audio-tag">Témoignage audio</div>
<div class="who"><b>{who}</b><span>{country} · client WooPlans</span></div></div>''')
            js.append(f'tl.fromTo("#{sid} .who",{{opacity:0,x:-60}},{{opacity:1,x:0,duration:0.5}},{a+0.4:.2f});')
            # onde sonore : hauteur des barres d'après l'enveloppe réelle de l'audio (12 images/s)
            env = envelope(A / f"{src}.mp4", 12)
            t0 = TT[src][0]
            for b in range(28):
                keys = []
                for f, v in enumerate(env):
                    h = 0.07 + 0.93 * min(1, v * (0.3 + 0.7 * math.sin(b * 1.7 + f * 0.9) ** 2) * (0.35 + 0.65 * math.exp(-((b - 13.5) / 7) ** 2)))
                    keys.append(round(h, 2))
                js.append(f'tl.to("#{sid} .wave i:nth-child({b+1})",{{keyframes:{json.dumps([{"scaleY": h, "duration": round(1/12, 3)} for h in keys])},ease:"none"}},{t0:.2f});')
    for a, d, h, cls in texts:
        i = len(parts)
        tid = f"tx{i}"
        if cls == "counters":
            parts.append(f'''<div id="{tid}" class="clip overlay" data-start="{a:.2f}" data-duration="{d:.2f}"><div class="counters">
<div><b data-to="12">0</b><span>ans de BTP</span></div><div><b data-to="150">0</b><span>chantiers suivis</span></div>
<div><b data-to="283">0</b><span>familles clientes</span></div><div><b data-to="16">0</b><span>pays</span></div></div></div>''')
            for k, (n, off) in enumerate([(12, 0.3), (150, 1.8), (283, 6.0), (16, 7.5)]):
                js.append(f'tl.fromTo("#{tid} .counters div:nth-child({k+1})",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.4}},{a+off:.2f});')
                js.append(f'tl.fromTo("#{tid} .counters div:nth-child({k+1}) b",{{textContent:0}},{{textContent:{n},duration:1.2,snap:{{textContent:1}},ease:"power2.out"}},{a+off:.2f});')
            continue
        parts.append(f'<div id="{tid}" class="clip overlay {cls}" data-start="{a:.2f}" data-duration="{d:.2f}"><div class="inner">{h}</div></div>')
        js.append(f'tl.fromTo("#{tid} .inner",{{opacity:0,y:30,scale:.96}},{{opacity:1,y:0,scale:1,duration:0.45,ease:"power3.out"}},{a:.2f});')
    for i, (a, b, x) in enumerate(caps):
        parts.append(f'<div class="clip cap" data-start="{a:.2f}" data-duration="{b-a:.2f}"><span>{x}</span></div>')
    # Filigranes mobiles retirés (demande de Tao, 23 nov.).
    parts.append(f'<audio id="voixmix" class="clip" src="assets/mix.m4a" data-start="0" data-duration="{TOTAL}" data-has-audio="true"></audio>')
    return TEMPLATE.replace("{{TOTAL}}", str(TOTAL)).replace("{{BODY}}", "\n".join(parts)).replace("{{JS}}", "\n".join(js))


def envelope(f, fps):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(f), "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True).stdout
    import array
    s = array.array("h", raw)
    step = 8000 // fps
    out = []
    for i in range(0, len(s), step):
        w = s[i:i + step]
        out.append(math.sqrt(sum(v * v for v in w) / max(1, len(w))) / 32768 if w else 0)
    m = max(out) or 1
    return [min(1, v / m * 1.2) for v in out]


TEMPLATE = """<!doctype html>
<html lang="fr" data-resolution="portrait">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=1080, height=1920">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
:root{--ground:#0b1410;--ink:#fff;--accent:#f39a1e;--green:#1f7a4d;--font:"Inter",sans-serif}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:var(--ground)}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;font-family:var(--font);color:var(--ink)}
.clip{position:absolute;inset:0}
.shot{overflow:hidden}
.bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transform-origin:50% 50%}
.bg.gray{filter:grayscale(1) brightness(.75)}
.bg.blur{filter:blur(14px) brightness(.6)}
.bg.dim{filter:brightness(.45)}
.tri{position:absolute;inset:0;display:flex;flex-direction:column;gap:12px;padding:0;background:#000}
.tri .row{position:relative;flex:1;overflow:hidden}
.tri .row img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
video.vid{width:1080px;height:1920px;object-fit:cover}
.shot::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.35) 0%,rgba(0,0,0,0) 22%,rgba(0,0,0,0) 55%,rgba(0,0,0,.55) 100%);pointer-events:none}
.overlay{display:flex;justify-content:center;pointer-events:none}
.overlay .inner{position:absolute;text-align:center}
.hook{align-items:center}.hook .inner{top:700px;left:60px;right:60px;font-size:92px;font-weight:800;line-height:1.08;letter-spacing:-.02em}
.hook em{font-style:normal;color:var(--accent)}
.kicker .inner{top:170px;left:60px;right:60px;font-size:54px;font-weight:800;background:var(--accent);color:#111;padding:18px 28px;border-radius:18px;width:fit-content;margin:auto}
.objection .inner{top:180px;left:50px;right:50px;font-size:72px;font-weight:800;line-height:1.1;background:rgba(11,20,16,.86);border-left:14px solid var(--accent);padding:30px 34px;border-radius:22px;text-align:left}
.pain .inner{top:200px;left:50px;right:50px;font-size:60px;font-weight:800;line-height:1.12;background:rgba(11,20,16,.86);padding:28px 34px;border-radius:22px;text-align:left;display:flex;gap:26px;align-items:center}
.pain b{flex:none;width:96px;height:96px;border-radius:50%;background:var(--accent);color:#111;display:flex;align-items:center;justify-content:center;font-size:58px}
.note .inner{bottom:150px;right:40px;font-size:26px;font-weight:600;color:rgba(255,255,255,.85);background:rgba(0,0,0,.45);padding:8px 16px;border-radius:10px}
.bigprice .inner{top:620px;left:40px;right:40px;font-size:150px;font-weight:800;color:var(--accent);text-shadow:0 8px 40px rgba(0,0,0,.6);line-height:1}
.bigprice small,.badge small{display:block;font-size:44px;color:#fff;font-weight:700;margin-top:24px}
.badge .inner{top:640px;left:70px;right:70px;font-size:78px;font-weight:800;background:var(--green);padding:46px 30px;border-radius:36px;border:6px solid #fff;line-height:1.1}
.counters{position:absolute;top:1000px;left:50px;right:50px;display:grid;grid-template-columns:1fr 1fr;gap:26px}
.counters div{background:rgba(11,20,16,.85);border-radius:24px;padding:26px 20px;text-align:center}
.counters b{display:block;font-size:110px;font-weight:800;color:var(--accent);line-height:1}
.counters span{font-size:38px;font-weight:700}
.steps{position:absolute;top:420px;left:60px;right:60px;display:flex;flex-direction:column;gap:46px}
.step{display:flex;gap:34px;align-items:center;background:rgba(255,255,255,.06);border:3px solid rgba(255,255,255,.14);border-radius:30px;padding:36px}
.step b{flex:none;width:130px;height:130px;border-radius:50%;background:var(--accent);color:#111;font-size:80px;font-weight:800;display:flex;align-items:center;justify-content:center}
.step span{font-size:52px;font-weight:800;line-height:1.15}
.split{position:absolute;inset:0;display:flex;flex-direction:column}
.half{position:relative;flex:1;overflow:hidden}
.half img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.before img{filter:grayscale(1) brightness(.5)}
.after img{filter:brightness(.6)}
.half span{position:absolute;top:60px;left:50px;font-size:64px;font-weight:800;padding:8px 26px;border-radius:14px}
.before span{background:#555}.after span{background:var(--accent);color:#111}
.half ul{position:absolute;top:180px;left:50px;right:50px;list-style:none;font-size:52px;font-weight:800;line-height:1.5}
.before li::before{content:"✕ ";color:#ff6b5b}.after li::before{content:"✓ ";color:#5bdc8c}
.offer{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:40px;text-align:center;padding:0 60px}
.o-kicker{font-size:52px;font-weight:800;color:var(--accent);text-transform:uppercase;letter-spacing:.04em}
.o-old{font-size:56px;font-weight:700;color:rgba(255,255,255,.75)}
.o-old s{text-decoration:none;position:relative;--strike:0%}
.o-old s::after{content:"";position:absolute;left:0;top:52%;height:7px;width:var(--strike);background:#ff5b4b}
.o-new{font-size:190px;font-weight:800;line-height:1;color:#fff}.o-new i{font-style:normal;font-size:80px;color:var(--accent)}
.o-when{font-size:58px;font-weight:800;line-height:1.2;background:var(--accent);color:#111;padding:22px 40px;border-radius:999px}.o-when small{font-size:36px;color:rgba(255,255,255,.75);font-weight:600}
.o-btn{background:var(--accent);color:#111;font-size:56px;font-weight:800;padding:40px 56px;border-radius:999px;box-shadow:0 14px 50px rgba(243,154,30,.45)}
.o-pay{font-size:34px;font-weight:600;color:rgba(255,255,255,.8)}
.tv-bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:blur(30px) brightness(.5);transform:scale(1.2)}
.tv{position:absolute;left:0;top:160px;width:1080px;height:1600px;object-fit:contain}
.who{position:absolute;left:50px;top:110px;background:rgba(11,20,16,.88);border-left:12px solid var(--accent);padding:20px 30px;border-radius:16px}
.who b{display:block;font-size:54px;font-weight:800}.who span{font-size:36px;font-weight:600;color:rgba(255,255,255,.85)}
.blurbg{filter:blur(36px) brightness(.45);transform:scale(1.2)}
.portrait{position:absolute;left:290px;top:440px;width:500px;height:500px;border-radius:50%;object-fit:cover;border:10px solid var(--accent)}
.wave{position:absolute;left:110px;right:110px;top:1040px;height:300px;display:flex;align-items:center;justify-content:space-between}
.wave i{display:block;width:20px;height:300px;background:var(--accent);border-radius:10px;transform:scaleY(.12)}
.audio-tag{position:absolute;top:1380px;left:0;right:0;text-align:center;font-size:36px;font-weight:700;color:rgba(255,255,255,.8)}
.cap{display:flex;justify-content:center;pointer-events:none}
.cap span{position:absolute;bottom:330px;max-width:980px;text-align:center;font-size:62px;font-weight:800;line-height:1.15;color:#fff;
 text-shadow:0 0 6px #000,0 4px 14px rgba(0,0,0,.9);-webkit-text-stroke:2px #000;paint-order:stroke fill}
.wm{width:250px;height:auto;opacity:.28;inset:auto;left:0;top:0;z-index:50}
.overlay{z-index:20}.cap{z-index:30}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{{TOTAL}}" data-width="1080" data-height="1920">
{{BODY}}
</div>
<script>
window.__timelines = window.__timelines || {};
const tl = gsap.timeline({ paused: true });
{{JS}}
window.__timelines["main"] = tl;
tl.seek(0);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    import sys
    out = html()
    (P / "index.html").write_text(out, encoding="utf-8")
    if "--no-audio" not in sys.argv:
        build_audio()
    print("durée totale", TOTAL, "s ; témoignages à", {k: round(v[0], 1) for k, v in TT.items()})
