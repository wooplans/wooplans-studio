"""VSL Catalogue Premium (9:16) : texte animé sur la charte WooPlans, calé sur la voix off.

Entrées (variables d'environnement) :
  VSL   : script JSON (vsl/scripts/<id>.json)
  SYNC  : optionnel, JSON {"starts": [t0, t1, ...], "total": T} (début de chaque beat dans la voix LeTao) ;
          sans lui, la durée de chaque beat est estimée sur le nombre de mots.
  ASSETS: optionnel, dossier d'images (<image>.png, ex. catalogue.png) montrées au-dessus du texte.

Rendu : VSL=scripts/vsl1_erreur.json manimgx render scene_vsl.py VSL -r 1080x1920 --fps 30
"""

import json
import os
from pathlib import Path

import manimgx as m

HERE = Path(__file__).parent
SCRIPT = json.loads(Path(os.environ.get("VSL", str(HERE / "scripts" / "vsl1_erreur.json"))).read_text(encoding="utf-8"))
BEATS = SCRIPT["beats"]
ASSETS = Path(os.environ.get("ASSETS", str(HERE / "assets")))

# --- Charte WooPlans ---------------------------------------------------------
GREEN = "#0F5B59"       # Primary  -> fond
ORANGE = "#F08A2E"      # Accent   -> mot clé, bouton
GOLD = "#E7C36C"        # Highlight -> numéros d'étape, barre de progression
FONT = "Noto Sans"

m.config.background_color = GREEN
m.config.pixel_width, m.config.pixel_height = 1080, 1920

FRAME_W = 8.0
FRAME_H = 8.0 * 1920 / 1080
TEXT_W = FRAME_W - 1.0
WORDS_PER_S = 2.7       # débit moyen de LeTao, utilisé seulement sans SYNC


def estimated_timing():
    starts, t = [], 0.0
    for b in BEATS:
        starts.append(t)
        t += len(b["voix"].split()) / WORDS_PER_S + 0.4
    return {"starts": starts, "total": t + 0.8}


TIMING = json.loads(Path(os.environ["SYNC"]).read_text(encoding="utf-8")) if os.environ.get("SYNC") else estimated_timing()


def text(s, size, color=m.WHITE):
    t = m.Text(s, color=color, font=FONT, weight=m.BOLD, font_size=size)
    if t.width > TEXT_W:                    # une ligne = une ligne, jamais coupée
        t.scale_to_fit_width(TEXT_W)
    return t


def line_color(line, beat):
    acc = beat.get("accent", "")
    return ORANGE if acc and acc.lower() in line.lower() else m.WHITE


class VSL(m.Scene):
    def construct(self) -> None:
        t = [0.0]

        def play(*a, run_time, **k):
            self.play(*a, run_time=run_time, **k)
            t[0] += run_time

        def wait_until(x):
            if x > t[0]:
                self.wait(x - t[0])
                t[0] = x

        # ---- Habillage fixe : marque en haut, barre de progression en bas ----
        brand = text("WOOPLANS", 34, GOLD).move_to([0, FRAME_H / 2 - 0.7, 0])
        rule = m.Line([-1.2, FRAME_H / 2 - 1.05, 0], [1.2, FRAME_H / 2 - 1.05, 0], color=ORANGE, stroke_width=5)
        total = TIMING["total"]
        bar_y = -FRAME_H / 2 + 0.25
        bar = m.Rectangle(width=FRAME_W, height=0.12, fill_color=GOLD, fill_opacity=1, stroke_width=0)
        bar.move_to([0, bar_y, 0])
        clock = [0.0]

        def bar_up(mob, dt):
            clock[0] += dt
            w = max(0.01, FRAME_W * min(1.0, clock[0] / total))
            mob.stretch_to_fit_width(w)
            mob.move_to([-FRAME_W / 2 + w / 2, bar_y, 0])

        bar.add_updater(bar_up)
        self.add(brand, rule, bar)

        shown = None
        for i, beat in enumerate(BEATS):
            wait_until(TIMING["starts"][i])
            if shown is not None:
                play(m.FadeOut(shown), run_time=0.25)
                self.remove(shown)

            parts = []
            top = 2.6                                   # haut de la zone texte
            img_path = ASSETS / f"{beat['image']}.png" if beat.get("image") else None
            if img_path and img_path.exists():
                img = m.ImageMobject(str(img_path))
                img.scale_to_fit_width(FRAME_W - 0.8)
                if img.height > 4.6:
                    img.scale_to_fit_height(4.6)
                img.move_to([0, 3.4, 0])
                parts.append(img)
                top = 3.4 - img.height / 2 - 0.6
            if beat["type"] == "etape":
                disc = m.Circle(radius=0.75, color=GOLD, fill_color=GOLD, fill_opacity=1, stroke_width=0)
                num = text(str(beat["numero"]), 80, GREEN)
                disc.move_to([0, top - 0.75, 0])
                num.move_to(disc.get_center())
                parts += [disc, num]
                top -= 1.9

            size = 76 if beat["type"] in ("hook", "offre") else 62
            lines = []
            for j, s in enumerate(beat["ecran"]):
                ln = text(s, size if j == 0 else size - 10, line_color(s, beat))
                ln.move_to([0, top - ln.height / 2, 0])
                top -= ln.height + 0.45
                lines.append(ln)

            extra = []
            if beat["type"] == "offre":                 # carte blanche derrière le prix
                card = m.Rectangle(width=TEXT_W + 0.4, height=lines[0].height + 0.7, fill_color=m.WHITE,
                                   fill_opacity=1, stroke_color=ORANGE, stroke_width=6)
                card.move_to(lines[0].get_center()).set_z_index(-1)
                lines[0].set_color(GREEN)
                extra.append(card)
            if beat["type"] == "cta":                   # bouton orange + flèche vers le lien
                btn = m.Rectangle(width=TEXT_W + 0.2, height=lines[0].height + 0.8, fill_color=ORANGE,
                                  fill_opacity=1, stroke_width=0)
                btn.move_to(lines[0].get_center()).set_z_index(-1)
                lines[0].set_color(m.WHITE)
                arrow = m.Line([0, top - 0.2, 0], [0, top - 1.6, 0], color=GOLD, stroke_width=12)
                tip_l = m.Line([0, top - 1.6, 0], [-0.45, top - 1.1, 0], color=GOLD, stroke_width=12)
                tip_r = m.Line([0, top - 1.6, 0], [0.45, top - 1.1, 0], color=GOLD, stroke_width=12)
                extra += [btn, arrow, tip_l, tip_r]

            group = m.Group(*parts, *extra, *lines)
            # centrage vertical du bloc (sans image) pour un rendu équilibré
            if not (img_path and img_path.exists()):
                group.move_to([0, 0.2, 0])

            dur = (TIMING["starts"][i + 1] if i + 1 < len(BEATS) else total) - t[0]
            step = min(0.45, max(0.2, dur * 0.5 / max(1, len(lines))))
            if parts:
                play(*[m.FadeIn(p) for p in parts], run_time=0.35)
            if extra:
                play(*[m.FadeIn(e) for e in extra], run_time=0.3)
            for ln in lines:
                play(m.FadeIn(ln), run_time=step, rate_func=m.ease_in_out_cubic)
            if beat["type"] in ("hook", "cta"):         # petit battement pour accrocher l'œil
                play(lines[0].animate.scale(1.06), run_time=0.2)
                play(lines[0].animate.scale(1 / 1.06), run_time=0.2)
            shown = group

        wait_until(total)
