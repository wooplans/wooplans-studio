"""Boîte à outils motion design des VSL : charte, voix, fond animé, illustrations vectorielles.

Tout est dessiné en formes ManimGX (aucune image externe) pour garder des vidéos légères et nettes.
"""

import json
import os
import random
from pathlib import Path

import numpy as np
import manimgx as m
from manimgx.audio import Speech, Word, timed

HERE = Path(__file__).resolve().parent

# --- Charte WooPlans ---------------------------------------------------------
GREEN = "#0F5B59"
GREEN_DARK = "#0A4341"
GREEN_LIGHT = "#2E8A86"
ORANGE = "#F08A2E"
GOLD = "#E7C36C"
CREAM = "#FFF7EC"
WHITE = "#FFFFFF"
RED = "#D9483B"
GREY = "#C9D3D2"
FONT = "Noto Sans"

FRAME_W = 8.0
FRAME_H = 8.0 * 1920 / 1080
TOP = FRAME_H / 2
ART_Y = 1.2             # centre de la zone d'illustration
CAP_Y = -3.7            # haut de la zone des titres

m.config.background_color = GREEN
m.config.pixel_width, m.config.pixel_height = 1080, 1920


def script(name):
    return json.loads((HERE / "scripts" / f"{name}.json").read_text(encoding="utf-8"))


def mark(text, *phrases):
    """Entoure de crochets, dans l'ordre, chaque expression de la voix off (ancre d'une animation).
    None = ancre vide à l'endroit courant."""
    out, pos = [], 0
    for p in phrases:
        if p is None:
            out.append(text[pos:pos])
            out.append("[]")
            continue
        i = text.find(p, pos)
        if i < 0:
            raise ValueError(f"« {p} » absent de : {text}")
        out += [text[pos:i], f"[{p}]"]
        pos = i + len(p)
    out.append(text[pos:])
    return "".join(out)


# --- Voix --------------------------------------------------------------------
def apercu(text: str) -> Speech:
    """Voix muette d'aperçu : silence, mots calés au débit moyen de LeTao (≈ 2,7 mots/s)."""
    words, t = [], 0.1
    for w in text.split():
        d = 0.055 * len(w) + 0.1
        words.append(Word(w, t, t + d))
        t += d + (0.3 if w[-1] == "," else 0.45 if w[-1] in ".:;?!" else 0.0)
    rate = 24000
    return Speech(np.zeros(int((t + 0.2) * rate), dtype=np.float32), text=text, words=words, rate=rate)


def letao(text: str) -> Speech:
    """ElevenLabs « LeTao » (seule voix autorisée), avec l'horodatage de chaque caractère."""
    import base64
    import requests
    from wooplans.settings import VOICE_ID
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/with-timestamps",
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
        json={"text": text, "model_id": "eleven_multilingual_v2"}, timeout=120)
    r.raise_for_status()
    d = r.json()
    a = d["alignment"]
    pieces = list(zip(a["characters"], a["character_start_times_seconds"], a["character_end_times_seconds"]))
    return Speech(base64.b64decode(d["audio_base64"]), text=text, words=timed(text, pieces))


VOICE = letao if os.environ.get("VSL_VOICE") == "letao" else apercu


# --- Texte -------------------------------------------------------------------
def T(s, size=64, color=WHITE, accent=None, max_w=FRAME_W - 0.8):
    t = m.Text(s, color=color, font=FONT, weight=m.BOLD, font_size=size,
               t2c={accent: ORANGE} if accent else None)
    if t.width > max_w:
        t.scale_to_fit_width(max_w)
    return t


def caption(lines, accent=None, y=CAP_Y, first=84, rest=60):
    g = m.VGroup(*[T(s, first if i == 0 else rest, accent=accent) for i, s in enumerate(lines)])
    g.arrange(m.DOWN, buff=0.35).move_to([0, y - g.height / 2, 0])
    return g


def slam(mob, run_time=0.5):
    """Titre qui claque : grandit depuis le centre avec un léger rebond."""
    return m.GrowFromCenter(mob, run_time=run_time, rate_func=m.ease_out_back)


def rise(mob, run_time=0.5):
    return m.FadeIn(mob, shift=0.5 * m.UP, run_time=run_time, rate_func=m.ease_out_cubic)


def underline(mob, color=ORANGE):
    ln = m.Line(mob.get_corner(m.DL) + 0.12 * m.DOWN, mob.get_corner(m.DR) + 0.12 * m.DOWN,
                color=color, stroke_width=10)
    return ln


