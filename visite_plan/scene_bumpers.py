import os
"""Hook / Estimation / CTA animés (9:16) pour les visites guidées WooPlans.
Rendu : manimgx render scene_bumpers.py HookScene|EstimScene|CtaScene -r 1080x1920 --fps 30
Variables : JOB = dossier du job (bump.json, plan.png, facade.png, logo_white.png)."""
import json, math, os
from pathlib import Path
import manimgx as m
import sys
sys.path.insert(0, str(Path(__file__).parent))
import slides

JOB = Path(os.environ["JOB"])
B = json.loads((JOB / "bump.json").read_text(encoding="utf-8"))
GREEN, ORANGE, GOLD, WHITE_ = "#0F5B59", "#F08A2E", "#E7C36C", "#FFFFFF"
FONT = "Noto Sans"
FRAME_W, FRAME_H = 8.0, 8.0 * 1920 / 1080
FACADE_H, BAND_H = FRAME_W * 0.5625, 0.95
PANEL_TOP = FRAME_H / 2 - FACADE_H - BAND_H
PANEL_BOTTOM = -FRAME_H / 2
PANEL_H = PANEL_TOP - PANEL_BOTTOM
PANEL_CY = (PANEL_TOP + PANEL_BOTTOM) / 2
FACADE_SLOT_Y = FRAME_H / 2 - FACADE_H / 2
BB_H = 190 / 135.0                      # bande basse (zone masquée par les interfaces des plateformes)
BB_Y = -FRAME_H / 2 + BB_H / 2
PLAN_W_PX, PLAN_H_PX = 1000, 1072
U = min(FRAME_W / PLAN_W_PX, PANEL_H / PLAN_H_PX)
OUT = getattr(m, "ease_out_cubic", m.smooth)
OUT_BACK = getattr(m, "ease_out_back", OUT)
INOUT = getattr(m, "ease_in_out_cubic", m.smooth)
m.config.background_color = GREEN
m.config.pixel_width, m.config.pixel_height = 1080, 1920


def T(txt, size=60, color=WHITE_, width=None):
    t = m.Text(txt, color=color, font=FONT, weight=m.BOLD, font_size=size)
    if width is not None:
        t.scale_to_fit_width(width)
    return t


def scr(p):
    return [(p[0] - PLAN_W_PX / 2) * U, -(p[1] - PLAN_H_PX / 2) * U + PANEL_CY, 0.0]


_WP = os.path.exists(os.path.join(os.environ.get("JOB", ""), "cta_wp.flag"))
_BTN = "VISITEZ LE SITE"

class Base(m.Scene):
    def setup_clock(self):
        self.t = 0.0

    def go(self, *anims, rt=0.4, rate=OUT):
        self.play(*anims, run_time=rt, rate_func=rate)
        self.t += rt

    def until(self, x):
        if x > self.t:
            self.wait(x - self.t)
            self.t = x

    def pop(self, mob, rt=0.35, s0=0.7):
        """apparition avec léger rebond."""
        mob.set_opacity(0)
        mob.scale(s0)
        self.add(mob)
        self.go(mob.animate.set_opacity(1).scale(1 / s0), rt=rt, rate=OUT_BACK)

    def grid(self, opacity=0.10, z=1):
        """lignes de plan (blueprint) qui défilent doucement en fond."""
        lines = []
        for i in range(-4, 5):
            lines.append(m.Line([i, -FRAME_H / 2 - 1, 0], [i, FRAME_H / 2 + 1, 0], color=WHITE_,
                                stroke_width=2, stroke_opacity=opacity))
        for j in range(-8, 9):
            ln = m.Line([-FRAME_W / 2 - 1, j, 0], [FRAME_W / 2 + 1, j, 0], color=WHITE_,
                        stroke_width=2, stroke_opacity=opacity)
            def up(mob, dt):
                mob.shift([0, 0.18 * dt, 0])
                if mob.get_center()[1] > 8.5:
                    mob.shift([0, -17, 0])
            ln.add_updater(up)
            lines.append(ln)
        for ln in lines:
            ln.set_z_index(z)
        return m.Group(*lines)

    def bg(self, color=GREEN):
        r = m.Rectangle(width=FRAME_W + 1, height=FRAME_H + 1, fill_color=color, fill_opacity=1,
                        stroke_width=0).set_z_index(0)
        self.add(r)
        return r

    def top_block(self, band_text):
        facade = m.ImageMobject(str(JOB / "facade.png"))
        facade.scale_to_fit_width(FRAME_W).move_to([0, FACADE_SLOT_Y, 0]).set_z_index(30)
        _SL = slides.make(m, JOB, FRAME_W, FACADE_SLOT_Y, FACADE_H, t_start=0.0, z0=24)
        if _SL is not None:
            facade = _SL
        band_y = FRAME_H / 2 - FACADE_H - BAND_H / 2
        band = m.Rectangle(width=FRAME_W + 0.2, height=BAND_H, fill_color=GREEN, fill_opacity=1,
                           stroke_width=0).move_to([0, band_y, 0]).set_z_index(31)
        bt = T(band_text, 44, WHITE_)
        if bt.width > FRAME_W - 0.7:
            bt.scale_to_fit_width(FRAME_W - 0.7)
        bt.move_to([0, band_y, 0]).set_z_index(32)
        div = m.Line([-FRAME_W / 2, FRAME_H / 2 - FACADE_H, 0], [FRAME_W / 2, FRAME_H / 2 - FACADE_H, 0],
                     color=ORANGE, stroke_width=6).set_z_index(33)
        return facade, band, bt, div


