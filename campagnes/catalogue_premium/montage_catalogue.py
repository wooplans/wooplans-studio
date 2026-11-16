"""Montage final de la vidéo « Catalogue Premium » (9:16) à partir des rushes de Tao (16 nov. 2026).

Sources (hors dépôt, trop lourdes) dans MEDIA :
  catalogue_raw.mp4   vidéo de Tao : catalogue imprimé puis version numérique sur téléphone (voix de Tao)
  9020c555.wav        audio de Tao « Voici quelques témoignages… »
  10d75772.wav        audio de Tao sur le prix (seuls « notre catalogue est actuellement » + « au prix de 29 000 francs »
                      sont gardés : pas de « promotion limitée » ni de prix barré non sourcé, cf. CLAUDE.md)
  temoignages/*.mp4   vrais témoignages clients publiés sur wooplans.com (src/lib/testimonials.ts du site)

Rendu : python campagnes/catalogue_premium/montage_catalogue.py [MEDIA] → MEDIA/out/catalogue-premium-9x16.mp4
"""
import subprocess, sys, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
MEDIA = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/user/media/catalogue")
WORK = MEDIA / "work"; OUT = MEDIA / "out"
WORK.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
FONTS = Path("/home/user/wooplans/scripts/guide/cache/fonts")
WM = ROOT / "assets" / "brand" / "wm_logo.png"
LOGO = ROOT / "assets" / "brand" / "logo_white.png"
MUSIC = ROOT / "assets" / "music" / "Africa_Arulo_mixkit-218.mp3"
W, H, FPS = 1080, 1920, 30
GREEN, ORANGE, YELLOW = (15, 92, 87), (240, 140, 40), (245, 200, 80)

def ff(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, a)], check=True)

def font(w, s):
    return ImageFont.truetype(str(FONTS / f"Montserrat-{w}.ttf"), s)

# ---------------------------------------------------------------- plan de montage
# (source, début, fin, étiquette, sous-titre). Sous-titres relus (transcription corrigée à la main).
RAW = MEDIA / "catalogue_raw.mp4"
CLIPS = [
    (RAW, 2.55, 7.95, "Le Catalogue Premium", "Une collection qui contient plus de 100 plans"),
    (RAW, 8.90, 10.95, "Rendus 3D", "Pour chaque plan,"),
    (RAW, 14.35, 17.10, "Rendus 3D", "on a les images de rendu"),
    (RAW, 19.90, 24.50, "Plan de distribution coté", "Le plan de distribution avec les dimensions de chaque pièce"),
    (RAW, 26.70, 37.50, "Devis par lot", "Le devis par lot : fondation, élévation, dalle… jusqu'aux finitions, et le coût total"),
    (RAW, 47.45, 55.90, "Duplex et villas", "Les plans de duplex et, de l'autre côté, les plans de villas"),
    (RAW, 57.65, 66.00, "Pour choisir votre maison", "Le document idéal pour faire un choix et lancer votre projet de construction"),
    (RAW, 86.90, 93.70, "Version numérique", "Ça, c'est le document physique. Voici la version numérique du même document"),
    (RAW, 93.80, 99.40, "Version numérique", "Tous les plans directement sur votre téléphone"),
    (RAW, 103.05, 105.65, "Version numérique", "Parcourez les images de chaque modèle"),
    (RAW, 106.60, 112.70, "Plan coté sur téléphone", "Le plan de distribution de chaque modèle, avec les dimensions"),
    (RAW, 113.70, 120.30, "Devis sur téléphone", "Et le devis de chaque modèle, sur votre téléphone"),
    (RAW, 121.45, 131.50, "Nouveaux plans inclus", "Nous ajoutons régulièrement des plans, et vous avez accès aux nouveaux"),
]
TEMO = [  # (fichier, début, fin, nom, pays, sous-titre)
    ("ibrahim.mp4", 10.50, 25.05, "M. Ibrahim Sako", "Mali",
     "J'ai galéré pendant des mois à trouver des modèles de plans sur internet. Un ami m'a parlé du Catalogue Premium de WooPlans, et quand je l'ai eu, j'ai été émerveillé."),
    ("francis.mp4", 4.60, 10.60, "M. Francis Bilong", "Cameroun", "J'ai obtenu mon Catalogue Premium WooPlans et je vous le recommande."),
    ("bassirou.mp4", 37.40, 46.40, "M. Mamadou Bassirou", "Sénégal", "Je confirme honnêtement : ce sont de beaux plans, faits par de véritables professionnels."),
]

def zoom_filter(d, i):
    z0, z1 = (1.0, 1.07) if i % 2 == 0 else (1.07, 1.0)   # zoom lent avant / arrière, alterné
    return (f"scale=w='trunc({W}*({z0}+({z1}-{z0})*t/{d:.3f})/2)*2':h=-2:eval=frame,"
            f"crop={W}:{H}:(iw-{W})/2:(ih-{H})/2,setsar=1,fps={FPS}")

AUD = "aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.5:LRA=11"