# --- Fond animé : plan d'architecte qui dérive + particules dorées -----------
def background(scene):
    step = 0.8
    lines = m.VGroup()
    for i in range(-8, 9):
        lines.add(m.Line([i * step, -FRAME_H, 0], [i * step, FRAME_H, 0], stroke_width=1.5))
    for j in range(-12, 13):
        lines.add(m.Line([-FRAME_W, j * step, 0], [FRAME_W, j * step, 0], stroke_width=1.5))
    lines.set_stroke(color=GREEN_LIGHT, opacity=0.35)
    off = [0.0]

    def drift(mob, dt):
        off[0] = (off[0] + 0.12 * dt) % step
        mob.move_to([off[0], off[0] * 0.6, 0])

    lines.add_updater(drift)
    vignette = m.VGroup(
        m.Rectangle(width=FRAME_W + 1, height=3, fill_color=GREEN_DARK, fill_opacity=0.6, stroke_width=0).move_to([0, TOP, 0]),
        m.Rectangle(width=FRAME_W + 1, height=3, fill_color=GREEN_DARK, fill_opacity=0.6, stroke_width=0).move_to([0, -TOP, 0]))
    rng = random.Random(7)
    dots = m.VGroup(*[m.Dot([rng.uniform(-3.8, 3.8), rng.uniform(-7, 7), 0], radius=rng.uniform(0.03, 0.07),
                            color=GOLD).set_opacity(rng.uniform(0.25, 0.6)) for _ in range(22)])
    speeds = [rng.uniform(0.15, 0.45) for _ in dots]

    def float_up(mob, dt):
        for d, v in zip(mob, speeds):
            d.shift([0, v * dt, 0])
            if d.get_y() > TOP + 0.2:
                d.set_y(-TOP - 0.2)

    dots.add_updater(float_up)
    brand = T("WOOPLANS", 34, GOLD)
    brand.move_to([0, TOP - 0.75, 0])
    rule = m.Line([-1.1, TOP - 1.1, 0], [1.1, TOP - 1.1, 0], color=ORANGE, stroke_width=5)
    for mob in (lines, vignette, dots):
        mob.set_z_index(-10)
    scene.add(lines, vignette, dots, brand, rule)


def wipe(scene):
    """Transition : deux bandes (orange puis or) balaient l'écran en diagonale."""
    a = m.Rectangle(width=FRAME_W * 2.2, height=FRAME_H * 0.9, fill_color=ORANGE, fill_opacity=1, stroke_width=0)
    b = a.copy().set_fill(GOLD)
    for r in (a, b):
        r.rotate(0.35).move_to([-FRAME_W * 2.2, 0, 0]).set_z_index(50)
    scene.play(m.LaggedStart(a.animate.move_to([FRAME_W * 2.2, 0, 0]), b.animate.move_to([FRAME_W * 2.2, 0, 0]),
                             lag_ratio=0.3), run_time=0.75, rate_func=m.ease_in_out_cubic)
    scene.remove(a, b)


def clear(scene, *mobs, run_time=0.35):
    mobs = [x for x in mobs if x is not None]
    if mobs:
        scene.play(*[m.FadeOut(x, scale=0.85) for x in mobs], run_time=run_time)


# --- Illustrations -----------------------------------------------------------
def house(w=3.0, body=CREAM, roof=ORANGE, door=GREEN):
    h = w * 0.62
    b = m.Rectangle(width=w, height=h, fill_color=body, fill_opacity=1, stroke_color=WHITE, stroke_width=4)
    r = m.Polygon([-w / 2 - 0.3, h / 2, 0], [w / 2 + 0.3, h / 2, 0], [0, h / 2 + w * 0.42, 0],
                  fill_color=roof, fill_opacity=1, stroke_color=WHITE, stroke_width=4)
    d = m.Rectangle(width=w * 0.18, height=h * 0.48, fill_color=door, fill_opacity=1, stroke_width=0)
    d.move_to([0, -h / 2 + h * 0.24, 0])
    win = [m.Square(side_length=w * 0.17, fill_color=GOLD, fill_opacity=1, stroke_color=GREEN, stroke_width=3)
           .move_to([s * w * 0.3, h * 0.08, 0]) for s in (-1, 1)]
    g = m.VGroup(b, r, d, *win)
    g.body, g.roof = b, r
    return g


