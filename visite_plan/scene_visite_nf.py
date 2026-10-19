"""Variante SANS 3D : écran 9:16, bande de titre en haut, plan seul (pas de façade). Dérivé de scene_visite.py.

Les trajets du point sont calculés sur l'image du plan (make_paths.py) : il contourne
les murs et passe uniquement par les portes et ouvertures.

Rendu : manimgx render scene.py VisitePlan -r 1080x1920 --fps 30
"""

import json
import math
from pathlib import Path

import manimgx as m

HERE = Path(__file__).parent
import os
JOB = Path(os.environ.get("JOB", str(HERE / "jobs" / "V3-003")))
META = json.loads((JOB / "meta.json").read_text(encoding="utf-8"))
SEGS = json.loads((JOB / "segments.json").read_text(encoding="utf-8"))
SEG = SEGS[int(os.environ["SEG"])] if os.environ.get("SEG") not in (None, "") else None
PATHS = json.loads((JOB / "paths.json").read_text(encoding="utf-8"))

# --- Charte WooPlans ---------------------------------------------------------
BG = "#FFFFFF"          # fond blanc de la zone animée
GREEN = "#0F5B59"       # Primary
ORANGE = "#F08A2E"      # Accent  -> voile de surbrillance + séparateur
GOLD = "#E7C36C"        # Highlight -> traînée

m.config.background_color = BG
m.config.pixel_width, m.config.pixel_height = 1080, 1920

PLAN_IMG = str(JOB / "plan.png")
PLAN_IMG2 = JOB / "plan_etage.png"           # duplex : plan de l'étage (même canevas que plan.png)
FACADE_IMG = str(JOB / "facade.png")

# --- Géométrie de l'écran (cadre 9:16 = 8 x 14.222 unités) -------------------
FRAME_W = 8.0
FRAME_H = 8.0 * 1920 / 1080
FACADE_H = 0.0                                  # variante sans 3D : pas de façade
BAND_H = 0.95                                   # bande de titre (une ligne de texte)
BAND_TEXT = META["band"]
PANEL_TOP = FRAME_H / 2 - FACADE_H - BAND_H     # haut de la zone plan animée
ZOOM_RATIO = 0.5                                # 1 = zoom d'origine, 0.5 = moitié moins serré
PANEL_BOTTOM = -FRAME_H / 2
PANEL_H = 9.6                                   # hauteur utile pour le calcul du zoom
PANEL_CENTER = (0.0, 0.9)                       # plan au-dessus de la zone des sous-titres

PLAN_W_PX, PLAN_H_PX = 1024, 1024
U = 7.7 / 1024                                  # plan de 7,7 unités de large (marge de 0,15 de chaque côté)                          # unités écran par pixel du plan


def scr(p) -> list[float]:
    """Pixel du plan -> point écran."""
    x, y = p
    return [(x - PLAN_W_PX / 2) * U + PANEL_CENTER[0],
            -(y - PLAN_H_PX / 2) * U + PANEL_CENTER[1], 0.0]


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


POLYS = {r["name"]: [tuple(p) for p in r["poly"]] for r in PATHS["rooms"]}

SYNC = {it["name"]: it for it in json.loads((JOB / "sync.json").read_text(encoding="utf-8"))["items"]}
SYNC_TOTAL = json.loads((JOB / "sync.json").read_text(encoding="utf-8"))["total"]
LEAD = 0.5          # la voix démarre un peu avant l'arrivée du point
TAIL = 0.3
INTRO = 1.2
OUTRO = 1.6
T_DIM_IN = 0.35
T_ZOOM = 0.85
T_VEIL_OUT = 0.4
T_ZOOM_OUT = 0.8