# =============================================================== HOOK
class HookScene(Base):
    def construct(self):
        self.setup_clock()
        H = B["hook"]; C = H["cues"]
        self.bg(GREEN)
        self.add(self.grid(0.10))
        facade = m.ImageMobject(str(JOB / "facade.png"))
        facade.scale_to_fit_width(FRAME_W).move_to([0, 2.7, 0]).set_z_index(30)
        facade.add_updater(lambda mob, dt: mob.scale(1 + 0.014 * dt))      # poussée lente
        # entrée de la façade : glisse depuis le haut
        facade.shift([0, 1.2, 0])
        self.add(facade)
        self.go(m.FadeIn(facade), facade.animate.shift([0, -1.2, 0]), rt=0.45, rate=OUT)
        tag = T(B.get("tag", "DUPLEX D5-016"), 40, GOLD, width=3.6).move_to([0, 6.35, 0]).set_z_index(10)
        self.until(C["tag"]); self.pop(tag, 0.3)
        w1 = T("COMBIEN", 72, WHITE_, width=4.9).move_to([0, -0.6, 0]).set_z_index(10)
        w2 = T("COÛTE", 72, ORANGE, width=5.2).move_to([0, -2.0, 0]).set_z_index(10)
        w3 = T(B.get("hook_w3", "CETTE MAISON ?"), 72, WHITE_, width=(5.4 if "hook_w3" in B else 6.9)).move_to([0, -3.4, 0]).set_z_index(10)
        chip_bg = m.RoundedRectangle(corner_radius=0.3, width=6.2, height=0.85, stroke_color=GOLD,
                                     stroke_width=4, fill_color=GREEN, fill_opacity=0.6).move_to([0, -5.2, 0]).set_z_index(10)
        chip_tx = T(B.get("chip", "5 CHAMBRES · 2 NIVEAUX"), 36, GOLD, width=5.6).move_to([0, -5.2, 0]).set_z_index(11)
        chip = m.Group(chip_bg, chip_tx)
        self.until(C["w1"]); self.pop(w1, 0.3)
        self.until(C["w2"]); self.pop(w2, 0.32, 0.5)
        self.until(C["w3"]); self.pop(w3, 0.32)
        self.until(C["chip"]); self.pop(chip, 0.35)
        self.until(C["pulse"])            # pulsation (synchro « boum »)
        self.go(w2.animate.scale(1.15), facade.animate.scale(1.02), rt=0.14, rate=OUT)
        self.go(w2.animate.scale(1 / 1.15), facade.animate.scale(1 / 1.02), rt=0.25, rate=OUT)

        # ---- transition : la façade monte à sa place, le plan glisse en fond (pas de fond blanc vide)
        self.until(C["trans"])
        facade.clear_updaters()
        panel = m.Rectangle(width=FRAME_W + 0.4, height=PANEL_H + 0.1, fill_color=WHITE_, fill_opacity=1,
                            stroke_width=0).set_z_index(20)
        plan = m.ImageMobject(str(JOB / "plan.png"))
        plan.scale_to_fit_height(PLAN_H_PX * U).set_z_index(21)
        ZS = 1.08                          # le plan arrive un peu zoomé puis se pose à l'échelle du corps
        plan.scale(ZS)
        panel.move_to([0, PANEL_CY - FRAME_H, 0]); plan.move_to([0, PANEL_CY - FRAME_H, 0])
        self.add(panel, plan)
        band_y = FRAME_H / 2 - FACADE_H - BAND_H / 2
        band = m.Rectangle(width=FRAME_W + 0.2, height=BAND_H, fill_color=GREEN, fill_opacity=1,
                           stroke_width=0).move_to([0, band_y, 0]).set_z_index(31)
        bt = T(B["band"], 44, WHITE_)
        if bt.width > FRAME_W - 0.7:
            bt.scale_to_fit_width(FRAME_W - 0.7)
        bt.move_to([0, band_y, 0]).set_z_index(32)
        div = m.Line([-FRAME_W / 2, FRAME_H / 2 - FACADE_H, 0], [FRAME_W / 2, FRAME_H / 2 - FACADE_H, 0],
                     color=ORANGE, stroke_width=6).set_z_index(33)
        band.set_opacity(0); bt.set_opacity(0); div.set_stroke(opacity=0)
        bb = m.ImageMobject(str(JOB / "band_bottom.png")); bb.scale_to_fit_width(FRAME_W)
        bb.move_to([0, BB_Y - 2.2, 0]).set_z_index(40)
        self.add(band, bt, div, bb)
        k = FRAME_W / facade.width
        self.go(facade.animate.scale(k).move_to([0, FACADE_SLOT_Y, 0]),
                panel.animate.move_to([0, PANEL_CY, 0]), plan.animate.move_to([0, PANEL_CY, 0]),
                bb.animate.move_to([0, BB_Y, 0]),
                m.FadeOut(w1), m.FadeOut(w2), m.FadeOut(w3), m.FadeOut(chip), m.FadeOut(tag),
                band.animate.set_opacity(1), bt.animate.set_opacity(1), div.animate.set_stroke(opacity=1),
                rt=0.75, rate=INOUT)
        # le point vert apparaît à l'entrée, comme au début du corps, pendant que le plan se pose
        sp = scr(B["start_pos"])
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
        self.go(plan.animate.scale(1 / ZS, about_point=[0, PANEL_CY, 0]), m.FadeIn(core), rt=0.9, rate=INOUT)
        self.until(H["total"])