def card(scale=1.0, roof=ORANGE):
    c = m.RoundedRectangle(corner_radius=0.15, width=1.9, height=2.5, fill_color=WHITE, fill_opacity=1,
                           stroke_color=GOLD, stroke_width=3)
    hs = house(1.2, body=CREAM, roof=roof).move_to(c.get_center() + 0.35 * m.UP)
    l1 = m.Line([-0.6, -0.65, 0], [0.6, -0.65, 0], color=GREY, stroke_width=8)
    l2 = m.Line([-0.6, -0.9, 0], [0.25, -0.9, 0], color=GREY, stroke_width=8)
    return m.VGroup(c, hs, l1, l2).scale(scale)


def coin(r=0.32):
    c = m.Circle(radius=r, fill_color=GOLD, fill_opacity=1, stroke_color="#B8913C", stroke_width=4)
    return m.VGroup(c, T("F", int(r * 110), GREEN).move_to(c))


def person(color=ORANGE, s=1.0):
    head = m.Circle(radius=0.28, fill_color=CREAM, fill_opacity=1, stroke_width=0).shift(0.62 * m.UP)
    body = m.RoundedRectangle(corner_radius=0.3, width=0.8, height=0.9, fill_color=color, fill_opacity=1, stroke_width=0)
    return m.VGroup(body, head).scale(s)


def check(size=0.6, color=GREEN_LIGHT):
    disc = m.Circle(radius=size / 2, fill_color=color, fill_opacity=1, stroke_color=WHITE, stroke_width=3)
    mk = m.VMobject(stroke_color=WHITE, stroke_width=8)
    mk.set_points_as_corners([[-0.22, 0.0, 0], [-0.05, -0.17, 0], [0.24, 0.17, 0]])
    mk.scale(size / 0.6).move_to(disc)
    return m.VGroup(disc, mk)


def cross(size=1.0, color=RED):
    a = m.Line([-size / 2, -size / 2, 0], [size / 2, size / 2, 0], color=color, stroke_width=14)
    b = m.Line([-size / 2, size / 2, 0], [size / 2, -size / 2, 0], color=color, stroke_width=14)
    return m.VGroup(a, b)


def tile(icon, label, w=3.65, h=3.3):
    box = m.RoundedRectangle(corner_radius=0.25, width=w, height=h, fill_color=GREEN_DARK, fill_opacity=0.9,
                             stroke_color=GOLD, stroke_width=3)
    icon.scale_to_fit_height(h * 0.42).move_to(box.get_center() + h * 0.12 * m.UP)
    lab = T(label, 44, max_w=w - 0.3).move_to(box.get_center() + h * 0.33 * m.DOWN)
    return m.VGroup(box, icon, lab)


def icon_cube():
    s = 0.9
    top = m.Polygon([0, s, 0], [s * 0.87, s / 2, 0], [0, 0, 0], [-s * 0.87, s / 2, 0], fill_color=GOLD, fill_opacity=1, stroke_width=0)
    left = m.Polygon([-s * 0.87, s / 2, 0], [0, 0, 0], [0, -s, 0], [-s * 0.87, -s / 2, 0], fill_color=ORANGE, fill_opacity=1, stroke_width=0)
    right = m.Polygon([s * 0.87, s / 2, 0], [0, 0, 0], [0, -s, 0], [s * 0.87, -s / 2, 0], fill_color=CREAM, fill_opacity=1, stroke_width=0)
    return m.VGroup(top, left, right)


def icon_plan():
    out = m.Rectangle(width=1.8, height=1.4, stroke_color=CREAM, stroke_width=6)
    inner = m.VGroup(m.Line([-0.2, 0.7, 0], [-0.2, -0.2, 0]), m.Line([-0.9, -0.2, 0], [0.3, -0.2, 0]),
                     m.Line([0.3, 0.1, 0], [0.9, 0.1, 0])).set_stroke(CREAM, 5)
    dim = m.Line([-0.9, -0.95, 0], [0.9, -0.95, 0], color=ORANGE, stroke_width=5)
    return m.VGroup(out, inner, dim)


def icon_ruler():
    body = m.Rectangle(width=2.0, height=0.6, fill_color=GOLD, fill_opacity=1, stroke_width=0).rotate(0.5)
    ticks = m.VGroup(*[m.Line([x, 0.3, 0], [x, 0.3 - (0.28 if i % 2 else 0.16), 0], color=GREEN, stroke_width=4)
                       for i, x in enumerate(np.linspace(-0.8, 0.8, 9))]).rotate(0.5, about_point=[0, 0, 0])
    return m.VGroup(body, ticks)


