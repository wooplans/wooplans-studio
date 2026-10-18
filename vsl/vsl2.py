"""VSL2 « Combien coûte vraiment ta maison ? » en motion design.

Aperçu muet : manimgx render vsl2.py VSL2 -r 1080x1920 --fps 30
"""

import manimgx as m

from motion import (ART_Y, CAP_Y, CREAM, GOLD, GREEN, GREEN_DARK, GREEN_LIGHT, GREY, ORANGE, RED, VOICE, T,
                    background, bricks, bubble, caption, card, check, chip, clear, coin, counter, cross, cta_beat, fan,
                    helmet_person, house, icon_doc, icon_plan, mark, offer_beat, person, pin, price_tag, rise, script,
                    slam, stop_sign, wipe)

S = script("vsl2_budget")
B = S["beats"]


class VSL2(m.Scene):
    voice = VOICE

    def construct(self) -> None:
        background(self)

        # 1. Accroche : qui fixe le budget ? Le sac d'argent glisse vers l'entrepreneur
        v = B[0]["voix"]
        hs = house(2.6).move_to([0, ART_Y + 2.6, 0])
        tag = price_tag("? FCFA").scale(0.6).next_to(hs, m.RIGHT, buff=-0.4).shift(0.9 * m.UP).rotate(-0.2)
        me = person(ORANGE, 1.3).move_to([-2.4, ART_Y - 1.0, 0])
        me_l = T("Toi", 44).next_to(me, m.DOWN, buff=0.2)
        pro = helmet_person(GREEN_LIGHT, 1.3).move_to([2.1, ART_Y - 1.0, 0])
        pro_l = T("Entrepreneur", 36).next_to(pro, m.DOWN, buff=0.2)
        bag = m.VGroup(*[coin(0.36).shift([0.42 * (i % 3) - 0.42, 0.3 * (i // 3), 0]) for i in range(6)]).move_to([0, ART_Y - 1.0, 0])
        cap = caption(B[0]["ecran"], accent="budget", y=CAP_Y - 0.2)
        self.say(mark(v, "combien coûte ta maison", "l'entrepreneur", "fixer ton budget", "Pas toi"),
                 m.AnimationGroup(m.DrawBorderThenFill(hs, run_time=1.0),
                                  m.SpinInFromNothing(tag, angle=0.5, rate_func=m.ease_out_back)),
                 m.AnimationGroup(m.FadeIn(me, shift=2 * m.RIGHT), rise(me_l), m.FadeIn(pro, shift=2 * m.LEFT), rise(pro_l),
                                  slam(bag), rise(cap[0])),
                 bag.animate(rate_func=m.ease_in_out_back, run_time=0.9).move_to([0.9, ART_Y - 1.0, 0]),
                 m.AnimationGroup(rise(cap[1]), m.Wiggle(me)))
        clear(self, hs, tag, me, me_l, pro, pro_l, bag, cap)

        # 2. Aucun repère : des points d'interrogation, le plan et le devis barrés
        v = B[1]["voix"]
        guy = person(ORANGE, 1.6).move_to([0, ART_Y + 2.2, 0])
        qs = m.VGroup(*[T("?", 80, GOLD).move_to(guy.get_center() + p)
                        for p in ([-1.6, 1.0, 0], [1.6, 1.2, 0], [-1.9, -0.6, 0], [1.9, -0.4, 0])])
        ip = icon_plan().scale(0.9).move_to([-1.7, ART_Y - 1.2, 0])
        idoc = icon_doc().move_to([1.7, ART_Y - 1.2, 0])
        x1, x2 = cross(1.6).move_to(ip), cross(1.6).move_to(idoc)
        cap = caption(B[1]["ecran"], accent="Aucun repère", y=CAP_Y - 0.6)
        self.say(mark(v, "sans aucun repère", "Pas de plan comparé", "pas de devis", "rien"),
                 m.AnimationGroup(m.FadeIn(guy, shift=m.UP), m.LaggedStart(*[slam(q, 0.35) for q in qs], lag_ratio=0.2),
                                  slam(cap[0])),
                 m.AnimationGroup(m.FadeIn(ip, scale=0.5), m.Create(x1, run_time=0.5, lag_ratio=0.5)),
                 m.AnimationGroup(m.FadeIn(idoc, scale=0.5), m.Create(x2, run_time=0.5, lag_ratio=0.5)),
                 m.AnimationGroup(rise(cap[1]), m.Wiggle(guy)))
        clear(self, guy, qs, ip, idoc, x1, x2, cap)

        # 3. Résultat : le budget gonfle, le chantier s'arrête, le prix reste un mystère
        v = B[2]["voix"]
        base_y = ART_Y - 0.8
        limit = m.DashedLine([-3.2, base_y + 2.2, 0], [3.2, base_y + 2.2, 0], color=GOLD, stroke_width=5)
        limit_l = T("Budget prévu", 34, GOLD).next_to(limit, m.UP, buff=0.1).align_to(limit, m.LEFT)
        heights = [1.2, 1.9, 2.8, 3.6, 4.4]
        bars = m.VGroup(*[m.Rectangle(width=0.8, height=h, fill_color=(ORANGE if h < 2.2 else RED), fill_opacity=1,
                                      stroke_width=0).move_to([-2.4 + i * 1.2, base_y + h / 2, 0]) for i, h in enumerate(heights)])
        chart = m.VGroup(limit, limit_l)
        half = m.VGroup(m.Rectangle(width=3.0, height=1.0, fill_color=CREAM, fill_opacity=1, stroke_color=m.WHITE, stroke_width=4),
                        m.DashedVMobject(m.Rectangle(width=3.0, height=1.1, color=m.WHITE, stroke_width=4), num_dashes=20))
        half[1].next_to(half[0], m.UP, buff=0)
        half.move_to([-0.9, ART_Y + 0.6, 0])
        stop = stop_sign(0.9).move_to([2.1, ART_Y + 1.4, 0])
        tag = price_tag("? FCFA").scale(0.75).move_to([0, ART_Y + 0.8, 0]).rotate(0.15)
        labels = [chip(t, size=36) for t in B[2]["ecran"]]
        for i, lab in enumerate(labels):
            lab.move_to([0, CAP_Y + 0.1 - i * 0.95, 0])
        self.say(mark(v, "le budget gonfle", "s'arrêtent à mi-chemin", "prix annoncé était juste"),
                 m.AnimationGroup(m.Create(limit), rise(limit_l),
                                  m.LaggedStart(*[m.GrowFromEdge(b, m.DOWN, rate_func=m.ease_out_back) for b in bars],
                                                lag_ratio=0.2, run_time=1.4), rise(labels[0])),
                 m.AnimationGroup(m.FadeOut(chart, shift=m.UP), m.FadeOut(bars, shift=m.UP),
                                  m.GrowFromEdge(half, m.DOWN), m.SpinInFromNothing(stop, rate_func=m.ease_out_back), rise(labels[1])),
                 m.AnimationGroup(m.FadeOut(half, shift=m.UP), m.FadeOut(stop, shift=m.UP),
                                  m.GrowFromCenter(tag, rate_func=m.ease_out_back), rise(labels[2])))
        self.play(m.Wiggle(tag), run_time=0.6)
        clear(self, tag, *labels)

        # 4. La solution : 50+ modèles et, pour chacun, un devis détaillé par lot
        wipe(self)
        v = B[3]["voix"]
        cards, _ = fan()
        num, upd = counter(50, "+", 150)
        num.move_to([0, CAP_Y + 0.1, 0])
        sub = T("modèles", 60).next_to(num, m.DOWN, buff=0.3)
        doc = m.RoundedRectangle(corner_radius=0.2, width=5.0, height=6.0, fill_color=m.WHITE, fill_opacity=1,
                                 stroke_color=GOLD, stroke_width=6).move_to([0, ART_Y + 0.6, 0])
        title = T("Devis estimatif", 52, GREEN, max_w=4.3).move_to(doc.get_top() + 0.65 * m.DOWN)
        rows = m.VGroup()
        for i, w in enumerate([2.4, 1.6, 2.9, 1.2, 2.0]):
            y = doc.get_top()[1] - 1.6 - i * 0.85
            lab = T(f"Lot {i + 1}", 34, GREEN).move_to([-1.6, y, 0])
            bar = m.Rectangle(width=w, height=0.32, fill_color=(ORANGE if i % 2 else GOLD), fill_opacity=1, stroke_width=0)
            bar.move_to([-0.8 + w / 2, y, 0])
            rows.add(m.VGroup(lab, bar))
        self.say(mark(v, "Catalogue Premium WooPlans", "plus de cinquante modèles", "un devis estimatif détaillé par lot"),
                 m.LaggedStart(*[m.FadeIn(c, shift=2 * m.UP, scale=0.5, rate_func=m.ease_out_back) for c in cards],
                               lag_ratio=0.12, run_time=1.3),
                 m.AnimationGroup(m.UpdateFromAlphaFunc(num, upd, run_time=1.3, rate_func=m.ease_out_cubic), rise(sub)),
                 m.AnimationGroup(m.FadeOut(cards, shift=m.DOWN), m.FadeIn(doc, shift=3 * m.UP, rate_func=m.ease_out_back),
                                  rise(title), m.LaggedStart(*[m.GrowFromEdge(r, m.LEFT) for r in rows], lag_ratio=0.25, run_time=1.4)))
        clear(self, num, sub, doc, title, rows)

        # 5. Comment sont faites les estimations : m² actualisé, ordre de grandeur, ville et matériaux
        v = B[4]["voix"]
        sq = m.Square(side_length=2.6, fill_color=GREEN_DARK, fill_opacity=1, stroke_color=GOLD, stroke_width=6)
        sq.move_to([0, ART_Y + 2.4, 0])
        m2 = T("m²", 110, GOLD).move_to(sq)
        loop = m.Arc(radius=1.75, start_angle=0.3, angle=5.2, color=ORANGE, stroke_width=10).move_to(sq).add_tip()
        rng_bar = m.RoundedRectangle(corner_radius=0.2, width=6.0, height=0.4, fill_color=GREY, fill_opacity=1, stroke_width=0)
        rng_bar.move_to([0, ART_Y - 0.3, 0])
        zone = m.RoundedRectangle(corner_radius=0.2, width=2.2, height=0.4, fill_color=ORANGE, fill_opacity=1, stroke_width=0)
        zone.move_to(rng_bar.get_center() + 0.6 * m.RIGHT)
        mk = m.Triangle(fill_color=GOLD, fill_opacity=1, stroke_width=0).scale(0.25).rotate(m.PI)
        mk.move_to(rng_bar.get_left() + 0.4 * m.UP)
        pn = pin().move_to([-1.6, ART_Y - 2.2, 0])
        br = bricks().move_to([1.6, ART_Y - 2.3, 0])
        cap = caption(B[4]["ecran"], accent="actualisés", y=CAP_Y - 0.6, first=72, rest=60)
        self.say(mark(v, "ratios professionnels", "prix au mètre carré actualisés", "ordre de grandeur", "ta ville", "tes matériaux"),
                 m.AnimationGroup(m.DrawBorderThenFill(sq), slam(m2), rise(cap[0])),
                 m.AnimationGroup(m.Rotate(loop, -2 * m.PI, about_point=sq.get_center(), run_time=1.2), m.FadeIn(loop),
                                  rise(cap[1])),
                 m.AnimationGroup(m.FadeIn(rng_bar), m.GrowFromCenter(zone),
                                  m.Succession(m.FadeIn(mk), mk.animate(rate_func=m.ease_in_out_back, run_time=1.0)
                                               .move_to(zone.get_center() + 0.4 * m.UP))),
                 m.FadeIn(pn, shift=1.5 * m.DOWN, rate_func=m.ease_out_bounce),
                 m.LaggedStart(*[m.FadeIn(b, shift=m.DOWN) for b in br], lag_ratio=0.15, run_time=0.8))
        clear(self, sq, m2, loop, rng_bar, zone, mk, pn, br, cap)

        # 6. Le bon modèle pour ton budget, les bonnes questions, la négociation chiffres en main
        v = B[5]["voix"]
        cup = m.VMobject(stroke_color=GOLD, stroke_width=10)
        cup.set_points_as_corners([[-2.0, ART_Y + 3.0, 0], [-2.0, ART_Y + 0.8, 0], [2.0, ART_Y + 0.8, 0], [2.0, ART_Y + 3.0, 0]])
        cup_l = T("Ton budget", 40, GOLD).next_to(cup, m.DOWN, buff=0.2)
        hs = house(2.4).move_to([0, ART_Y + 9, 0])
        ok = check(0.8).move_to([2.4, ART_Y + 3.0, 0])
        me = person(ORANGE, 1.1).move_to([-2.2, ART_Y - 1.6, 0])
        pro = helmet_person(GREEN_LIGHT, 1.1).move_to([2.2, ART_Y - 1.6, 0])
        q1 = bubble(2.2, 0.8).move_to([-1.0, ART_Y - 0.3, 0])
        q2 = bubble(2.2, 0.8, fill=GOLD, right=True).move_to([1.0, ART_Y - 0.7, 0])
        doc = icon_doc().scale(0.8).move_to([-0.9, ART_Y - 1.7, 0])
        labels = [chip(t, size=34) for t in B[5]["ecran"]]
        for i, lab in enumerate(labels):
            lab.move_to([0, CAP_Y - 0.4 - i * 0.9, 0])
        self.say(mark(v, "rentre dans ton budget", "les bonnes questions", "chiffres en main"),
                 m.AnimationGroup(m.Create(cup), rise(cup_l),
                                  hs.animate(rate_func=m.ease_out_bounce, run_time=1.0).move_to([0, ART_Y + 1.8, 0]),
                                  slam(ok), rise(labels[0])),
                 m.AnimationGroup(m.FadeIn(me, shift=m.UP), m.FadeIn(pro, shift=m.UP),
                                  m.LaggedStart(m.GrowFromCenter(q1), m.GrowFromCenter(q2), lag_ratio=0.5), rise(labels[1])),
                 m.AnimationGroup(m.FadeOut(q1), m.FadeOut(q2), m.FadeIn(doc, shift=m.UP, rate_func=m.ease_out_back),
                                  rise(labels[2])))
        self.play(m.Indicate(doc, color=GOLD), run_time=0.6)
        clear(self, cup, cup_l, hs, ok, me, pro, doc, *labels)

        # 7. L'offre, 8. l'appel à l'action
        wipe(self)
        clear(self, *offer_beat(self, B[6]))
        cta_beat(self, B[7], "avant de poser la première brique")
