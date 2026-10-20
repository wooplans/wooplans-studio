"""Reel « rendus 3D » d'un plan du catalogue : musique de fond + sous-titres animés, sans voix off.

  python tools/make_reel.py D4-026 sortie.mp4 [--music assets/music/<fichier>.mp3] [--keep dossier_de_travail]

Rendus pris sur la fiche publique du plan ; textes et chiffres : data/plans.json (check_copy appliqué) ;
coupes calées sur les mesures de la musique (assets/music/tracks.json, produit par tools/analyze_music.py).
"""
import argparse
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from tools.image_batch import download, fetch_page_images
from wooplans.image_posts import load_plans
from wooplans.reel3d import (FPS, H, OVERLAP, W, assign_images, bar_length, build_ass, check_scenes, fcfa, n_bars, pan, scenes)
from wooplans.settings import OFFER_PRICE_FCFA, ROOT

BRAND = ROOT / "assets" / "brand"
FONT = ROOT / "visite_plan" / "fonts" / "Poppins-Bold.ttf"
TRANSITIONS = ["fade", "slideleft", "fade", "zoomin", "fade", "slideleft", "fade", "zoomin", "fade", "fade"]
DEFAULT_MUSIC = ROOT / "assets" / "music" / "Let-s-Play-Africa_Michael-Ramir-C_mixkit-x.mp3"
MAX_IMAGES = 8
FG_H = 1080                                    # hauteur de l'image à l'écran
IMG_Y = 30                                    # haut de l'image (le texte est décalé vers le bas, voir CAP_DY)


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        raise RuntimeError(f"ffmpeg a échoué :\n{' '.join(map(str, cmd))[:400]}\n{r.stderr[-1500:]}")
    return r


def clip_cmd(img: Path, size, mode: str, idx: int, dur: float, out: Path, blur: bool = False):
    a, b = pan(idx)
    w, h = size
    ff = ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", str(img)]
    # image à hauteur fixe (FG_H) : assez grande pour apprécier le plan ; si elle déborde en largeur, travelling lent
    fh = f"trunc({FG_H}*(1+0.04*t/{dur:.3f})/2)*2"
    a, b = pan(idx)
    fc = (f"[0:v]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=30,eq=brightness=-0.15[bg];"
          f"[b]scale=w=-2:h='{fh}':eval=frame[fg];"
          f"[bg][fg]overlay=x='if(gt(w,{W}),({W}-w)*({a}+({b}-{a})*t/{dur:.3f}),({W}-w)/2)':y={IMG_Y},format=yuv420p")
    if blur:
        fc += ",gblur=sigma=12,eq=brightness=-0.12"
    return ff + ["-filter_complex", fc, "-r", str(FPS), "-c:v", "libx264", "-crf", "16", "-preset", "veryfast", str(out)]


def gradient_png(path: Path, h: int = 900):
    im = Image.new("RGBA", (W, h))
    px = im.load()
    for y in range(h):
        a = int(165 * (y / h) ** 1.6)
        for x in range(W):
            px[x, y] = (0, 0, 0, a)
    im.save(path)


