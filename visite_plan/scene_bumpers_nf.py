"""Hook et CTA de la variante « visite sans 3D » (9:16). Rendu : manimgx render scene_bumpers_nf.py HookNF|CtaNF
Variables : JOB (bump.json, plan.png, walls.png, logo_white.png, band_bottom.png)."""
import sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import manimgx as m
from scene_bumpers import (Base, B, JOB, T, FRAME_W, FRAME_H, BAND_H, BB_Y, GREEN, ORANGE, GOLD, WHITE_,
                           OUT, OUT_BACK, INOUT)

BAND_Y = FRAME_H / 2 - BAND_H / 2
PLAN_CY = 0.9                       # même centre et même échelle que le corps (scene_visite_nf.py)
PLAN_SIDE = 7.7


def plan_img(name, z):
    im = m.ImageMobject(str(JOB / name))
    im.scale_to_fit_height(PLAN_SIDE).move_to([0, PLAN_CY, 0]).set_z_index(z)
    return im


def pp(x, y):
    """pixel du plan (1024) -> point écran."""
    return [(x - 512) * PLAN_SIDE / 1024, -(y - 512) * PLAN_SIDE / 1024 + PLAN_CY, 0.0]


BEDS = [(165, 150), (175, 705), (860, 275), (870, 790)]            # chambres 1, 2, 3, principale
WETS = [(75, 335), (75, 523), (935, 430), (935, 555)]              # 4 salles d'eau (WC/douche x3, salle de bain)
BLUE = "#3FA7D6"