def icon_doc(rows=4):
    page = m.RoundedRectangle(corner_radius=0.08, width=1.4, height=1.8, fill_color=WHITE, fill_opacity=1, stroke_width=0)
    ls = m.VGroup(*[m.Line([-0.45, 0.55 - i * 0.32, 0], [0.45 if i % 2 else 0.2, 0.55 - i * 0.32, 0], color=GREY, stroke_width=7)
                    for i in range(rows)])
    c = coin(0.28).move_to([0.55, -0.75, 0])
    return m.VGroup(page, ls, c)


def price_tag(text):
    lab = T(text, 74, GREEN)
    w, h = lab.width + 1.4, lab.height + 0.9
    body = m.Polygon([-w / 2, h / 2, 0], [w / 2 - 0.5, h / 2, 0], [w / 2, 0, 0], [w / 2 - 0.5, -h / 2, 0], [-w / 2, -h / 2, 0],
                     fill_color=WHITE, fill_opacity=1, stroke_color=ORANGE, stroke_width=6)
    hole = m.Circle(radius=0.13, fill_color=GREEN, fill_opacity=1, stroke_width=0).move_to([w / 2 - 0.55, 0, 0])
    lab.move_to(body.get_center() + 0.3 * m.LEFT)
    return m.VGroup(body, hole, lab)


def chip(text, fill=GREEN_DARK, color=WHITE, size=44):
    lab = T(text, size, color)
    box = m.RoundedRectangle(corner_radius=(lab.height + 0.5) / 2, width=lab.width + 0.8, height=lab.height + 0.5,
                             fill_color=fill, fill_opacity=1, stroke_color=GOLD, stroke_width=3)
    return m.VGroup(box, lab.move_to(box))


def phone():
    shell = m.RoundedRectangle(corner_radius=0.4, width=3.4, height=6.0, fill_color="#12302F", fill_opacity=1,
                               stroke_color=GOLD, stroke_width=5)
    screen = m.RoundedRectangle(corner_radius=0.25, width=3.0, height=5.3, fill_color=CREAM, fill_opacity=1, stroke_width=0)
    hs = house(1.8).move_to(screen.get_center() + 1.2 * m.UP)
    btn = m.RoundedRectangle(corner_radius=0.3, width=2.5, height=0.7, fill_color=ORANGE, fill_opacity=1, stroke_width=0)
    btn.move_to(screen.get_center() + 1.6 * m.DOWN)
    bl = T("Obtenir", 34).move_to(btn)
    g = m.VGroup(shell, screen, hs, btn, bl)
    g.button = m.VGroup(btn, bl)
    return g


def finger():
    return m.VGroup(m.Circle(radius=0.32, fill_color=CREAM, fill_opacity=1, stroke_color=GREEN, stroke_width=4),
                    m.Circle(radius=0.12, fill_color=GOLD, fill_opacity=1, stroke_width=0))


def sad_face(r=0.5, smile=False):
    f = m.Circle(radius=r, fill_color=GOLD, fill_opacity=1, stroke_width=0)
    eyes = m.VGroup(*[m.Dot([s * r * 0.35, r * 0.2, 0], radius=r * 0.1, color=GREEN) for s in (-1, 1)])
    mouth = m.Arc(radius=r * 0.4, start_angle=(m.PI * 1.15 if smile else m.PI * 0.15), angle=m.PI * 0.7,
                  color=GREEN, stroke_width=6)
    mouth.move_to([0, -r * 0.3, 0])
    return m.VGroup(f, eyes, mouth)


def stop_sign(r=0.9):
    o = m.RegularPolygon(8, radius=r, fill_color=RED, fill_opacity=1, stroke_color=WHITE, stroke_width=6).rotate(m.PI / 8)
    return m.VGroup(o, T("STOP", int(r * 60)).move_to(o))


