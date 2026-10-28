"""Short « rendus 3D » plein écran (9:16, ~20 s) : travelling lent sur chaque rendu d'origine, sans voix ni plan coté.

  python tools/make_short.py shorts/jobs/<id> [sortie.mp4]

Inspiré des shorts « Small House Design » : la plus belle façade dès la 1re image, mouvement continu, coupes sur
le temps de la musique, texte réduit au minimum. Job : shorts/jobs/<id>/short.json
  {"code": "D4-004", "images": ["youtube_plan/jobs/D4-004/assets/R0.png", ...],
   "music": "assets/music/Africa_Arulo_mixkit-218.mp3", "beats": 8,
   "thumbnail": {"title": "...", "chip": "..."}}
Rendus d'origine (1920x1080 ou plus, sans filigrane du site). Textes : data/plans.json, passés par check_copy.
Marque : 2 logos semi-transparents qui se promènent du début à la fin, fin « wooplans.com ».
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wooplans.guardrails import check_copy  # noqa: E402

W, H, FPS = 1080, 1920, 30
FONT = ROOT / "visite_plan" / "fonts" / "Poppins-Bold.ttf"
BRAND = ROOT / "assets" / "brand"
GREEN, ORANGE, GOLD = (15, 91, 89), (240, 138, 46), (231, 195, 108)
XFADE = 0.4                        # fondu entre deux rendus (s)
END = 2.6                          # carte de fin (s)


def ff(*args):
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *map(str, args)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-1500:])


def plan_info(code: str) -> dict:
    plans = json.loads((ROOT / "data" / "plans.json").read_text(encoding="utf-8"))
    return next(p for p in plans if p["code"] == code)


def texts(p: dict):
    kind = "Duplex" if p["category"] == "duplex" else "Villa"
    title = f"{kind} {p['bedrooms']} chambres"
    facts = f"{p['surface']} m²" + (f" · terrain {p['land_area']} m²" if p.get("land_area") else "")
    return title, facts


def overlay_png(path: Path, lines):
    """Calque transparent 1080x1920 : bandeau d'infos en bas (zone sûre, au-dessus des boutons des plateformes)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(H - 760, H):
        d.line([(0, y), (W, y)], fill=(8, 40, 40, int(170 * (y - (H - 760)) / 760)))
    big, small = ImageFont.truetype(str(FONT), 84), ImageFont.truetype(str(FONT), 54)
    d.text((W // 2, 1380), lines[0].upper(), font=big, fill="white", anchor="mm", stroke_width=6, stroke_fill=GREEN)
    d.text((W // 2, 1480), lines[1], font=small, fill=GOLD, anchor="mm", stroke_width=4, stroke_fill=GREEN)
    img.save(path)


def end_png(path: Path, bg: Path, line: str):
    """Carte de fin : dernier rendu flouté et assombri, logo + wooplans.com."""
    src = Image.open(bg).convert("RGB")
    k = H / src.height
    src = src.resize((round(src.width * k), H), Image.LANCZOS)
    x0 = (src.width - W) // 2
    img = src.crop((x0, 0, x0 + W, H)).filter(ImageFilter.GaussianBlur(18))
    img = Image.alpha_composite(img.convert("RGBA"), Image.new("RGBA", (W, H), (8, 40, 40, 175)))
    d = ImageDraw.Draw(img)
    logo = Image.open(BRAND / "logo_white.png").convert("RGBA")
    logo = logo.resize((520, round(logo.height * 520 / logo.width)), Image.LANCZOS)
    img.alpha_composite(logo, ((W - logo.width) // 2, 560))
    f1, f2 = ImageFont.truetype(str(FONT), 54), ImageFont.truetype(str(FONT), 96)
    y = 560 + logo.height + 90
    d.text((W // 2, y), line, font=f1, fill="white", anchor="mm")
    tw = d.textlength("wooplans.com", font=f2)
    d.rounded_rectangle([(W - tw) / 2 - 50, y + 90, (W + tw) / 2 + 50, y + 250], radius=80, fill=ORANGE)
    d.text((W // 2, y + 170), "wooplans.com", font=f2, fill="white", anchor="mm")
    img.convert("RGB").save(path)


def clip(img: Path, k: int, dur: float, out: Path):
    """Travelling horizontal plein écran : rendu mis à la hauteur 1920 puis fenêtre 1080 qui glisse (sens alterné).
    Calcul sur une image 2x pour un mouvement fluide."""
    a, b = (0.2, 0.8) if k % 2 == 0 else (0.8, 0.2)
    ff("-loop", "1", "-t", f"{dur:.3f}", "-i", img, "-vf",
       f"scale=-2:{2 * H}:flags=lanczos,"
       f"crop={2 * W}:{2 * H}:x='(iw-ow)*({a}+({b}-{a})*t/{dur:.3f})':y=0,"
       f"scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-r", FPS, out)


def main() -> int:
    job = Path(sys.argv[1])
    cfg = json.loads((job / "short.json").read_text(encoding="utf-8"))
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "shorts" / "out" / f"{job.name}.mp4"
    p = plan_info(cfg["code"])
    title, facts = texts(p)
    end_line = cfg.get("end_line", "Plans et devis de ce modèle sur")
    problems = check_copy(" ".join([title, facts, end_line]))
    if problems:
        print("Texte refusé :", problems)
        return 1
    tracks = json.loads((ROOT / "assets" / "music" / "tracks.json").read_text(encoding="utf-8"))
    music = ROOT / cfg["music"]
    tr = tracks[music.name]
    seg = tr["beat_interval"] * cfg.get("beats", 8)          # chaque rendu dure N temps
    images = [ROOT / i for i in cfg["images"]]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        clips = []
        for k, img in enumerate(images):
            c = tmp / f"c{k}.mp4"
            clip(img, k, seg + XFADE, c)
            clips.append(c)
        overlay_png(tmp / "info.png", (title, facts))
        end_png(tmp / "end.png", images[-1], end_line)
        ff("-loop", "1", "-t", f"{END + XFADE:.3f}", "-i", tmp / "end.png", "-vf", f"fps={FPS},format=yuv420p",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-r", FPS, tmp / "end.mp4")
        clips.append(tmp / "end.mp4")
        total = (len(clips) - 1) * seg + END
        # enchaînement : fondus entre rendus, puis carte de fin
        inputs, fc, last = [], "", "0:v"
        for c in clips:
            inputs += ["-i", c]
        for k in range(1, len(clips)):
            fc += f"[{last}][{k}:v]xfade=transition=fade:duration={XFADE}:offset={k * seg:.3f}[x{k}];"
            last = f"x{k}"
        n = len(clips)
        inputs += ["-i", tmp / "info.png", "-i", BRAND / "wm_logo.png", "-i", BRAND / "wm_logo.png",
                   "-ss", f"{tr['best_start']:.3f}", "-i", music]
        fc += (f"[{n + 1}:v]format=rgba,scale=390:-1,colorchannelmixer=aa=0.62[w1];"
               f"[{n + 2}:v]format=rgba,scale=390:-1,colorchannelmixer=aa=0.62[w2];"
               f"[{last}][{n}:v]overlay=0:0:enable='between(t,0.25,{seg * 1.5:.2f})'[i];"
               "[i][w1]overlay=x='(W-w)*(0.5+0.5*sin(0.53*t))':y='(H-h)*(0.5+0.5*sin(0.37*t+1.1))'[m];"
               "[m][w2]overlay=x='(W-w)*(0.5+0.5*sin(0.41*t+2.6))':y='(H-h)*(0.5+0.5*sin(0.29*t+4.0))',"
               f"trim=duration={total:.3f},format=yuv420p[v];"
               f"[{n + 3}:a]atrim=duration={total:.3f},afade=t=in:d=0.3,afade=t=out:st={total - 1.6:.3f}:d=1.6,"
               "loudnorm=I=-14:TP=-1.5:LRA=11[a]")
        out.parent.mkdir(parents=True, exist_ok=True)
        ff(*inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium",
           "-crf", "18", "-pix_fmt", "yuv420p", "-r", FPS, "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-movflags", "+faststart", "-metadata", "comment=© WooPlans - wooplans.com", "-metadata",
           "copyright=© WooPlans", out)
    print(f"short : {out} ({total:.1f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