class HookNF(Base):
    def construct(self):
        self.setup_clock()
        H = B["hook"]; C = H["cues"]
        self.bg(GREEN)
        self.add(self.grid(0.10))
        # plan « dessiné » : murs blancs révélés par un balayage de gauche à droite
        walls = plan_img("plan.png", 5)
        walls.add_updater(lambda mob, dt: mob.scale(1 + 0.01 * dt))
        mask = m.Rectangle(width=FRAME_W + 1, height=FRAME_H + 1, fill_color=GREEN, fill_opacity=1,
                           stroke_width=0).set_z_index(6)
        mask.move_to([0.5, 0, 0])
        edge = m.Line([-4.0, PLAN_CY - 4.1, 0], [-4.0, PLAN_CY + 4.1, 0], color=GOLD, stroke_width=6).set_z_index(7)
        self.add(walls, mask, edge)
        self.go(mask.animate.shift([FRAME_W + 1.0, 0, 0]), edge.animate.shift([FRAME_W + 1.0, 0, 0]),
                rt=C["draw1"], rate=m.linear)
        self.remove(mask, edge)

        # titres : « REGARDEZ CE PLAN » puis « DONNEZ VOTRE AVIS » + bulle « EN COMMENTAIRE »
        t1 = T(H.get("t1_text", "REGARDEZ CE PLAN"), 78, WHITE_, width=7.0).move_to([0, 6.6, 0]).set_z_index(10)
        t2 = T(H.get("t2_text", "DONNEZ VOTRE AVIS"), 66, GOLD, width=6.6).move_to([0, 5.9, 0]).set_z_index(10)
        bub = m.RoundedRectangle(corner_radius=0.35, width=6.2, height=0.95, fill_color=ORANGE, fill_opacity=1,
                                 stroke_color=WHITE_, stroke_width=4)
        tail = m.Polygon([-1.9, -0.45, 0], [-1.3, -0.45, 0], [-1.9, -0.95, 0], fill_color=ORANGE, fill_opacity=1,
                         stroke_width=0)
        btx = T("EN COMMENTAIRE", 44, WHITE_, width=5.0)
        q = m.Group(bub, tail, btx).move_to([0, 4.65, 0]).set_z_index(11)
        self.until(C["t1"]); self.pop(t1, 0.3)
        self.until(C["t2"]); self.pop(t2, 0.3)
        self.until(C["t3"]); self.pop(q, 0.35, 0.6)
        self.until(C["pulse"])
        self.go(q.animate.scale(1.08), rt=0.14, rate=OUT)
        self.go(q.animate.scale(1 / 1.08), rt=0.25, rate=OUT)

        # ---- transition : le plan se remplit (rendu 2D), la bande de titre et la bande basse se posent
        self.until(C["trans"])
        walls.clear_updaters()
        panel = m.Rectangle(width=FRAME_W + 0.4, height=FRAME_H, fill_color=WHITE_, fill_opacity=1,
                            stroke_width=0).set_z_index(20)
        panel.move_to([0, 0, 0]).set_opacity(0)
        plan = plan_img("plan.png", 21)
        plan.set_opacity(0)
        self.add(panel, plan)
        band = m.Rectangle(width=FRAME_W + 0.2, height=BAND_H, fill_color=GREEN, fill_opacity=1,
                           stroke_width=0).move_to([0, BAND_Y + 1.2, 0]).set_z_index(31)
        bt = T(B["band"], 44, WHITE_)
        if bt.width > FRAME_W - 0.7:
            bt.scale_to_fit_width(FRAME_W - 0.7)
        bt.move_to([0, BAND_Y + 1.2, 0]).set_z_index(32)
        div = m.Line([-FRAME_W / 2, FRAME_H / 2 - BAND_H, 0], [FRAME_W / 2, FRAME_H / 2 - BAND_H, 0],
                     color=ORANGE, stroke_width=6).set_z_index(33)
        div.set_stroke(opacity=0)
        bb = m.ImageMobject(str(JOB / "band_bottom.png")); bb.scale_to_fit_width(FRAME_W)
        bb.move_to([0, BB_Y - 2.2, 0]).set_z_index(40)
        self.add(band, bt, div, bb)
        self.go(panel.animate.set_opacity(1), plan.animate.set_opacity(1),
                band.animate.move_to([0, BAND_Y, 0]), bt.animate.move_to([0, BAND_Y, 0]),
                div.animate.set_stroke(opacity=1), bb.animate.move_to([0, BB_Y, 0]),
                m.FadeOut(q), m.FadeOut(t1), m.FadeOut(t2), rt=0.75, rate=INOUT)
        self.remove(walls)
        sp = pp(*B["start_pos"])
        core = m.Dot(point=sp, radius=0.14, color=GREEN, stroke_color=WHITE_, stroke_width=3).set_z_index(27)
        halo = m.Circle(radius=0.2, color=GREEN, stroke_width=4, fill_color=GREEN, fill_opacity=0.3).set_z_index(26)
        hc = [0.0]
        def halo_up(mob, dt):
            hc[0] += dt
            ph = (hc[0] % 1.1) / 1.1
            mob.scale_to_fit_width(2 * (0.18 + 0.5 * ph)); mob.move_to(sp)
            mob.set_stroke(opacity=1 - ph); mob.set_fill(opacity=0.3 * (1 - ph))
        halo.add_updater(halo_up)
        self.until(C["dot"])
        self.add(halo)
        self.go(m.FadeIn(core), rt=0.5, rate=INOUT)
        self.until(H["total"])