# =============================================================== ESTIMATION
class EstimScene(Base):
    def construct(self):
        self.setup_clock()
        E = B["estim"]; v1, v2 = E["items"]
        self.bg(WHITE_)
        facade, band, bt, div = self.top_block(B["band"])
        plan = m.ImageMobject(str(JOB / "plan.png"))
        plan.scale_to_fit_height(PLAN_H_PX * U).move_to([0, PANEL_CY, 0]).set_z_index(2)
        bb = m.ImageMobject(str(JOB / "band_bottom.png")); bb.scale_to_fit_width(FRAME_W)
        bb.move_to([0, BB_Y, 0]).set_z_index(4)
        self.add(plan, facade, band, bt, div, bb)
        sheet = m.Rectangle(width=FRAME_W + 0.4, height=PANEL_H + 0.1, fill_color=GREEN, fill_opacity=1,
                            stroke_width=0).set_z_index(5)
        sheet.move_to([0, PANEL_CY - PANEL_H - 0.5, 0])
        self.add(sheet)
        self.go(sheet.animate.move_to([0, PANEL_CY, 0]), rt=0.7, rate=INOUT)
        grid = self.grid(0.07, z=6); self.add(grid)
        # grille limitée au panneau : on la recouvre en haut par la façade (z 30) ; OK visuellement
        lab = T("ESTIMATION · DEVIS DU PLAN", 40, GOLD, width=6.4).move_to([0, 1.05, 0]).set_z_index(10)
        self.pop(lab, 0.35)
        if "range" in B:
            self.range_block(E)
            return

        TARGET = B.get("target", 43864000)
        GROS, FIN = B.get("gros", 19738800), B.get("fin", 24125200)
        probe = m.Text(f"{TARGET:,}".replace(",", " "), color=WHITE_, font=FONT, weight=m.BOLD, font_size=100)
        fs = 100 * 6.9 / probe.width
        def fmt(n): return f"{int(n):,}".replace(",", " ")
        num = m.Text("0", color=WHITE_, font=FONT, weight=m.BOLD, font_size=fs).move_to([0, 0.15, 0]).set_z_index(10)
        clk = [0.0]
        t_start, t_end = E["cues"]["count0"], E["cues"]["count1"]
        def num_up(mob, dt):
            clk[0] += dt
            x = (clk[0] + 0.0)
            # clk démarre quand l'updater est ajouté ; on le cale sur la scène
            p = min(1.0, max(0.0, (x - 0.0) / (t_end - t_start)))
            p = 1 - (1 - p) ** 3
            new = m.Text(fmt(TARGET * p), color=WHITE_, font=FONT, weight=m.BOLD, font_size=fs)
            new.move_to([0, 0.15, 0]).set_z_index(10)
            mob.become(new)
        self.until(t_start)
        self.add(num)
        num.add_updater(num_up)
        fc = T("FCFA", 56, ORANGE, width=2.2).move_to([0, -0.9, 0]).set_z_index(10)
        self.pop(fc, 0.35)
        pill_bg = m.RoundedRectangle(corner_radius=0.32, width=3.6, height=0.8, fill_color=ORANGE, fill_opacity=1,
                                     stroke_width=0).move_to([0, -1.8, 0]).set_z_index(10)
        pill_tx = T("CLÉ EN MAIN", 36, WHITE_, width=3.0).move_to([0, -1.8, 0]).set_z_index(11)
        pill = m.Group(pill_bg, pill_tx)
        self.until(E["cues"]["pill"]); self.pop(pill, 0.35)
        # barre gros œuvre / finitions (révélée par un masque vert qui glisse)
        BW, BX0, BY = 7.0, -3.5, -2.6
        gw = BW * GROS / TARGET
        bar_g = m.Rectangle(width=gw, height=0.5, fill_color=ORANGE, fill_opacity=1, stroke_width=0)
        bar_g.move_to([BX0 + gw / 2, BY, 0]).set_z_index(10)
        bar_f = m.Rectangle(width=BW - gw, height=0.5, fill_color=GOLD, fill_opacity=1, stroke_width=0)
        bar_f.move_to([BX0 + gw + (BW - gw) / 2, BY, 0]).set_z_index(10)
        mask = m.Rectangle(width=BW + 0.2, height=0.7, fill_color=GREEN, fill_opacity=1, stroke_width=0)
        mask.move_to([BX0 + (BW + 0.2) / 2, BY, 0]).set_z_index(12)
        self.add(bar_g, bar_f, mask)
        self.until(E["cues"]["bar"])
        self.go(mask.animate.shift([BW + 0.4, 0, 0]), rt=1.1, rate=INOUT)
        l1 = T("GROS ŒUVRE", 30, ORANGE, width=2.6).move_to([BX0 + gw / 2, BY - 0.5, 0]).set_z_index(10)
        l1b = T(f"{GROS:,}".replace(",", " ") + " FCFA", 28, WHITE_, width=3.0).move_to([BX0 + gw / 2, BY - 0.92, 0]).set_z_index(10)
        l2 = T("FINITIONS", 30, GOLD, width=2.0).move_to([BX0 + gw + (BW - gw) / 2, BY - 0.5, 0]).set_z_index(10)
        l2b = T(f"{FIN:,}".replace(",", " ") + " FCFA", 28, WHITE_, width=3.0).move_to([BX0 + gw + (BW - gw) / 2, BY - 0.92, 0]).set_z_index(10)
        for l in (l1, l1b, l2, l2b):
            l.set_opacity(0); self.add(l)
        self.go(*[l.animate.set_opacity(1) for l in (l1, l1b, l2, l2b)], rt=0.5)
        # emphase à l'arrivée du total
        self.until(E["cues"]["impact"])
        self.go(num.animate.scale(1.06), rt=0.18); self.go(num.animate.scale(1 / 1.06), rt=0.2)
        # mention de prudence, sur la 2e phrase de voix
        n1 = T("Le coût réel dépend du terrain,", 34, WHITE_, width=6.6)
        n2 = T("des techniciens et des matériaux", 34, WHITE_, width=6.6)
        n1.move_to([0, -4.25, 0]).set_z_index(10); n2.move_to([0, -4.7, 0]).set_z_index(10)
        note = m.Group(n1, n2)
        self.until(v2["start"]); self.pop(note, 0.4, 0.9)
        self.until(E["total"])


    def range_block(self, E):
        """devis : intervalle de prix (source : site WooPlans, budget min / max)."""
        C = E["cues"]; v2 = E["items"][1]
        lo, hi = B["range"]
        def fmt(n): return f"{int(n):,}".replace(",", " ")
        probe = m.Text(fmt(hi), color=WHITE_, font=FONT, weight=m.BOLD, font_size=100)
        fs = 100 * 5.3 / probe.width
        def counter(target, y, t0, t1):
            clk = [0.0]
            num = m.Text("0", color=WHITE_, font=FONT, weight=m.BOLD, font_size=fs).move_to([0, y, 0]).set_z_index(10)
            def up(mob, dt):
                clk[0] += dt
                p = min(1.0, max(0.0, clk[0] / max(0.3, t1 - t0)))
                p = 1 - (1 - p) ** 3
                new = m.Text(fmt(target * p), color=WHITE_, font=FONT, weight=m.BOLD, font_size=fs)
                new.move_to([0, y, 0]).set_z_index(10)
                mob.become(new)
            return num, up
        s1 = T("ENTRE", 42, GOLD, width=1.8).move_to([0, 0.45, 0]).set_z_index(10)
        num1, up1 = counter(lo, -0.4, C["count0"], C["count1"])
        s2 = T("ET", 42, GOLD, width=0.8).move_to([0, -1.25, 0]).set_z_index(10)
        num2, up2 = counter(hi, -2.05, C["count2"], C["count3"])
        fc = T("FCFA", 52, ORANGE, width=2.0).move_to([0, -2.95, 0]).set_z_index(10)
        pill_bg = m.RoundedRectangle(corner_radius=0.32, width=3.6, height=0.8, fill_color=ORANGE, fill_opacity=1,
                                     stroke_width=0).move_to([0, -3.8, 0]).set_z_index(10)
        pill_tx = T("CLÉ EN MAIN", 36, WHITE_, width=3.0).move_to([0, -3.8, 0]).set_z_index(11)
        pill = m.Group(pill_bg, pill_tx)
        self.until(C["count0"] - 0.3); self.pop(s1, 0.3)
        self.until(C["count0"]); self.add(num1); num1.add_updater(up1)
        self.until(C["count2"] - 0.25); self.pop(s2, 0.25)
        self.until(C["count2"]); self.add(num2); num2.add_updater(up2)
        self.until(C["count3"]); self.pop(fc, 0.35)
        self.until(C["pill"]); self.pop(pill, 0.35)
        if "split" in B:                      # répartition gros œuvre / finitions (source : lots du devis du site)
            sp = B["split"]; BWd, BX0d, BYd = 7.0, -3.5, -3.8
            gw = BWd * sp[0] / 100
            self.until(C["split"])
            self.go(m.FadeOut(pill), rt=0.25)
            bg_ = m.Rectangle(width=gw, height=0.7, fill_color=ORANGE, fill_opacity=1, stroke_width=0).move_to([BX0d + gw / 2, BYd, 0]).set_z_index(10)
            bf_ = m.Rectangle(width=BWd - gw, height=0.7, fill_color=GOLD, fill_opacity=1, stroke_width=0).move_to([BX0d + gw + (BWd - gw) / 2, BYd, 0]).set_z_index(10)
            tg_ = T(f"GROS ŒUVRE {sp[0]} %", 28, WHITE_, width=gw - 0.3).move_to([BX0d + gw / 2, BYd, 0]).set_z_index(11)
            tf_ = T(f"FINITIONS {sp[1]} %", 28, WHITE_, width=BWd - gw - 0.3).move_to([BX0d + gw + (BWd - gw) / 2, BYd, 0]).set_z_index(11)
            mk_ = m.Rectangle(width=BWd + 0.2, height=0.9, fill_color=GREEN, fill_opacity=1, stroke_width=0).move_to([BX0d + (BWd + 0.2) / 2, BYd, 0]).set_z_index(12)
            self.add(bg_, bf_, tg_, tf_, mk_)
            self.go(mk_.animate.shift([BWd + 0.4, 0, 0]), rt=0.9, rate=INOUT)
        n1 = T("Le coût réel dépend du terrain,", 34, WHITE_, width=6.6)
        n2 = T("des techniciens et des matériaux", 34, WHITE_, width=6.6)
        n1.move_to([0, -4.7, 0]).set_z_index(10); n2.move_to([0, -5.12, 0]).set_z_index(10)
        note = m.Group(n1, n2)
        self.until(v2["start"]); self.pop(note, 0.4, 0.9)
        self.until(E["total"])


