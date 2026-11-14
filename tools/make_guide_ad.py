"""Pub vidéo 9:16 du « Guide WooPlans des maisons » : accroche, rendus des modèles les plus achetés / vus,
défilement réel du guide sur le téléphone (vidéo de Tao), écran final avec le logo officiel et le prix.

  python tools/make_guide_ad.py --vo voix.mp3 --phone guide_telephone.mp4 --img dossier_rendus --out pub.mp4

Voix off : ElevenLabs « John Mala » (rendus 3D). Musique : assets/music (Mixkit, licence dans LISEZMOI_licence.txt).
Filigranes : 2 logos semi-transparents qui se promènent du début à la fin (décision du 16 oct.).
Les chiffres affichés viennent des fiches publiques du site ; les textes passent par check_copy.
"""
import argparse
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from wooplans.guardrails import check_copy  # noqa: E402

W, H, FPS = 1080, 1920, 30
TEAL = (15, 91, 89)
ORANGE = (240, 138, 46)
GOLD = (231, 195, 108)
WHITE = (255, 255, 255)
DARK = (30, 41, 51)
MUSIC = ROOT / "assets" / "music" / "Let-s-Play-Africa_Michael-Ramir-C_mixkit-x.mp3"
WM = ROOT / "assets" / "brand" / "wm_logo.png"
LOGO_STACKED = ROOT / "assets" / "brand" / "logo_white.png"

# Phrases de la voix off (bornes mesurées par silencedetect sur la voix « John Mala »).
SCENES = {
    "hook": (0.0, 3.52),
    "villa": (3.52, 8.16),
    "duplex": (8.16, 12.41),
    "guide": (12.41, 18.88),
    "montage": (18.88, 22.67),
    "end": (22.67, 28.0),
}
DUR = 28.0
HOOK_IMGS = ["V4-005", "D5-012", "V4-036", "V3-017", "D4-034", "V3-037"]
MONTAGE_IMGS = ["V4-032", "V3-014", "D4-040", "V3-018", "D4-043", "V4-005"]
TEXTS = {
    "hook1": "Avec votre budget…",
    "hook2": "quelle maison pouvez-vous",
    "hook3": "vraiment construire ?",
    "villa_t": "Villa 3 chambres · 120 m²",
    "villa_b": "Budget estimé : 17,3 à 21,1 millions FCFA",
    "duplex_t": "Duplex 5 chambres · 234 m²",
    "duplex_b": "Terrain conseillé : 350 m²",
    "guide1": "100 villas et duplex",
    "guide2": "classés par budget",
    "montage1": "Trouvez la maison",
    "montage2": "à votre portée",
    "end1": "Le Guide des maisons",
    "end2": "100 villas et duplex avec leur budget",
    "end_cta": "Guide PDF · 1 900 FCFA",
    "end_url": "wooplans.com",
}
CAPTIONS = [  # sous-titres (son coupé sur Facebook)
    (3.6, 5.6, "Cette villa de 3 chambres"),
    (5.6, 8.1, "environ 17 à 21 millions FCFA"),
    (8.2, 10.2, "Ce duplex de 5 chambres"),
    (10.2, 12.4, "tient sur 350 m² de terrain"),
]


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease_back(x):
    x = min(max(x, 0.0), 1.0)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


class Fonts:
    def __init__(self, font_dir: Path):
        self.dir = font_dir
        self.cache = {}

    def get(self, weight, size):
        key = (weight, size)
        if key not in self.cache:
            self.cache[key] = ImageFont.truetype(str(self.dir / f"Montserrat-{weight}.ttf"), size)
        return self.cache[key]


