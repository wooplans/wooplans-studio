"""2 vidéos pub 9:16 (1080×1920) qui enchaînent les 7 modèles du top 7, coupes calées sur le tempo de la musique.

  python tools/make_ad_videos.py creatives/top7 [dossier_sortie] [--price 39000]   # lit spec.json, écrit video_A_regulier.mp4, video_B_acceleration.mp4
  --price : variante dont SEUL le montant change (fichiers suffixés _<montant>)
  --no-price : variante sans prix, le bouton « TÉLÉCHARGER PLAN ET DEVIS » prend sa place (fichiers suffixés _sansprix)

A « régulier »  : 7 modèles × 4 temps (Africa Arulo, 124 bpm), puis carte finale.
B « accélération » : 8, 6, 4, 4, 2, 2, 2 temps (Pop Two, 100 bpm) : les 3 meilleurs restent plus longtemps, les autres défilent en rafale.
Chaque plan montre : nom du modèle, chambres / douches / m², « Plan + devis » 14 900 FCFA, bouton « TÉLÉCHARGER MAINTENANT ».
Textes passés dans check_copy ; rendus publics filigranés ; musique Mixkit (licence libre). Rien n'est envoyé à Meta sans l'accord de Tao.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageOps

from tools.make_ad_creatives import GOLD, ORANGE, SOFT, TEAL_D, WHITE, font, gradient
from wooplans.guardrails import check_copy
from wooplans.settings import ROOT

W, H, FPS = 1080, 1920, 30
IMG_Y = 370                    # haut de l'image ; tout le texte reste au-dessus de y≈1580 (zones de l'interface Reels)
MAX_SLOT = 690
MUSIC = ROOT / "assets" / "music"
BRAND = ROOT / "assets" / "brand"

def videos_for(n: int) -> list:
    """Deux montages : A « régulier » (4 temps par modèle) et B « accélération » (les 4 premiers restent plus longtemps)."""
    return [
        {"id": "A_regulier", "track": "Africa_Arulo_mixkit-218.mp3", "beats": [4] * n, "end_beats": 8},
        {"id": "B_acceleration", "track": "C_Pop-Two_Grigoriy-Nuzhny_mixkit-697.mp3", "beats": ([8, 6, 4, 4] + [2] * max(0, n - 4))[:n], "end_beats": 6},
    ]


VIDEOS = videos_for(7)  # top 7 d'origine ; main() recalcule selon le nombre de modèles du spec

CTA_NO_PRICE = "TÉLÉCHARGER PLAN ET DEVIS"
SUBLINE_NO_PRICE = "Plan coté + devis détaillé du modèle"


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"ffmpeg a échoué : {r.stderr[-1500:]}")


def fcfa(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def centered(d, xy, text, f, fill):
    d.text(xy, text, font=f, fill=fill, anchor="mm")


def texts(p: dict, price: int) -> list:
    if not price:
        return ["Quel modèle choisissez-vous ?", p["name"].upper(), f"{p['bedrooms']} chambres", f"{p['bathrooms']} douches", f"{p['surface']} m²",
                SUBLINE_NO_PRICE, CTA_NO_PRICE, "wooplans.com"]
    return ["Quel modèle choisissez-vous ?", p["name"].upper(), f"{p['bedrooms']} chambres", f"{p['bathrooms']} douches", f"{p['surface']} m²",
            "Plan + devis du modèle", f"{fcfa(price)} FCFA", "TÉLÉCHARGER MAINTENANT", "wooplans.com"]


def slot_height(im: Image.Image) -> int:
    return min(MAX_SLOT, round(W * im.height / im.width))


def layout_png(p: dict, price: int, idx: int, n: int, slot_h: int, out: Path) -> None:
    """Fond de marque + textes ; la case de l'image (y = IMG_Y) est laissée vide, ffmpeg y superpose le rendu animé."""
    im = gradient(H)
    d = ImageDraw.Draw(im)
    centered(d, (W // 2, 190), "Quel modèle choisissez-vous ?", font(36), SOFT)
    centered(d, (W // 2, 275), p["name"].upper(), font(78), WHITE)
    y0 = IMG_Y + slot_h
    stats = [(str(p["bedrooms"]), "chambres"), (str(p["bathrooms"]), "douches"), (str(p["surface"]), "m²")]
    col = W // 3
    for i, (num, lab) in enumerate(stats):
        cx = col * i + col // 2
        centered(d, (cx, y0 + 70), num, font(96), GOLD)
        centered(d, (cx, y0 + 144), lab, font(36), WHITE)
        if i:
            d.line([(col * i, y0 + 30), (col * i, y0 + 160)], fill=SOFT, width=2)
    if not price:
        # Sans prix : le bouton « TÉLÉCHARGER PLAN ET DEVIS » prend la place du prix
        centered(d, (W // 2, y0 + 232), SUBLINE_NO_PRICE, font(35), SOFT)
        by = y0 + 290
        d.rounded_rectangle([(W - 920) // 2, by, (W + 920) // 2, by + 130], radius=65, fill=ORANGE)
        centered(d, (W // 2, by + 62), CTA_NO_PRICE, font(50), TEAL_D)
        centered(d, (W // 2, by + 190), "wooplans.com", font(36), SOFT)
        by += 25  # repères de progression un peu plus bas pour rester au même endroit que la version avec prix
    else:
        centered(d, (W // 2, y0 + 225), "Plan + devis du modèle", font(34), SOFT)
        ptxt = fcfa(price)
        fp, fc = font(112), font(48)
        wp, wc = d.textlength(ptxt, font=fp), d.textlength(" FCFA", font=fc)
        x = (W - (wp + wc)) / 2
        d.text((x, y0 + 292), ptxt, font=fp, fill=WHITE, anchor="lm")
        d.text((x + wp, y0 + 310), " FCFA", font=fc, fill=WHITE, anchor="lm")
        by = y0 + 365
        d.rounded_rectangle([(W - 800) // 2, by, (W + 800) // 2, by + 104], radius=52, fill=ORANGE)
        centered(d, (W // 2, by + 50), "TÉLÉCHARGER MAINTENANT", font(44), TEAL_D)
        centered(d, (W // 2, by + 150), "wooplans.com", font(34), SOFT)
    # repères de progression : un point par modèle
    gap, r = 38, 9
    x0 = (W - gap * (n - 1)) // 2
    for i in range(n):
        d.ellipse([x0 + i * gap - r, by + 205 - r, x0 + i * gap + r, by + 205 + r], fill=GOLD if i == idx else (255, 255, 255, 70) and "#2F7F7C")
    im.save(out)


def end_card_png(price: int, out: Path) -> None:
    im = gradient(H)
    d = ImageDraw.Draw(im)
    logo = Image.open(BRAND / "logo_white.png").convert("RGBA")
    lw = 420
    logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
    im.paste(logo, ((W - lw) // 2, 330), logo)
    centered(d, (W // 2, 860), "Votre plan + devis", font(78), WHITE)
    centered(d, (W // 2, 960), "dès aujourd'hui", font(78), WHITE)
    if not price:
        d.rounded_rectangle([(W - 920) // 2, 1110, (W + 920) // 2, 1250], radius=70, fill=ORANGE)
        centered(d, (W // 2, 1180), CTA_NO_PRICE, font(52), TEAL_D)
        centered(d, (W // 2, 1340), "wooplans.com", font(46), SOFT)
    else:
        ptxt = fcfa(price)
        fp, fc = font(116), font(50)
        wp, wc = d.textlength(ptxt, font=fp), d.textlength(" FCFA", font=fc)
        x = (W - (wp + wc)) / 2
        d.text((x, 1110), ptxt, font=fp, fill=GOLD, anchor="lm")
        d.text((x + wp, 1128), " FCFA", font=fc, fill=GOLD, anchor="lm")
        d.rounded_rectangle([(W - 800) // 2, 1220, (W + 800) // 2, 1330], radius=55, fill=ORANGE)
        centered(d, (W // 2, 1275), "TÉLÉCHARGER MAINTENANT", font(46), TEAL_D)
        centered(d, (W // 2, 1400), "wooplans.com", font(44), SOFT)
    im.save(out)


def clip(img: Path, layout: Path, slot_h: int, frames: int, out: Path) -> None:
    dur = frames / FPS
    z = f"trunc({W}*(1+0.07*t/{dur:.4f})/2)*2"
    fc = (f"[0:v]scale=w='{z}':h=-2:eval=frame,crop={W}:{slot_h}:(iw-{W})/2:(ih-{slot_h})/2[z];"
          f"[1:v][z]overlay=0:{IMG_Y},format=yuv420p")
    run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", FPS, "-t", f"{dur:.4f}", "-i", img,
         "-loop", "1", "-framerate", FPS, "-t", f"{dur:.4f}", "-i", layout, "-filter_complex", fc,
         "-r", FPS, "-c:v", "libx264", "-crf", "17", "-preset", "veryfast", "-frames:v", frames, out])


def still(layout: Path, frames: int, out: Path) -> None:
    run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", FPS, "-t", f"{frames / FPS:.4f}", "-i", layout,
         "-vf", "format=yuv420p", "-r", FPS, "-c:v", "libx264", "-crf", "17", "-preset", "veryfast", "-frames:v", frames, out])


def render(spec: dict, root: Path, v: dict, tmp: Path, out_dir: Path, suffix: str = "") -> Path:
    price = spec["price_fcfa"]
    plans = spec["plans"]
    tracks = json.loads((MUSIC / "tracks.json").read_text(encoding="utf-8"))
    tr = tracks[v["track"]]
    bi = tr["beat_interval"]
    # coupes sur les temps, cumulées (aucune dérive) : durée en images = écart entre deux temps arrondis
    cum, cuts = 0, [0]
    for b in v["beats"] + [v["end_beats"]]:
        cum += b
        cuts.append(round(cum * bi * FPS))
    parts = []
    for i, p in enumerate(plans):
        problems = check_copy(" | ".join(texts(p, price)), allowed_amounts=[price])
        if problems:
            raise SystemExit(f"{p['code']} : {problems}")
        src = root / p["render"]
        if not src.is_file():
            src.parent.mkdir(parents=True, exist_ok=True)
            r = requests.get(p["url"], headers={"User-Agent": "Mozilla/5.0 (compatible; WooPlansStudio/1.0)"}, timeout=60)
            r.raise_for_status()
            src.write_bytes(r.content)
        im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        jpg = tmp / f"{v['id']}_{p['code']}.jpg"
        im.save(jpg, quality=95)
        sh = slot_height(im)
        lay = tmp / f"{v['id']}_{p['code']}_layout.png"
        layout_png(p, price, i, len(plans), sh, lay)
        part = tmp / f"{v['id']}_{i}.mp4"
        clip(jpg, lay, sh, cuts[i + 1] - cuts[i], part)
        parts.append(part)
    end_lay = tmp / f"{v['id']}_end.png"
    end_card_png(price, end_lay)
    end_texts = ["Votre plan + devis", "dès aujourd'hui", CTA_NO_PRICE, "wooplans.com"] if not price else ["Votre plan + devis", "dès aujourd'hui", f"{fcfa(price)} FCFA", "TÉLÉCHARGER MAINTENANT", "wooplans.com"]
    for t in end_texts:
        pb = check_copy(t, allowed_amounts=[price])
        if pb:
            raise SystemExit(f"carte finale : {pb}")
    end = tmp / f"{v['id']}_end.mp4"
    still(end_lay, cuts[-1] - cuts[-2], end)
    parts.append(end)

    lst = tmp / f"{v['id']}_list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
    silent = tmp / f"{v['id']}_silent.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])
    total = cuts[-1] / FPS
    out = out_dir / f"video_{v['id']}{suffix}.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-ss", f"{tr['best_start']:.3f}", "-t", f"{total:.3f}", "-i", MUSIC / v["track"],
         "-filter_complex", f"[1:a]afade=t=in:d=0.15,afade=t=out:st={total - 1.4:.3f}:d=1.4,volume=0.9[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out])
    # premier frame = vignette : la plateforme l'affiche tant que la vidéo ne tourne pas
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", out, "-frames:v", "1", "-q:v", "2", out_dir / f"video_{v['id']}{suffix}_cover.jpg"])
    print(f"OK {out.name} : {total:.1f} s, coupes tous les {v['beats']} temps ({tr['bpm']} bpm)")
    return out


def main(root: Path, out_dir: Path, price: int = None, no_price: bool = False) -> None:
    spec = json.loads((root / "spec.json").read_text(encoding="utf-8"))
    suffix = ""
    if no_price:
        spec["price_fcfa"], suffix = 0, "_sansprix"
    elif price and price != spec["price_fcfa"]:
        spec["price_fcfa"], suffix = price, f"_{price}"
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="adv-") as t:
        for v in videos_for(len(spec["plans"])):
            render(spec, root, v, Path(t), out_dir, suffix)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    price = None
    no_price = "--no-price" in args
    if no_price:
        args.remove("--no-price")
    if "--price" in args:
        i = args.index("--price")
        price = int(args[i + 1])
        del args[i:i + 2]
    r = Path(args[0])
    main(r, Path(args[1]) if len(args) > 1 else r / "video", price, no_price)