def end_card_png(path: Path):
    f = lambda s: ImageFont.truetype(str(FONT), s)
    im = Image.new("RGBA", (W, H), (15, 91, 89, 214))
    d = ImageDraw.Draw(im)
    logo = Image.open(BRAND / "logo_white.png").convert("RGBA")
    lw = 400
    logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
    im.alpha_composite(logo, ((W - lw) // 2, 430))

    def centered(text, y, size, fill):
        fnt = f(size)
        d.text(((W - d.textlength(text, font=fnt)) / 2, y), text, font=fnt, fill=fill)

    centered("Plan complet", 880, 78, "white")
    centered("+ devis détaillé", 975, 78, "white")
    d.rounded_rectangle((150, 1130, W - 150, 1290), radius=80, fill=(240, 138, 46, 255))
    centered("wooplans.com", 1165, 88, "white")
    centered("Catalogue Premium", 1345, 50, "white")
    centered(f"prix actuel : {fcfa(OFFER_PRICE_FCFA)} FCFA", 1410, 50, "white")
    centered("Lien en description", 1505, 52, (240, 138, 46, 255))
    im.save(path)


def end_card_texts():
    return ["Plan complet", "+ devis détaillé", "wooplans.com", "Catalogue Premium",
            f"prix actuel : {fcfa(OFFER_PRICE_FCFA)} FCFA", "Lien en description"]


def build(code: str, out: Path, music: Path = DEFAULT_MUSIC, keep: Path = None) -> Path:
    from wooplans.guardrails import check_copy
    plan = next((p for p in load_plans() if p["code"] == code), None)
    if not plan:
        raise SystemExit(f"plan inconnu : {code}")
    sc = scenes(plan)
    problems = check_scenes(sc, plan) + [x for t in end_card_texts() for x in check_copy(t, [plan["estimate_total"]])]
    if problems:
        raise SystemExit(f"texte refusé : {problems}")
    tracks = json.loads((ROOT / "assets" / "music" / "tracks.json").read_text(encoding="utf-8"))
    tr = tracks[music.name]
    bar_s = bar_length(60.0 / tr["beat_interval"])
    nb = n_bars(sc)
    total = nb * bar_s + OVERLAP

    tmp = Path(keep) if keep else Path(tempfile.mkdtemp(prefix="reel-"))
    tmp.mkdir(parents=True, exist_ok=True)
    urls = fetch_page_images(plan)[:MAX_IMAGES]
    if not urls:
        raise SystemExit(f"{code} : aucun rendu sur la fiche")
    imgs, sizes = [], []
    for i, u in enumerate(urls):
        im = Image.open(io.BytesIO(download(u))).convert("RGB")
        p = tmp / f"img{i}.jpg"
        im.save(p, quality=93)
        imgs.append(p)
        sizes.append(im.size)
    plan_imgs = assign_images(nb, sizes)

    clips = []
    for k in range(nb):
        i, mode = plan_imgs[k]
        c = tmp / f"clip{k}.mp4"
        run(clip_cmd(imgs[i], sizes[i], mode, k, bar_s + OVERLAP, c, blur=(k == nb - 1)))
        clips.append(c)

    # fondus enchaînés calés sur les mesures
    fc, last = [], "0:v"
    for k in range(1, nb):
        lab = f"x{k}"
        fc.append(f"[{last}][{k}:v]xfade=transition={TRANSITIONS[(k - 1) % len(TRANSITIONS)]}:duration={OVERLAP}:offset={k * bar_s:.3f}[{lab}]")
        last = lab
    base = tmp / "base.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error"] + sum([["-i", str(c)] for c in clips], []) +
        ["-filter_complex", ";".join(fc), "-map", f"[{last}]", "-r", str(FPS), "-c:v", "libx264", "-crf", "16", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", str(base)])

    grad, card = tmp / "grad.png", tmp / "card.png"
    gradient_png(grad)
    end_card_png(card)
    (tmp / "reel.ass").write_text(build_ass(sc, plan, bar_s, total), encoding="utf-8")
    shutil.copytree(ROOT / "visite_plan" / "fonts", tmp / "fonts", dirs_exist_ok=True)
    t_end = (nb - 1) * bar_s + 0.05
    fcx = (f"[0:v][1:v]overlay=0:{H - 900}:enable='lt(t,{t_end:.2f})'[v1];"
           f"[v1][2:v]overlay=0:1530:enable='lt(t,{t_end:.2f})'[v2];"
           f"[v2][3:v]overlay=30:50:enable='lt(t,{t_end:.2f})'[v3];"
           f"[4:v]format=rgba,fade=t=in:st={t_end:.2f}:d=0.35:alpha=1[ec];"
           f"[v3][ec]overlay=0:0[v4];"
           f"[v4]subtitles=reel.ass:fontsdir=fonts[v]")
    audio = f"afade=t=in:d=0.25,afade=t=out:st={total - 1.4:.2f}:d=1.4,loudnorm=I=-14:TP=-1.5:LRA=7"
    out = Path(out).resolve()
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(base), "-i", str(grad), "-i", str(BRAND / "band_bottom.png"),
         "-i", str(BRAND / "badge_url.png"), "-loop", "1", "-t", f"{total:.2f}", "-i", str(card),
         "-ss", f"{tr['best_start']:.3f}", "-t", f"{total:.2f}", "-i", str(music),
         "-filter_complex", fcx, "-map", "[v]", "-map", "5:a", "-af", audio, "-t", f"{total:.2f}",
         "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", str(out)], cwd=tmp)
    if not keep:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"OK {out} · {total:.1f} s · {nb} mesures de {bar_s:.2f} s")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("code")
    ap.add_argument("out")
    ap.add_argument("--music", default=str(DEFAULT_MUSIC))
    ap.add_argument("--keep", default=None)
    a = ap.parse_args(argv)
    build(a.code, Path(a.out), Path(a.music).resolve(), a.keep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
