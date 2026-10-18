"""VSL3 « Du rêve au vrai projet en 3 étapes » en motion design.

Aperçu muet : manimgx render vsl3.py VSL3 -r 1080x1920 --fps 30
"""

import manimgx as m

from motion import (ART_Y, CAP_Y, CREAM, GOLD, GREEN, GREEN_DARK, GREEN_LIGHT, ORANGE, VOICE, WHITE, T, background,
                    blueprint, bubble, caption, card, check, chip, clear, counter, cta_beat, fan, house, icon_cube,
                    icon_doc, icon_plan, mark, offer_beat, person, phone, rise, script, slam, step_badge, tile, wipe)

S = script("vsl3_projet")
B = S["beats"]


class VSL3(m.Scene):
    voice = VOICE

    def construct(self) -> None:
        background(self)

        # 1. Le rêve, puis le chemin en trois étapes
        v = B[0]["voix"]
        dreamer = person(ORANGE, 1.4).move_to([-2.2, ART_Y - 2.4, 0])
        puffs = m.VGroup(*[m.Circle(radius=r, fill_color=CREAM, fill_opacity=0.95, stroke_width=0).move_to(p) for r, p in (
            (0.14, [-1.6, ART_Y - 1.1, 0]), (0.22, [-1.2, ART_Y - 0.6, 0]))])
        cloud = m.VGroup(*[m.Circle(radius=r, fill_color=CREAM, fill_opacity=0.95, stroke_width=0).move_to([x, ART_Y + 2.6 + y, 0])
                           for r, x, y in ((1.2, -0.8, 0), (1.0, 0.6, 0.3), (0.9, 1.5, -0.3), (0.9, -1.9, -0.3), (1.0, 0.2, -0.7))])
        dream = house(2.2).move_to([-0.1, ART_Y + 2.7, 0])
        qs = T("?", 140, GOLD).move_to([2.4, ART_Y - 2.2, 0])
        road = m.CubicBezier([-2.8, CAP_Y + 0.9, 0], [4.0, CAP_Y + 1.8, 0], [-4.0, ART_Y - 2.0, 0], [2.4, ART_Y + 0.4, 0],
                             stroke_color=GOLD, stroke_width=12)
        stops = [road.point_from_proportion(a) for a in (0.12, 0.5, 0.88)]
        discs = m.VGroup(*[m.VGroup(m.Circle(radius=0.48, fill_color=ORANGE, fill_opacity=1, stroke_color=WHITE, stroke_width=4),
                                    T(str(i + 1), 58)).move_to(p) for i, p in enumerate(stops)])
        for d in discs:
            d[1].move_to(d[0])
        cap = T("3 étapes", 96, ORANGE).move_to([0, CAP_Y - 1.4, 0])
        self.say(mark(v, "Tu rêves de ta maison", "par où commencer", "Voici le chemin", "en trois étapes"),
                 m.AnimationGroup(m.FadeIn(dreamer, shift=m.UP), m.LaggedStart(*[m.GrowFromCenter(p) for p in puffs], lag_ratio=0.4),
                                  m.LaggedStart(*[m.GrowFromCenter(c, rate_func=m.ease_out_back) for c in cloud], lag_ratio=0.15),
                                  m.DrawBorderThenFill(dream, run_time=1.2)),
                 slam(qs),
                 m.AnimationGroup(m.FadeOut(qs), m.FadeOut(dreamer), m.FadeOut(puffs), m.Create(road, run_time=1.2)),
                 m.AnimationGroup(m.LaggedStart(*[m.GrowFromCenter(d, rate_func=m.ease_out_back) for d in discs], lag_ratio=0.3),
                                  slam(cap)))
        clear(self, cloud, dream, road, discs, cap)

        # 2. Étape 1 : le catalogue, 50+ modèles, rendus, distributions, devis
        v = B[1]["voix"]
        badge = step_badge(1)
        cards, _ = fan()
        num, upd = counter(50, "+", 130)
        num.move_to([0, CAP_Y + 1.0, 0])
        sub = T("villas et duplex", 54).next_to(num, m.DOWN, buff=0.25)
        icons = m.VGroup(tile(icon_cube(), "Rendus 3D", 2.4, 2.0), tile(icon_plan(), "Plans", 2.4, 2.0),
                         tile(icon_doc(), "Devis", 2.4, 2.0)).arrange(m.RIGHT, buff=0.2).move_to([0, CAP_Y - 2.0, 0])
        self.say(mark(v, "Étape un", "Catalogue Premium", "Plus de cinquante villas et duplex", "rendus 3D",
                      "distributions cotées", "devis estimatifs"),
                 m.FadeIn(badge, shift=3 * m.RIGHT, rate_func=m.ease_out_back),
                 m.LaggedStart(*[m.FadeIn(c, shift=2 * m.UP, scale=0.5, rate_func=m.ease_out_back) for c in cards],
                               lag_ratio=0.12, run_time=1.3),
                 m.AnimationGroup(m.UpdateFromAlphaFunc(num, upd, run_time=1.3, rate_func=m.ease_out_cubic), rise(sub)),
                 *[m.GrowFromCenter(t, rate_func=m.ease_out_back) for t in icons])
        clear(self, badge, cards, num, sub, icons)

        # 3. En famille : on compare, on choisit le modèle qui nous ressemble
        v = B[2]["voix"]
        row = m.VGroup(card(0.95), card(0.95, GOLD), card(0.95, GREEN_LIGHT)).arrange(m.RIGHT, buff=0.3)
        row.move_to([0, ART_Y + 2.0, 0])
        fam = m.VGroup(person(ORANGE, 1.25), person(GOLD, 0.85), person(GREEN_LIGHT, 1.15)).arrange(m.RIGHT, buff=0.25)
        fam.move_to([0, ART_Y - 1.4, 0])
        glow = m.SurroundingRectangle(row[1], color=GOLD, buff=0.12, stroke_width=8)
        heart = m.VGroup(m.Circle(radius=0.3), m.Circle(radius=0.3).shift(0.42 * m.RIGHT),
                         m.Polygon([-0.27, -0.12, 0], [0.69, -0.12, 0], [0.21, -0.75, 0]))
        heart.set_fill(ORANGE, 1).set_stroke(width=0).move_to(row[1].get_top() + 0.6 * m.UP)
        cap = caption(B[2]["ecran"], accent="ensemble", y=CAP_Y - 0.3)
        self.say(mark(v, "ta famille", "vous comparez ensemble", "le modèle qui vous ressemble"),
                 m.AnimationGroup(m.LaggedStart(*[m.FadeIn(p, shift=m.UP, rate_func=m.ease_out_back) for p in fam], lag_ratio=0.25),
                                  m.LaggedStart(*[m.FadeIn(c, shift=m.DOWN) for c in row], lag_ratio=0.2)),
                 m.AnimationGroup(m.LaggedStart(*[m.Indicate(c, color=GOLD, scale_factor=1.08) for c in row], lag_ratio=0.35),
                                  rise(cap[0])),
                 m.AnimationGroup(m.Create(glow), m.GrowFromCenter(heart, rate_func=m.ease_out_back), rise(cap[1]),
                                  row[0].animate.set_opacity(0.35), row[2].animate.set_opacity(0.35)))
        clear(self, row, fam, glow, heart, cap)

        # 4. Étape 2 : le modèle choisi part sur WhatsApp, avec les modifications voulues
        v = B[3]["voix"]
        badge = step_badge(2)
        ph = phone().move_to([0, ART_Y - 0.4, 0])
        screen = ph[1]
        for x in ph[2:]:
            x.set_opacity(0)
        wa = m.VGroup(m.Circle(radius=0.55, fill_color="#25D366", fill_opacity=1, stroke_color=WHITE, stroke_width=5),
                      T("✆", 54)).move_to(ph.get_corner(m.UR) + [-0.1, -0.1, 0])
        wa[1].move_to(wa[0])
        sent = m.VGroup(m.RoundedRectangle(corner_radius=0.2, width=2.2, height=1.9, fill_color="#DCF8C6", fill_opacity=1,
                                           stroke_width=0), card(0.62))
        sent[1].move_to(sent[0])
        sent.move_to(screen.get_center() + [0.25, 1.4, 0])
        ask = bubble(2.4, 0.9, fill="#DCF8C6", right=True).move_to(screen.get_center() + [0.2, -0.2, 0])
        ok = m.VGroup(bubble(1.8, 0.7), check(0.45)).move_to(screen.get_center() + [-0.4, -1.5, 0])
        ok[1].move_to(ok[0].get_right() + 0.45 * m.LEFT)
        cap = T("Écris-nous sur WhatsApp", 64, accent="WhatsApp").move_to([0, CAP_Y - 1.6, 0])
        self.say(mark(v, "Étape deux", "WhatsApp", "le modèle choisi", "ce que tu veux changer"),
                 m.AnimationGroup(m.FadeIn(badge, shift=3 * m.RIGHT, rate_func=m.ease_out_back), m.FadeIn(ph[:2], shift=2 * m.UP)),
                 m.AnimationGroup(m.SpinInFromNothing(wa, rate_func=m.ease_out_back), rise(cap)),
                 m.FadeIn(sent, shift=m.UP, scale=0.6, rate_func=m.ease_out_back),
                 m.Succession(m.GrowFromCenter(ask, rate_func=m.ease_out_back), m.GrowFromCenter(ok, rate_func=m.ease_out_back)))
        clear(self, badge, ph, wa, sent, ask, ok, cap)

        # 5. Étape 3 : les plans complets se déroulent, adaptés au terrain, à prix fixe
        v = B[4]["voix"]
        badge = step_badge(3)
        bp = blueprint().move_to([0, ART_Y + 0.2, 0])
        lot = m.DashedVMobject(m.Rectangle(width=6.6, height=5.0, color=GOLD, stroke_width=5), num_dashes=40).move_to(bp)
        terrain = T("Ton terrain", 36, GOLD).next_to(lot, m.DOWN, buff=0.15).align_to(lot, m.RIGHT)
        villa = chip("Villa : 149 000 FCFA", size=48).move_to([0, CAP_Y - 0.9, 0])
        duplex = chip("Duplex : 249 000 FCFA", size=48).move_to([0, CAP_Y - 2.1, 0])
        head = T("Prix fixe", 64, ORANGE).move_to([0, CAP_Y + 0.2, 0])
        self.say(mark(v, "Étape trois", "les plans complets", "adaptés à ton terrain", "Prix fixe", "149 000 FCFA pour une villa",
                      "249 000 FCFA pour un duplex"),
                 m.FadeIn(badge, shift=3 * m.RIGHT, rate_func=m.ease_out_back),
                 m.AnimationGroup(m.GrowFromEdge(bp[0], m.LEFT, run_time=0.8),
                                  m.Succession(m.Wait(0.4), m.Create(bp[1], run_time=1.0), m.Create(bp[2], run_time=0.5))),
                 m.AnimationGroup(m.Create(lot, run_time=0.9), rise(terrain)),
                 slam(head), slam(villa), slam(duplex))
        clear(self, badge, bp, lot, terrain, villa, duplex, head)

        # 6. Le prix du catalogue est déduit : deux soustractions qui se posent
        v = B[5]["voix"]
        top = T("Catalogue déduit", 80, ORANGE).move_to([0, ART_Y + 3.4, 0])

        def column(label, full, rest, x):
            lab = T(label, 52, GOLD)
            a = T(full, 60)
            b = T("− 39 000", 60, ORANGE)
            ln = m.Line([-1.6, 0, 0], [1.6, 0, 0], color=WHITE, stroke_width=5)
            c = T(rest, 66, GOLD)
            g = m.VGroup(lab, a, b, ln, c).arrange(m.DOWN, buff=0.35).move_to([x, ART_Y - 0.3, 0])
            return g

        cv = column("Villa", "149 000", "110 000", -1.95)
        cd = column("Duplex", "249 000", "210 000", 1.95)
        unit = T("FCFA", 56).move_to([0, ART_Y - 3.2, 0])
        cap = caption(["Tu paies seulement la différence"], y=CAP_Y - 0.9, first=56)
        self.say(mark(v, "le prix du catalogue est déduit", "la différence", "110 000 FCFA pour une villa", "210 000 FCFA pour un duplex"),
                 m.AnimationGroup(slam(top), m.LaggedStart(*[rise(x) for x in (cv[0], cv[1], cd[0], cd[1])], lag_ratio=0.15),
                                  m.LaggedStart(m.FadeIn(cv[2], shift=m.LEFT), m.FadeIn(cd[2], shift=m.LEFT), lag_ratio=0.4)),
                 m.AnimationGroup(m.Create(cv[3]), m.Create(cd[3]), rise(cap)),
                 m.AnimationGroup(slam(cv[4]), m.Flash(cv[4], color=GOLD, flash_radius=1.3)),
                 m.AnimationGroup(slam(cd[4]), m.Flash(cd[4], color=GOLD, flash_radius=1.3), rise(unit)))
        clear(self, top, cv, cd, unit, cap)

        # 7. L'offre, 8. l'appel à l'action
        wipe(self)
        clear(self, *offer_beat(self, B[6]))
        cta_beat(self, B[7], "le premier pas")