def cut(src, a, b, out, i, blur_bg=False):
    d = b - a
    if blur_bg:   # témoignage basse définition : fond flouté + vidéo pleine largeur
        vf = (f"[0:v]split[x][y];[x]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:2[bg];"
              f"[y]scale={W}:-2[fg];[bg][fg]overlay=0:(H-h)/2,setsar=1,fps={FPS}[v]")
    else:
        vf = f"[0:v]{zoom_filter(d, i)}[v]"
    ff("-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", src, "-filter_complex", vf + f";[0:a]{AUD},afade=t=in:d=0.04,afade=t=out:st={d-0.06:.3f}:d=0.06[a]",
       "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out)
    return d

def card_video(img, audio, out, d, audio_start=0.0):
    """Image fixe (sans zoom : les bords de la carte restent visibles) + piste audio."""
    vf = f"[0:v]scale={W}:{H},setsar=1,fps={FPS}[v]"
    inputs = ["-loop", "1", "-t", f"{d:.3f}", "-i", img]
    if audio:
        inputs += ["-i", audio]; af = f"[1:a]{AUD},apad,atrim=0:{d:.3f}[a]"
    else:
        inputs += ["-f", "lavfi", "-t", f"{d:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]; af = "[1:a]anull[a]"
    ff(*inputs, "-filter_complex", vf + ";" + af, "-map", "[v]", "-map", "[a]", "-t", f"{d:.3f}",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out)

def wrap(draw, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    return lines + [cur]

# ---------------------------------------------------------------- cartes (PIL)
def testimonials_card(path):
    im = Image.new("RGB", (W, H), GREEN); d = ImageDraw.Draw(im)
    thumbs = []
    for n, t in [("ibrahim", 12), ("francis", 6), ("bassirou", 40)]:
        p = WORK / f"th_{n}.jpg"; ff("-ss", t, "-i", MEDIA / "temoignages" / f"{n}.mp4", "-frames:v", 1, p); thumbs.append(Image.open(p))
    thumbs.append(Image.open(MEDIA / "temoignages" / "renaud.webp").convert("RGB"))
    tw, th = 400, 711
    for k, t in enumerate(thumbs):
        t = t.resize((tw, int(t.height * tw / t.width))).crop((0, 0, tw, th))
        x, y = (W - 2 * tw - 40) // 2 + (k % 2) * (tw + 40), 330 + (k // 2) * (th + 40)
        m = Image.new("L", (tw, th), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, tw, th), 36, fill=255)
        im.paste(t, (x, y), m)
    d.text((W // 2, 120), "Ils ont acheté", font=font(800, 76), fill="white", anchor="mm")
    d.text((W // 2, 210), "le Catalogue Premium", font=font(800, 76), fill=YELLOW, anchor="mm")
    im.save(path, quality=95)

def end_card(path):
    im = Image.new("RGB", (W, H), GREEN); d = ImageDraw.Draw(im)
    logo = Image.open(LOGO).convert("RGBA"); logo = logo.resize((360, int(logo.height * 360 / logo.width)))
    im.paste(logo, ((W - logo.width) // 2, 170), logo)
    y = 170 + logo.height + 110
    for line, f, c in [("Catalogue Premium", font(800, 92), "white"), ("100 villas et duplex", font(700, 58), YELLOW)]:
        d.text((W // 2, y), line, font=f, fill=c, anchor="mm"); y += 110
    y += 40
    for t in ["Rendus 3D de chaque modèle", "Plans de distribution cotés", "Devis par lot jusqu'aux finitions", "Nouveaux plans inclus"]:
        d.line([(176, y + 2), (192, y + 18), (222, y - 16)], fill=YELLOW, width=9, joint="curve")
        d.text((250, y), t, font=font(600, 48), fill="white", anchor="lm"); y += 84
    y += 60
    d.rounded_rectangle((120, y, W - 120, y + 200), 40, fill="white")
    d.text((W // 2, y + 62), "Prix actuel", font=font(600, 44), fill=GREEN, anchor="mm")
    d.text((W // 2, y + 140), "29 000 FCFA", font=font(800, 84), fill=GREEN, anchor="mm")
    y += 250
    d.text((W // 2, y + 20), "Version numérique : espace en ligne + fiches PDF", font=font(600, 38), fill="white", anchor="mm")
    d.rounded_rectangle((170, y + 90, W - 170, y + 230), 70, fill=ORANGE)
    d.text((W // 2, y + 160), "wooplans.com", font=font(800, 70), fill="white", anchor="mm")
    im.save(path, quality=95)

# ---------------------------------------------------------------- sous-titres ASS
def ass_time(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60); return f"{int(h)}:{int(m):02d}:{s:05.2f}"

def build_ass(events, path):
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Montserrat Thin ExtraBold,68,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,3,18,0,2,90,90,330,1
Style: Label,Montserrat Thin ExtraBold,50,&H00000000,&H00FFFFFF,&H0050C8F5,&H0050C8F5,0,0,0,0,100,100,0,0,3,16,0,7,70,70,150,1
Style: Name,Montserrat Thin ExtraBold,54,&H00FFFFFF,&H00FFFFFF,&H00575C0F,&H00575C0F,0,0,0,0,100,100,0,0,3,16,0,8,70,70,170,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [f"Dialogue: 0,{ass_time(a)},{ass_time(b)},{st},,0,0,0,,{{\\fad(120,120)}}{txt}" for a, b, st, txt in events]
    path.write_text(hdr + "\n".join(lines) + "\n", encoding="utf-8")

def sub_chunks(text, a, b, maxw=22):
    """Découpe un sous-titre en morceaux de ~2 lignes répartis au prorata du nombre de caractères."""
    words, chunks, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > maxw * 2 and cur: chunks.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    chunks.append(cur)
    total = sum(len(c) for c in chunks); t = a; out = []
    for c in chunks:
        d = (b - a) * len(c) / total; out.append((t, t + d, c)); t += d
    return out

# ---------------------------------------------------------------- rendu
def main():
    parts, events, t = [], [], 0.0
    for i, (src, a, b, label, sub) in enumerate(CLIPS):
        p = WORK / f"c{i:02d}.mp4"; d = cut(src, a, b, p, i); parts.append(p)
        if i == 0:
            events.append((t, t + d, "Label", "LE CATALOGUE PREMIUM WOOPLANS"))
        elif label != CLIPS[i - 1][3]:
            j = i; e = t + d
            while j + 1 < len(CLIPS) and CLIPS[j + 1][3] == label: j += 1; e += CLIPS[j][2] - CLIPS[j][1]
            events.append((t, e, "Label", label.upper()))
        for x, y, c in sub_chunks(sub, t + 0.05, t + d - 0.05): events.append((x, y, "Sub", c))
        t += d
    # témoignages : intro (voix de Tao) puis 3 clients
    card = WORK / "temo.jpg"; testimonials_card(card)
    p = WORK / "t_intro.mp4"; d = 7.3; card_video(card, MEDIA / "9020c555.wav", p, d); parts.append(p)
    for x, y, c in sub_chunks("Voici quelques témoignages de personnes qui ont acheté notre Catalogue Premium", t + 0.8, t + 7.2):
        events.append((x, y, "Sub", c))
    t += d
    for k, (f, a, b, name, pays, sub) in enumerate(TEMO):
        p = WORK / f"t{k}.mp4"; d = cut(MEDIA / "temoignages" / f, a, b, p, k, blur_bg=True); parts.append(p)
        events.append((t, t + d, "Name", f"{name} · {pays}"))
        for x, y, c in sub_chunks(sub, t + 0.05, t + d - 0.05): events.append((x, y, "Sub", c))
        t += d
    # prix (voix de Tao, deux extraits) + carte de fin
    pa = WORK / "prix.wav"
    ff("-i", MEDIA / "10d75772.wav", "-filter_complex",
       "[0:a]atrim=0.86:2.72,asetpts=N/SR/TB,afade=t=out:st=1.8:d=0.06[x];[0:a]atrim=3.50:6.20,asetpts=N/SR/TB,afade=t=in:d=0.05[y];"
       "[x][y]concat=n=2:v=0:a=1[a]", "-map", "[a]", pa)
    endc = WORK / "fin.jpg"; end_card(endc)
    p = WORK / "fin.mp4"; d = 8.0; card_video(endc, pa, p, d); parts.append(p)
    # pas de sous-titre sur la carte de fin : le prix y est écrit
    t += d
    total = t
    lst = WORK / "list.txt"; lst.write_text("".join(f"file '{p}'\n" for p in parts))
    mid = WORK / "mid.mp4"; ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", mid)
    ass = WORK / "subs.ass"; build_ass(events, ass)
    out = OUT / "catalogue-premium-9x16.mp4"
    fc = (f"[0:v]subtitles={ass}:fontsdir={FONTS}[s];"
          "[1:v]format=rgba,scale=390:-1,colorchannelmixer=aa=0.45[w1];[2:v]format=rgba,scale=390:-1,colorchannelmixer=aa=0.45[w2];"
          "[s][w1]overlay=x='(W-w)*(0.5+0.5*sin(0.53*t))':y='(H-h)*(0.5+0.5*sin(0.37*t+1.1))'[b];"
          "[b][w2]overlay=x='(W-w)*(0.5+0.5*sin(0.41*t+2.6))':y='(H-h)*(0.5+0.5*sin(0.29*t+4.0))'[v];"
          f"[3:a]atrim=20:{20+total:.2f},asetpts=N/SR/TB,volume=0.09,afade=t=in:d=1.5,afade=t=out:st={total-2.5:.2f}:d=2.5[m];"
          "[0:a][m]amix=inputs=2:duration=first:normalize=0[a]")
    ff("-i", mid, "-loop", "1", "-i", WM, "-loop", "1", "-i", WM, "-stream_loop", "-1", "-i", MUSIC, "-filter_complex", fc,
       "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
       "-pix_fmt", "yuv420p", "-r", FPS, "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
       "-metadata", "comment=© WooPlans - wooplans.com", out)
    (OUT / "montage.json").write_text(json.dumps({"duree_s": round(total, 1), "sous_titres": [e[3] for e in events if e[2] == "Sub"]}, ensure_ascii=False, indent=1))
    print("OK", out, round(total, 1), "s")

if __name__ == "__main__":
    main()