def cover(im, w, h):
    r = max(w / im.width, h / im.height)
    im = im.resize((math.ceil(im.width * r), math.ceil(im.height * r)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def rounded_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255)
    return m


def horizontal_logo(height):
    """Logo officiel (version empilée HD du dépôt) remis à l'horizontale comme sur le site : icône + WOOPLANS."""
    a = Image.open(LOGO_STACKED).convert("RGBA")
    alpha = a.split()[3]
    rows = [y for y in range(a.height) if alpha.crop((0, y, a.width, y + 1)).getextrema()[1] > 20]
    gap_rows = [y for y in range(rows[0], rows[-1]) if alpha.crop((0, y, a.width, y + 1)).getextrema()[1] <= 20]
    split = gap_rows[len(gap_rows) // 2]
    icon = a.crop((0, 0, a.width, split))
    icon = icon.crop(icon.getbbox())
    text = a.crop((0, split, a.width, a.height))
    text = text.crop(text.getbbox())
    ih = icon.height
    th = int(ih * 0.30)
    text = text.resize((int(text.width * th / text.height), th), Image.LANCZOS)
    gap = int(ih * 0.2)
    out = Image.new("RGBA", (icon.width + gap + text.width, ih), (0, 0, 0, 0))
    out.alpha_composite(icon, (0, 0))
    out.alpha_composite(text, (icon.width + gap, int(ih * 0.58)))
    return out.resize((int(out.width * height / out.height), height), Image.LANCZOS)


def text_center(img, y, txt, font, fill, scale=1.0, alpha=1.0, shadow=True):
    """Texte centré, avec mise à l'échelle (effet « pop ») et ombre portée."""
    if alpha <= 0 or scale <= 0.01:
        return
    d0 = ImageDraw.Draw(img)
    bb = d0.textbbox((0, 0), txt, font=font)
    tw, th = bb[2] - bb[0] + 20, bb[3] - bb[1] + 30
    layer = Image.new("RGBA", (tw + 20, th + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if shadow:
        d.text((14 - bb[0], 14 - bb[1]), txt, font=font, fill=(0, 0, 0, int(140 * alpha)))
        layer = layer.filter(ImageFilter.GaussianBlur(4))
        d = ImageDraw.Draw(layer)
    d.text((10 - bb[0], 10 - bb[1]), txt, font=font, fill=fill + (int(255 * alpha),))
    if abs(scale - 1) > 0.01:
        layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.LANCZOS)
    img.alpha_composite(layer, (int(W / 2 - layer.width / 2), int(y - layer.height / 2)))


def pill(img, cx, cy, txt, font, bg, fg, pad=(44, 22), scale=1.0):
    if scale <= 0.02:
        return
    d0 = ImageDraw.Draw(img)
    bb = d0.textbbox((0, 0), txt, font=font)
    w, h = bb[2] - bb[0] + pad[0] * 2, bb[3] - bb[1] + pad[1] * 2
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=bg + (255,))
    d.text((pad[0] - bb[0], pad[1] - bb[1]), txt, font=font, fill=fg)
    if abs(scale - 1) > 0.01:
        layer = layer.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    img.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


class Renderer:
    def __init__(self, img_dir: Path, phone_video: Path, font_dir: Path):
        self.f = Fonts(font_dir)
        self.src = {p.stem: Image.open(p).convert("RGB") for p in img_dir.glob("*.jpg")}
        self.bg = {k: Image.alpha_composite(cover(v, W, H).filter(ImageFilter.GaussianBlur(28)).convert("RGBA"),
                                            Image.new("RGBA", (W, H), TEAL + (175,))) for k, v in self.src.items()}
        self.card_w, self.card_h = 1000, 563
        self.card_mask = rounded_mask(self.card_w, self.card_h, 34)
        self.logo = horizontal_logo(64)
        self.logo_end = horizontal_logo(150)
        wm = Image.open(WM).convert("RGBA")
        a = wm.split()[3].point(lambda v: int(v * 0.33))
        wm.putalpha(a)
        self.wm = wm
        self.phone_w, self.phone_h = 540, 1150
        self.phone = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-ss", "1.5", "-i", str(phone_video), "-vf",
             f"setpts=PTS/1.55,fps={FPS},crop=iw:iw*2.13:0:ih*0.06,scale={self.phone_w - 28}:{self.phone_h - 28}",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.phone_frame = None

    def card(self, img, key, cy, t_local, zoom_from=1.0, zoom_to=1.08, x_off=0, scale=1.0):
        im = self.src[key]
        z = zoom_from + (zoom_to - zoom_from) * min(max(t_local, 0), 1)
        base = cover(im, int(self.card_w * z), int(self.card_h * z))
        x = (base.width - self.card_w) // 2
        y = (base.height - self.card_h) // 2
        c = base.crop((x, y, x + self.card_w, y + self.card_h)).convert("RGBA")
        c.putalpha(self.card_mask)
        if abs(scale - 1) > 0.01:
            c = c.resize((int(c.width * scale), int(c.height * scale)), Image.LANCZOS)
        shadow = Image.new("RGBA", (c.width + 60, c.height + 60), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle((30, 40, c.width + 30, c.height + 40), radius=34, fill=(0, 0, 0, 110))
        shadow = shadow.filter(ImageFilter.GaussianBlur(18))
        x0 = int(W / 2 - c.width / 2 + x_off)
        y0 = int(cy - c.height / 2)
        img.alpha_composite(shadow, (x0 - 30, y0 - 30))
        img.alpha_composite(c, (x0, y0))

    def tag(self, img, y, top, bottom, t_local):
        p = ease_out(t_local / 0.45)
        if p <= 0:
            return
        f1, f2 = self.f.get(700, 40), self.f.get(800, 40)
        w = 900
        h = 150
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.rounded_rectangle((0, 0, w - 1, h - 1), radius=28, fill=WHITE + (245,))
        d.text((36, 26), top, font=f1, fill=DARK)
        d.text((36, 82), bottom, font=f2, fill=ORANGE)
        x = int((W - w) / 2 - (1 - p) * 400)
        layer.putalpha(layer.split()[3].point(lambda v: int(v * p)))
        img.alpha_composite(layer, (x, y))

    def watermarks(self, img, t):
        for k, (ax, ay, fx, fy, ph) in enumerate(((380, 760, 0.11, 0.07, 0.0), (360, 700, 0.08, 0.13, 2.1))):
            x = W / 2 + ax * math.sin(2 * math.pi * fx * t + ph) - self.wm.width / 2
            y = H / 2 + ay * math.sin(2 * math.pi * fy * t + ph + k) - self.wm.height / 2
            img.alpha_composite(self.wm, (int(x), int(y)))

    def next_phone(self):
        raw = self.phone.stdout.read((self.phone_w - 28) * (self.phone_h - 28) * 3)
        if raw and len(raw) == (self.phone_w - 28) * (self.phone_h - 28) * 3:
            self.phone_frame = Image.frombytes("RGB", (self.phone_w - 28, self.phone_h - 28), raw)
        return self.phone_frame

    def frame(self, t):
        f = self.f
        name = next(k for k, (a, b) in SCENES.items() if a <= t < b) if t < DUR else "end"
        a, b = SCENES[name]
        lt = t - a
        if name == "hook":
            i = min(int(t / 0.55), len(HOOK_IMGS) - 1)
            key = HOOK_IMGS[i]
            img = self.bg[key].copy()
            cut = t - i * 0.55
            self.card(img, key, 1050, cut / 0.55, 1.15, 1.0, scale=1.0 + 0.04 * (1 - ease_out(cut / 0.2)))
            if cut < 0.06:  # flash de coupe
                img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, 90)))
            text_center(img, 330, TEXTS["hook1"], f.get(800, 84), WHITE, scale=ease_back(lt / 0.35))
            text_center(img, 470, TEXTS["hook2"], f.get(800, 62), GOLD, scale=ease_back((lt - 1.1) / 0.35))
            text_center(img, 555, TEXTS["hook3"], f.get(800, 62), GOLD, scale=ease_back((lt - 1.5) / 0.35))
        elif name in ("villa", "duplex"):
            key = "V3-017" if name == "villa" else "D5-012"
            img = self.bg[key].copy()
            enter = ease_out(lt / 0.4)
            self.card(img, key, 880, lt / (b - a), 1.0, 1.1, x_off=(1 - enter) * W)
            label = "Villa V3-017" if name == "villa" else "Duplex D5-012"
            text_center(img, 420, label, f.get(800, 70), WHITE, scale=ease_back(lt / 0.35))
            self.tag(img, 1210, TEXTS[f"{name}_t"], TEXTS[f"{name}_b"], lt - 0.5)
        elif name == "guide":
            img = Image.new("RGBA", (W, H), TEAL + (255,))
            g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(g).ellipse((90, 520, 990, 1600), fill=GOLD + (40,))
            img.alpha_composite(g.filter(ImageFilter.GaussianBlur(90)))
            rise = ease_out(lt / 0.6)
            px = (W - self.phone_w) // 2
            py = int(560 + (1 - rise) * 900)
            ph = Image.new("RGBA", (self.phone_w, self.phone_h), (0, 0, 0, 0))
            ImageDraw.Draw(ph).rounded_rectangle((0, 0, self.phone_w - 1, self.phone_h - 1), radius=60, fill=(12, 12, 14, 255))
            screen = self.next_phone()
            if screen is not None:
                s = screen.convert("RGBA")
                s.putalpha(rounded_mask(s.width, s.height, 46))
                ph.alpha_composite(s, (14, 14))
            img.alpha_composite(ph, (px, py))
            text_center(img, 300, TEXTS["guide1"], f.get(800, 78), WHITE, scale=ease_back((lt - 0.2) / 0.35))
            text_center(img, 400, TEXTS["guide2"], f.get(800, 66), GOLD, scale=ease_back((lt - 0.8) / 0.35))
        elif name == "montage":
            i = min(int(lt / 0.63), len(MONTAGE_IMGS) - 1)
            key = MONTAGE_IMGS[i]
            img = self.bg[key].copy()
            cut = lt - i * 0.63
            self.card(img, key, 1050, cut / 0.63, 1.0, 1.12, x_off=(1 - ease_out(cut / 0.18)) * 260)
            text_center(img, 360, TEXTS["montage1"], f.get(800, 80), WHITE, scale=ease_back(lt / 0.35))
            text_center(img, 470, TEXTS["montage2"], f.get(800, 80), GOLD, scale=ease_back((lt - 0.5) / 0.35))
        else:
            img = Image.new("RGBA", (W, H), TEAL + (255,))
            g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(g).ellipse((40, 300, 1040, 1300), fill=GOLD + (45,))
            img.alpha_composite(g.filter(ImageFilter.GaussianBlur(120)))
            s = ease_back(lt / 0.5)
            if s > 0.02:
                lg = self.logo_end.resize((max(1, int(self.logo_end.width * s)), max(1, int(self.logo_end.height * s))), Image.LANCZOS)
                img.alpha_composite(lg, (int(W / 2 - lg.width / 2), int(560 - lg.height / 2)))
            text_center(img, 820, TEXTS["end1"], f.get(800, 76), WHITE, scale=ease_back((lt - 0.4) / 0.35))
            text_center(img, 915, TEXTS["end2"], f.get(700, 42), GOLD, scale=ease_back((lt - 0.7) / 0.35))
            pulse = 1 + 0.045 * math.sin(2 * math.pi * 1.4 * max(lt - 1.2, 0)) if lt > 1.2 else ease_back((lt - 0.9) / 0.35)
            if pulse > 0.02:
                pill(img, W / 2, 1120, TEXTS["end_cta"], f.get(800, 58), ORANGE, WHITE, scale=pulse)
            text_center(img, 1290, TEXTS["end_url"], f.get(700, 50), WHITE, alpha=ease_out((lt - 1.3) / 0.4))
        # Logo en haut (sauf écran final) et sous-titres.
        if name != "end":
            img.alpha_composite(self.logo, (int(W / 2 - self.logo.width / 2), 70))
        if name not in ("end", "guide") and t > 0.8:
            pill(img, W / 2, 1720, TEXTS["end_cta"], f.get(800, 46), ORANGE, WHITE, scale=ease_back((t - 0.8) / 0.35))
        for s0, s1, txt in CAPTIONS:
            if s0 <= t < s1:
                pill(img, W / 2, 1490, txt, f.get(800, 50), DARK, WHITE, scale=ease_back((t - s0) / 0.25))
        self.watermarks(img, t)
        return img.convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vo", required=True)
    ap.add_argument("--phone", required=True)
    ap.add_argument("--img", required=True)
    ap.add_argument("--fonts", default=str(ROOT.parent / "wooplans" / "scripts" / "guide" / "cache" / "fonts"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--preview", type=float, nargs="*", help="Instants à exporter en PNG au lieu de la vidéo")
    args = ap.parse_args()

    problems = [p for t in [*TEXTS.values(), *(c[2] for c in CAPTIONS)] for p in check_copy(t, (1900,))]
    if problems:
        raise SystemExit(f"Textes refusés par check_copy : {problems}")

    r = Renderer(Path(args.img), Path(args.phone), Path(args.fonts))
    if args.preview:
        for t in args.preview:
            if SCENES["guide"][0] <= t < SCENES["guide"][1]:
                for _ in range(int((t - SCENES["guide"][0]) * FPS) + 1):
                    r.next_phone()
            r.frame(t).save(f"{args.out}_{t:05.2f}.png")
        return

    silent = args.out + ".video.mp4"
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for i in range(n):
        enc.stdin.write(r.frame(i / FPS).tobytes())
        if i % 120 == 0:
            print(f"{i}/{n}", flush=True)
    enc.stdin.close()
    enc.wait()
    # Voix devant, musique dessous (baissée sous la voix, remontée sur l'écran final), fondu de sortie.
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", args.vo, "-stream_loop", "-1", "-i", str(MUSIC), "-filter_complex",
         f"[1:a]volume=1.6,apad[vo];[2:a]volume='if(lt(t,{SCENES['end'][0]}),0.12,0.35)':eval=frame,afade=t=out:st={DUR - 1.6}:d=1.6[mu];"
         f"[vo][mu]amix=inputs=2:duration=first:normalize=0,atrim=0:{DUR}[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", args.out],
        check=True)
    Path(silent).unlink()
    print("OK", args.out)


if __name__ == "__main__":
    main()