def path_len(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def transit_time(pts):
    return 0.5 + 0.00085 * path_len(pts)


class VisitePlan(m.Scene):
    def construct(self) -> None:
        start = SEG["start_pos"] if SEG else PATHS["start"]
        rooms = [r for r in PATHS["rooms"] if (SEG is None or r["name"] in SEG["rooms"])]

        # ---- Plan (zone du bas) ------------------------------------------------
        def load_plan(level):
            im = m.ImageMobject(PLAN_IMG if level == 0 else str(PLAN_IMG2))
            im.scale_to_fit_height(PLAN_H_PX * U).move_to([*PANEL_CENTER, 0])
            im.set_z_index(0)
            return im
        level = [SEG.get("level", 0) if SEG else 0]      # niveau affiché (0 = RDC, 1 = étage)
        plan_img = load_plan(level[0])
        plan = m.Group(plan_img)
        cur_img = [plan_img]
        plan_rect_pts = [scr(p) for p in rect(0, 0, PLAN_W_PX, PLAN_H_PX)]

        # ---- Bandeau du haut : façade fixe, couvre tout débordement du zoom ----
        top_h = FACADE_H + BAND_H
        cover = m.Rectangle(width=FRAME_W + 1, height=top_h + 6, fill_color=BG,
                            fill_opacity=1, stroke_width=0)
        cover.move_to([0, PANEL_TOP + (top_h + 6) / 2, 0]).set_z_index(10)
        band_y = FRAME_H / 2 - FACADE_H - BAND_H / 2
        band = m.Rectangle(width=FRAME_W + 0.2, height=BAND_H, fill_color=GREEN,
                           fill_opacity=1, stroke_width=0).move_to([0, band_y, 0]).set_z_index(11)
        band_text = m.Text(BAND_TEXT, color=m.WHITE, font="Noto Sans", weight=m.BOLD,
                           font_size=44)
        if band_text.width > FRAME_W - 0.7:          # reste sur une seule ligne
            band_text.scale_to_fit_width(FRAME_W - 0.7)
        band_text.move_to([0, band_y, 0]).set_z_index(12)
        divider = m.Line([-FRAME_W / 2, FRAME_H / 2 - BAND_H, 0],
                         [FRAME_W / 2, FRAME_H / 2 - BAND_H, 0],
                         color=ORANGE, stroke_width=6).set_z_index(13)

        # ---- Point pulsant + traînée ------------------------------------------
        core = m.Dot(point=scr(start), radius=0.14, color=GREEN, stroke_color=m.WHITE,
                     stroke_width=3).set_z_index(7)
        halo = m.Circle(radius=0.2, color=GREEN, stroke_width=4, fill_color=GREEN,
                        fill_opacity=0.3).set_z_index(5)
        def new_trail():
            return m.TracedPath(core.get_center, dissipating_time=0.6, stroke_color=GREEN,
                                stroke_width=9, stroke_opacity=[0.0, 0.85]).set_z_index(4)

        clock = [0.0]

        def core_up(mob, dt):
            mob.scale_to_fit_width(0.28)

        def halo_up(mob, dt):
            clock[0] += dt
            ph = (clock[0] % 1.1) / 1.1
            mob.scale_to_fit_width(2 * (0.18 + 0.5 * ph))
            mob.move_to(core.get_center())
            mob.set_stroke(opacity=1 - ph)
            mob.set_fill(opacity=0.3 * (1 - ph))

        core.add_updater(core_up)
        halo.add_updater(halo_up)

        self.add(plan, cover, band, band_text, divider, halo, core)
        t = [SEG["t0"] if SEG else 0.0]          # horloge de la scène (secondes, temps absolu de la vidéo)
        timeline = []

        def play(*a, run_time, **k):
            self.play(*a, run_time=run_time, **k)
            t[0] += run_time

        def wait_until(x):
            if x > t[0]:
                self.wait(x - t[0])
                t[0] = x

        for room in rooms:
            name = room["name"]
            poly = POLYS[name]

            # 1) le point se promène jusqu'à la pièce, par les portes
            path = m.VMobject()
            path.set_points_as_corners([scr(p) for p in room["path"]])
            trail = new_trail()
            self.add(trail)
            sy = SYNC[name]
            nat = transit_time(room["path"])
            tr = max(0.6, sy["arrive"] - t[0])          # le point s'arrête pile sur le nom de la pièce
            if tr > nat * 1.6:                          # trop de temps : il attend, puis se met en marche
                self.wait(tr - nat * 1.6)
                t[0] += tr - nat * 1.6
                tr = nat * 1.6
            play(m.MoveAlongPath(core, path), run_time=tr, rate_func=m.ease_in_out_sine)

            # 2) voile coloré sur la pièce (le reste du plan reste intact)
            veil = m.Polygon(*[scr(p) for p in poly], fill_color=ORANGE, fill_opacity=0.42,
                             stroke_color=ORANGE, stroke_width=4).set_z_index(2)
            plan.add(veil)
            play(m.FadeIn(veil), m.FadeOut(trail), run_time=T_DIM_IN)
            self.remove(trail)

            sw = room.get("switch_to")                   # montée / descente d'étage

            def end_veil():
                """retire le voile ; si la pièce est un escalier, bascule vers l'autre niveau."""
                if sw is None:
                    play(m.FadeOut(veil), run_time=T_VEIL_OUT)
                    return
                old, new = cur_img[0], load_plan(sw)
                plan.add(new)
                play(m.FadeOut(veil), m.FadeOut(old), m.FadeIn(new),
                     core.animate.move_to(scr(room["jump_to"])), run_time=0.8)
                plan.remove(old); self.remove(old)
                cur_img[0] = new; level[0] = sw

            if sy["zoom"]:
                # 3) zoom avant centré sur la pièce
                xs = [p[0] for p in poly]
                ys = [p[1] for p in poly]
                bw, bh = (max(xs) - min(xs)) * U, (max(ys) - min(ys)) * U
                k_fit = max(1.5, min(7.0 / bw, (PANEL_H - 1.8) / bh, 3.4))
                k = 1 + (k_fit - 1) * ZOOM_RATIO
                c = scr(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2))
                d = [PANEL_CENTER[0] - c[0], PANEL_CENTER[1] - c[1], 0.0]
                p0 = core.get_center()
                p1 = [c[0] + k * (p0[0] - c[0]) + d[0], c[1] + k * (p0[1] - c[1]) + d[1], 0.0]
                play(plan.animate.scale(k, about_point=c).shift(d), core.animate.move_to(p1),
                     run_time=T_ZOOM, rate_func=m.ease_in_out_cubic)
                # 4) pièce présentée, point pulsant immobile pendant que la voix continue
                wait_until(sy["zout_start"])
                end_veil()
                # 6) retour au plan complet
                play(plan.animate.shift([-d[0], -d[1], 0]).scale(1 / k, about_point=c),
                     core.animate.move_to(p0), run_time=T_ZOOM_OUT, rate_func=m.ease_in_out_cubic)
            else:
                # pièce sans zoom : voile seul (évite l'effet monotone)
                wait_until(sy["zout_start"])
                end_veil()
            plan.remove(veil)
            self.remove(veil)

        if SEG is not None and not SEG["final"]:
            wait_until(SEG["t1"])
            return

        # ---- Final : on retire le point, plan seul jusqu'à la fin ----
        fin = SYNC["Final"]
        wait_until(fin["start"])
        play(m.FadeOut(core), m.FadeOut(halo), run_time=0.6)
        core.clear_updaters(); halo.clear_updaters()
        if SYNC_TOTAL > t[0]:
            self.wait(SYNC_TOTAL - t[0])