class CtaNF(Base):
    """CTA : on clique sur l'adresse du site (wooplans.com)."""
    def construct(self):
        self.setup_clock()
        Cc = B["cta"]; C = Cc["cues"]
        self.bg(GREEN)
        self.add(self.grid(0.10))
        LY = 4.9
        logo = m.ImageMobject(str(JOB / "logo_white.png"))
        logo.scale_to_fit_width(4.4).move_to([0, LY, 0]).set_z_index(10)
        clk = [0.0]
        rings = []
        for i in range(3):
            r = m.Circle(radius=1.0, color=GOLD, stroke_width=4).move_to([0, LY, 0]).set_z_index(3)
            def rup(mob, dt, i=i):
                if i == 0:
                    clk[0] += dt
                ph = (clk[0] / 1.6 + i / 3.0) % 1.0
                mob.scale_to_fit_width(2 * (1.6 + 3.0 * ph)); mob.move_to([0, LY, 0])
                mob.set_stroke(opacity=0.5 * (1 - ph))
            r.add_updater(rup); r.set_stroke(opacity=0); rings.append(r)
        self.add(*rings)
        logo.scale(0.6)
        self.add(logo)
        self.go(m.FadeIn(logo), logo.animate.scale(1 / 0.6), rt=0.3, rate=OUT_BACK)
        fl = [0.0]
        def float_up(mob, dt):
            fl[0] += dt
            mob.move_to([0, LY + 0.07 * math.sin(fl[0] * 2.2), 0])
        logo.add_updater(float_up)
        # titre : « D'AUTRES MODÈLES »
        h1 = T(Cc.get("h1_text", "DÉCOUVREZ"), 66, WHITE_, width=5.2).move_to([0, 2.85, 0]).set_z_index(10)
        h2 = T(Cc.get("h2_text", "TOUS NOS PLANS"), 66, GOLD, width=6.4).move_to([0, 1.7, 0]).set_z_index(10)
        self.until(C["h1"]); self.pop(h1, 0.3)
        self.until(C["h2"]); self.pop(h2, 0.32)
        # l'adresse du site est le bouton sur lequel on clique
        UY, UW, UH = 0.1, 7.0, 1.7
        ub = m.RoundedRectangle(corner_radius=0.5, width=UW, height=UH, fill_color=ORANGE, fill_opacity=1,
                                stroke_color=WHITE_, stroke_width=5).move_to([0, UY, 0]).set_z_index(10)
        ut = T("wooplans.com", 76, WHITE_, width=5.9).move_to([0, UY, 0]).set_z_index(11)
        url = m.Group(ub, ut)
        self.until(C["button"]); self.pop(url, 0.32, 0.5)
        halo = m.RoundedRectangle(corner_radius=0.5, width=UW, height=UH, color=ORANGE, stroke_width=5,
                                  fill_opacity=0).move_to([0, UY, 0]).set_z_index(9)
        hc = [0.0]
        def hup(mob, dt):
            hc[0] += dt
            ph = (hc[0] % 1.2) / 1.2
            mob.stretch_to_fit_width(UW * (1 + 0.12 * ph)); mob.stretch_to_fit_height(UH * (1 + 0.25 * ph))
            mob.move_to([0, UY, 0]); mob.set_stroke(opacity=0.9 * (1 - ph))
        halo.add_updater(hup)
        self.add(halo)
        # curseur qui vient cliquer sur l'adresse
        pts = [(0, 0), (0, -1.0), (0.26, -0.76), (0.45, -1.17), (0.62, -1.09), (0.43, -0.69), (0.78, -0.69)]
        tip_target = [1.4, UY - 0.1, 0]
        sx, sy = tip_target[0] + 2.4, tip_target[1] - 2.6
        cursor = m.Polygon(*[[sx + 0.9 * x, sy + 0.9 * y, 0] for x, y in pts], fill_color=WHITE_, fill_opacity=1,
                           stroke_color="#1E2933", stroke_width=4).set_z_index(40)
        self.until(C["cursor"]); self.add(cursor)
        self.go(cursor.animate.shift([-2.4, 2.6, 0]), rt=C["tap"] - C["cursor"] - 0.05, rate=OUT)
        ripple = m.Circle(radius=0.15, color=WHITE_, stroke_width=6).move_to(tip_target).set_z_index(39)
        self.until(C["tap"]); self.add(ripple)
        self.go(url.animate.scale(0.94), cursor.animate.scale(0.9, about_point=tip_target),
                ripple.animate.scale(7).set_stroke(opacity=0), rt=0.12, rate=OUT)
        self.go(url.animate.scale(1 / 0.94), cursor.animate.scale(1 / 0.9, about_point=tip_target), rt=0.22, rate=OUT_BACK)
        self.remove(ripple)
        self.go(cursor.animate.shift([0.8, -0.9, 0]).set_opacity(0), rt=0.4, rate=OUT)
        # slogan, affiché seulement (pas prononcé)
        bar = m.Rectangle(width=1.6, height=0.09, fill_color=ORANGE, fill_opacity=1, stroke_width=0)
        bar.move_to([0, -1.5, 0]).set_z_index(10)
        s1 = T("Tout projet", 64, WHITE_, width=4.6).move_to([0, -2.4, 0]).set_z_index(10)
        s2 = T("commence par un plan", 64, GOLD, width=6.8).move_to([0, -3.4, 0]).set_z_index(10)
        self.until(C["bar"]); self.pop(bar, 0.25, 0.3)
        self.until(C["s1"]); self.pop(s1, 0.33)
        self.until(C["s2"]); self.pop(s2, 0.35)
        self.until(Cc["total"])
