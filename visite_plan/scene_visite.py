"""Visite guidée du plan RDC : écran 9:16 scindé (façade fixe en haut, plan animé en bas).

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
FACADE_IMG = str(JOB / "facade.png")

# --- Géométrie de l'écran (cadre 9:16 = 8 x 14.222 unités) -------------------
FRAME_W = 8.0
FRAME_H = 8.0 * 1920 / 1080
HAS_FACADE = META.get("facade", True)          # False : visite sans 3D (pas de façade en haut)
FACADE_H = FRAME_W * META.get("facade_ratio", 0.5625) if HAS_FACADE else 0.0
BAND_H = 0.95                                   # bande de titre (une ligne de texte)
BAND_TEXT = META["band"]
PANEL_TOP = FRAME_H / 2 - FACADE_H - BAND_H     # haut de la zone plan animée
ZOOM_RATIO = 0.5                                # 1 = zoom d'origine, 0.5 = moitié moins serré
PANEL_BOTTOM = -FRAME_H / 2
PANEL_H = PANEL_TOP - PANEL_BOTTOM
PANEL_CENTER = (0.0, (PANEL_TOP + PANEL_BOTTOM) / 2)

PLAN_W_PX, PLAN_H_PX = META.get("plan_px", (1000, 1072))
U = min(FRAME_W / PLAN_W_PX, PANEL_H / PLAN_H_PX)                          # unités écran par pixel du plan


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
        plan_img = m.ImageMobject(PLAN_IMG)
        plan_img.scale_to_fit_height(PLAN_H_PX * U).move_to([*PANEL_CENTER, 0])
        plan_img.set_z_index(0)
        plan = m.Group(plan_img)
        plan_rect_pts = [scr(p) for p in rect(0, 0, PLAN_W_PX, PLAN_H_PX)]

        # ---- Bandeau du haut : façade fixe, couvre tout débordement du zoom ----
        top_h = FACADE_H + BAND_H
        cover = m.Rectangle(width=FRAME_W + 1, height=top_h + 6, fill_color=BG,
                            fill_opacity=1, stroke_width=0)
        cover.move_to([0, PANEL_TOP + (top_h + 6) / 2, 0]).set_z_index(10)
        facade = m.Group()
        if HAS_FACADE:
            facade = m.ImageMobject(FACADE_IMG)
            facade.scale_to_fit_width(FRAME_W).move_to([0, FRAME_H / 2 - FACADE_H / 2, 0]).set_z_index(11)
        band_y = FRAME_H / 2 - FACADE_H - BAND_H / 2
        band = m.Rectangle(width=FRAME_W + 0.2, height=BAND_H, fill_color=GREEN,
                           fill_opacity=1, stroke_width=0).move_to([0, band_y, 0]).set_z_index(11)
        band_text = m.Text(BAND_TEXT, color=m.WHITE, font="Noto Sans", weight=m.BOLD,
                           font_size=44)
        if band_text.width > FRAME_W - 0.7:          # reste sur une seule ligne
            band_text.scale_to_fit_width(FRAME_W - 0.7)
        band_text.move_to([0, band_y, 0]).set_z_index(12)
        divider = m.Line([-FRAME_W / 2, FRAME_H / 2 - FACADE_H, 0],
                         [FRAME_W / 2, FRAME_H / 2 - FACADE_H, 0],
                         color=ORANGE, stroke_width=6 if HAS_FACADE else 0).set_z_index(13)

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

        self.add(plan, cover, facade, band, band_text, divider, halo, core)
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
                play(m.FadeOut(veil), run_time=T_VEIL_OUT)
                # 6) retour au plan complet
                play(plan.animate.shift([-d[0], -d[1], 0]).scale(1 / k, about_point=c),
                     core.animate.move_to(p0), run_time=T_ZOOM_OUT, rate_func=m.ease_in_out_cubic)
            else:
                # pièce sans zoom : voile seul (évite l'effet monotone)
                wait_until(sy["zout_start"])
                play(m.FadeOut(veil), run_time=T_VEIL_OUT)
            plan.remove(veil)
            self.remove(veil)

        if SEG is not None and not SEG["final"]:
            wait_until(SEG["t1"])
            return

        # ---- Final : zoom arrière sur toute la maison, puis cotes globales (longueur / largeur) ----
        fin = SYNC["Final"]
        wait_until(fin["start"])
        ZF = 0.84                                   # zoom arrière : la maison + les cotes restent bien dans l'écran
        cf = [PANEL_CENTER[0], PANEL_CENTER[1], 0.0]
        play(m.FadeOut(core), m.FadeOut(halo), plan.animate.scale(ZF, about_point=cf),
             run_time=1.0, rate_func=m.ease_in_out_cubic)
        core.clear_updaters(); halo.clear_updaters()
        if "walls" not in META:                     # pas de cotes sans PDF : zoom arrière seul
            if SYNC_TOTAL > t[0]:
                self.wait(SYNC_TOTAL - t[0])
            return
        DIM = "#C75B3A"
        def PT(x, y):            # coordonnées plan.png (px) -> écran, après zoom arrière
            p = scr((x, y))
            return [cf[0] + (p[0] - cf[0]) * ZF, cf[1] + (p[1] - cf[1]) * ZF, 0.0]
        L, R, T_, B_ = META["walls"]               # murs extérieurs (px de plan.png) : x gauche/droite, y haut/bas
        def dim_line(a, b, ta, tb):
            return (m.Line(a, b, color=DIM, stroke_width=7).set_z_index(6),
                    m.Line(ta[0], ta[1], color=DIM, stroke_width=7).set_z_index(6),
                    m.Line(tb[0], tb[1], color=DIM, stroke_width=7).set_z_index(6))
        vx = L - 43
        v_ln, v_a, v_b = dim_line(PT(vx, T_), PT(vx, B_),
                                  (PT(vx - 14, T_), PT(vx + 14, T_)), (PT(vx - 14, B_), PT(vx + 14, B_)))
        v_txt = m.Text(META["dim_depth"], color=GREEN, font="Noto Sans", weight=m.BOLD, font_size=36).rotate(m.PI / 2)
        v_txt.move_to(PT(vx - 36, (T_ + B_) / 2)).set_z_index(6)
        hy = T_ - 36
        h_ln, h_a, h_b = dim_line(PT(L, hy), PT(R, hy),
                                  (PT(L, hy - 14), PT(L, hy + 14)), (PT(R, hy - 14), PT(R, hy + 14)))
        h_txt = m.Text(META["dim_front"], color=GREEN, font="Noto Sans", weight=m.BOLD, font_size=36)
        h_txt.move_to(PT((L + R) / 2, hy - 30)).set_z_index(6)

        wait_until(fin["dim1"])
        play(m.Create(v_ln), m.Create(v_a), m.Create(v_b), m.FadeIn(v_txt), run_time=0.9)
        wait_until(fin["dim2"])
        play(m.Create(h_ln), m.Create(h_a), m.Create(h_b), m.FadeIn(h_txt), run_time=0.9)

        if SYNC_TOTAL > t[0]:
            self.wait(SYNC_TOTAL - t[0])