# =============================================================== CTA
class CtaScene(Base):
    def construct(self):
        self.setup_clock()
        Cc = B["cta"]; C = Cc["cues"]
        self.bg(GREEN)
        self.add(self.grid(0.10))
        LY = 4.7
        logo = m.ImageMobject(str(JOB / "logo_white.png"))
        logo.scale_to_fit_width(4.6).move_to([0, LY, 0]).set_z_index(10)
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
        # bouton : uniquement « ABONNEZ-VOUS »
        BY, BW_, BH_ = 1.4, 7.0, 1.9
        btn = m.RoundedRectangle(corner_radius=0.55, width=BW_, height=BH_, fill_color=ORANGE, fill_opacity=1,
                                 stroke_width=0).move_to([0, BY, 0]).set_z_index(10)
        t1 = T(_BTN if _WP else "ABONNEZ-VOUS", 64, WHITE_, width=5.9).move_to([0, BY, 0]).set_z_index(11)
        group = m.Group(btn, t1)
        self.until(C["button"]); self.pop(group, 0.3, 0.5)
        halo = m.RoundedRectangle(corner_radius=0.55, width=BW_, height=BH_, color=ORANGE, stroke_width=5,
                                  fill_opacity=0).move_to([0, BY, 0]).set_z_index(9)
        hc = [0.0]
        def hup(mob, dt):
            hc[0] += dt
            ph = (hc[0] % 1.2) / 1.2
            mob.stretch_to_fit_width(BW_ * (1 + 0.12 * ph)); mob.stretch_to_fit_height(BH_ * (1 + 0.25 * ph))
            mob.move_to([0, BY, 0]); mob.set_stroke(opacity=0.9 * (1 - ph))
        halo.add_updater(hup)
        self.add(halo)
        # curseur qui vient appuyer sur le bouton
        pts = [(0, 0), (0, -1.0), (0.26, -0.76), (0.45, -1.17), (0.62, -1.09), (0.43, -0.69), (0.78, -0.69)]
        tip_target = [1.2, BY - 0.15, 0]
        sx, sy = tip_target[0] + 2.4, tip_target[1] - 2.6          # départ : en bas à droite
        cursor = m.Polygon(*[[sx + 0.9 * x, sy + 0.9 * y, 0] for x, y in pts], fill_color=WHITE_, fill_opacity=1,
                           stroke_color="#1E2933", stroke_width=4).set_z_index(40)
        self.until(C["cursor"]); self.add(cursor)
        self.go(cursor.animate.shift([-2.4, 2.6, 0]), rt=C["tap"] - C["cursor"] - 0.05, rate=OUT)
        ripple = m.Circle(radius=0.15, color=WHITE_, stroke_width=6).move_to(tip_target).set_z_index(39)
        self.until(C["tap"]); self.add(ripple)
        self.go(group.animate.scale(0.93), cursor.animate.scale(0.9, about_point=tip_target),
                ripple.animate.scale(6).set_stroke(opacity=0), rt=0.12, rate=OUT)
        self.go(group.animate.scale(1 / 0.93), cursor.animate.scale(1 / 0.9, about_point=tip_target), rt=0.22, rate=OUT_BACK)
        self.remove(ripple)
        self.go(cursor.animate.shift([0.8, -0.9, 0]).set_opacity(0), rt=0.4, rate=OUT)
        # slogan, affiché seulement (pas prononcé)
        bar = m.Rectangle(width=1.6, height=0.09, fill_color=ORANGE, fill_opacity=1, stroke_width=0)
        bar.move_to([0, -0.3, 0]).set_z_index(10)
        s1 = T("Voir plus de modèles" if _WP else "Tout projet", 64, WHITE_, width=(6.8 if _WP else 4.6)).move_to([0, -1.25, 0]).set_z_index(10)
        s2 = T("sur wooplans.com" if _WP else "commence par un plan", 64, GOLD, width=6.8).move_to([0, -2.3, 0]).set_z_index(10)
        self.until(C["bar"]); self.pop(bar, 0.25, 0.3)
        self.until(C["s1"]); self.pop(s1, 0.33)
        self.until(C["s2"]); self.pop(s2, 0.35)
        # adresse du site, bien visible (dans la zone sûre)
        ub = m.RoundedRectangle(corner_radius=0.5, width=6.6, height=1.1, stroke_color=GOLD, stroke_width=5,
                                fill_color="#0B4745", fill_opacity=1).move_to([0, -3.7, 0]).set_z_index(10)
        ut = T("wooplans.com", 70, WHITE_, width=5.4).move_to([0, -3.7, 0]).set_z_index(11)
        url = m.Group(ub, ut)
        self.until(C["url"]); self.pop(url, 0.35, 0.8)
        self.until(Cc["total"])