def bubble(w=2.6, h=1.0, fill=WHITE, right=False):
    b = m.RoundedRectangle(corner_radius=0.3, width=w, height=h, fill_color=fill, fill_opacity=1, stroke_width=0)
    sx = 1 if right else -1
    tail = m.Polygon([sx * (w / 2 - 0.5), -h / 2 + 0.05, 0], [sx * (w / 2 - 0.1), -h / 2 + 0.05, 0], [sx * w / 2, -h / 2 - 0.3, 0],
                     fill_color=fill, fill_opacity=1, stroke_width=0)
    ln = m.VGroup(*[m.Line([-w / 2 + 0.3, 0.15 - i * 0.3, 0], [w / 2 - 0.3 - i * 0.6, 0.15 - i * 0.3, 0], color=GREY, stroke_width=7)
                    for i in range(2)])
    return m.VGroup(b, tail, ln)


def fan(n=7, radius=4.2, spread=0.9):
    """Cartes du catalogue, déployées en éventail autour d'un point bas."""
    roofs = [ORANGE, GOLD, GREEN_LIGHT, ORANGE, GOLD, GREEN_LIGHT, ORANGE]
    cards = m.VGroup(*[card(0.95, roofs[i % len(roofs)]) for i in range(n)])
    pivot = np.array([0, ART_Y - radius + 0.6, 0])
    for i, c in enumerate(cards):
        a = (i - (n - 1) / 2) * spread / (n - 1) * 2 * 0.55
        c.move_to(pivot + radius * np.array([np.sin(a), np.cos(a), 0])).rotate(-a)
        c.set_z_index(i)
    return cards, pivot


def burst(mob, vec):
    """Animation d'envol : invisible avant son mot, puis part dans la direction `vec` en s'effaçant."""
    start = mob.get_center().copy()
    mob.set_opacity(0)

    def upd(x, a):
        x.move_to(start + a * np.array(vec))
        x.set_opacity(0 if a == 0 else 1 - a)
    return upd


def counter(target, suffix="", size=120, color=GOLD):
    holder = T(f"0{suffix}", size, color).set_opacity(0)      # invisible jusqu'à son mot

    def upd(mob, a):
        if a > 0:
            mob.become(T(f"{int(round(target * a))}{suffix}", size, color).move_to(mob))
    return holder, upd


def offer_beat(scene, beat):
    """Beat « prix actuel » commun aux trois VSL."""
    v = beat["voix"]
    tag = price_tag("39 000 FCFA").move_to([0, ART_Y + 1.4, 0])
    head = T("Prix actuel", 56, GOLD).next_to(tag, m.UP, buff=0.5)
    unique = chip("Paiement unique") if "paiement unique" in v or "une seule fois" in v else None
    life = chip("∞  Accès à vie")
    shield = chip("✓  Garantie 7 jours", fill=ORANGE)
    chips = [c for c in (unique, life, shield) if c is not None]
    for c in chips:
        c.scale(1.25)
    m.VGroup(*chips).arrange(m.DOWN, buff=0.5).move_to([0, ART_Y - 3.4, 0])
    tag.rotate(-0.25)
    phrases = ["Prix actuel : 39 000 FCFA"]
    anims = [m.AnimationGroup(rise(head), m.SpinInFromNothing(tag, angle=0.6, run_time=0.8, rate_func=m.ease_out_back),
                              m.Flash(tag.get_center() + 0.3 * m.UP, color=GOLD, flash_radius=2.6, line_length=0.6,
                                      num_lines=16, run_time=0.9))]
    if unique is not None:
        phrases.append("paiement unique" if "paiement unique" in v else "une seule fois")
        anims.append(slam(unique))
    phrases.append("ccès à vie")
    anims.append(slam(life))
    phrases.append("satisfait ou remboursé")
    anims.append(m.AnimationGroup(slam(shield), m.Rotate(tag, 0.25, run_time=0.5, rate_func=m.ease_out_back)))
    scene.say(mark(v, *phrases), *anims)
    return [tag, head, *chips]


def cta_beat(scene, beat, last_phrase, extra=None):
    """Beat final : téléphone, doigt qui clique, ondes, flèche vers le lien."""
    v = beat["voix"]
    ph = phone().scale(0.9).move_to([0, ART_Y + 1.4, 0])
    f = finger().move_to(ph.button.get_center() + [1.6, -1.4, 0])
    title = caption([beat["ecran"][0]], accent="lien", y=-2.0)
    sub = T(beat["ecran"][1], 52).next_to(title, m.DOWN, buff=0.45)
    arrow = m.Arrow(sub.get_bottom() + 0.3 * m.DOWN, sub.get_bottom() + 1.3 * m.DOWN, color=GOLD, stroke_width=14, buff=0)
    anims = [
        m.AnimationGroup(m.FadeIn(ph, shift=2 * m.UP, rate_func=m.ease_out_back, run_time=0.7), rise(title)),
        m.Succession(m.FadeIn(f, run_time=0.25), f.animate(run_time=0.35).move_to(ph.button.get_center()),
                     m.AnimationGroup(m.Indicate(ph.button, color=GOLD, scale_factor=1.15),
                                      m.Broadcast(m.Circle(radius=1.4, color=GOLD, stroke_width=6), focal_point=ph.button.get_center(),
                                                  run_time=1.0))),
        m.AnimationGroup(rise(sub), m.GrowArrow(arrow)),
    ]
    phrases = ["Clique sur le lien", None, last_phrase]
    if extra is not None:
        anims.append(extra)
        phrases.append(None)
    scene.say(mark(v, *phrases), *anims)
    for _ in range(3):
        scene.play(arrow.animate.shift(0.3 * m.DOWN), rate_func=m.there_and_back, run_time=0.45)
    scene.wait(0.6)


def helmet_person(color=GREEN_LIGHT, s=1.0):
    p = person(color, 1.0)
    hat = m.Arc(radius=0.33, start_angle=0, angle=m.PI, fill_color=GOLD, fill_opacity=1, stroke_width=0)
    hat.move_to(p[1].get_center() + 0.14 * m.UP)
    brim = m.Rectangle(width=0.8, height=0.08, fill_color=GOLD, fill_opacity=1, stroke_width=0).next_to(hat, m.DOWN, buff=0)
    return m.VGroup(p, hat, brim).scale(s)


def step_badge(n):
    disc = m.Circle(radius=0.7, fill_color=GOLD, fill_opacity=1, stroke_color=WHITE, stroke_width=5)
    num = T(str(n), 80, GREEN).move_to(disc)
    lab = T(f"ÉTAPE {n}", 54, GOLD)
    g = m.VGroup(m.VGroup(disc, num), lab).arrange(m.RIGHT, buff=0.35)
    return g.move_to([0, TOP - 2.1, 0])


def pin(color=ORANGE):
    head = m.Circle(radius=0.45, fill_color=color, fill_opacity=1, stroke_width=0)
    tip = m.Polygon([-0.38, -0.2, 0], [0.38, -0.2, 0], [0, -0.95, 0], fill_color=color, fill_opacity=1, stroke_width=0)
    hole = m.Circle(radius=0.17, fill_color=CREAM, fill_opacity=1, stroke_width=0)
    return m.VGroup(tip, head, hole)


def bricks():
    rows = m.VGroup()
    for r in range(3):
        for c in range(3 - (r % 2)):
            b = m.Rectangle(width=0.7, height=0.32, fill_color="#C8673A", fill_opacity=1, stroke_color=CREAM, stroke_width=3)
            b.move_to([(c - 1) * 0.72 + (0.36 if r % 2 else 0), r * 0.34, 0])
            rows.add(b)
    return rows


def blueprint(w=5.6, h=4.0):
    paper = m.Rectangle(width=w, height=h, fill_color="#1D4E89", fill_opacity=1, stroke_color=WHITE, stroke_width=4)
    x0, y0 = -w / 2 + 0.5, -h / 2 + 0.5
    walls = m.VGroup(
        m.Rectangle(width=w - 1.0, height=h - 1.0),
        m.Line([x0 + (w - 1) * 0.45, y0, 0], [x0 + (w - 1) * 0.45, y0 + (h - 1) * 0.6, 0]),
        m.Line([x0, y0 + (h - 1) * 0.6, 0], [x0 + (w - 1) * 0.8, y0 + (h - 1) * 0.6, 0]),
        m.Line([x0 + (w - 1) * 0.7, y0 + (h - 1) * 0.6, 0], [x0 + (w - 1) * 0.7, y0 + h - 1, 0]),
    ).set_stroke(WHITE, 5)
    dim = m.VGroup(m.Line([x0, h / 2 - 0.22, 0], [x0 + w - 1, h / 2 - 0.22, 0]),
                   m.Line([x0, h / 2 - 0.32, 0], [x0, h / 2 - 0.12, 0]),
                   m.Line([x0 + w - 1, h / 2 - 0.32, 0], [x0 + w - 1, h / 2 - 0.12, 0])).set_stroke(GOLD, 4)
    return m.VGroup(paper, walls, dim)
