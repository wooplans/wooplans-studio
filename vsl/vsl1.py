"""VSL1 « L'erreur qui coûte le plus cher » en motion design.

Aperçu muet : manimgx render vsl1.py VSL1 -r 1080x1920 --fps 30
Voix LeTao  : VSL_VOICE=letao (clé ELEVENLABS_API_KEY dans l'environnement)
"""

import numpy as np
import manimgx as m

from motion import (ART_Y, CAP_Y, GOLD, GREEN_LIGHT, ORANGE, RED, VOICE, T, background, caption, card, check,
                    chip, clear, coin, counter, cross, cta_beat, fan, house, icon_cube, icon_doc, icon_plan,
                    icon_ruler, mark, offer_beat, person, rise, sad_face, script, slam, tile, underline, wipe)

S = script("vsl1_erreur")
B = S["beats"]


class VSL1(m.Scene):
    voice = VOICE

    def construct(self) -> None:
        background(self)

        # 1. Accroche : une maison se dessine, puis l'avertissement claque
        v = B[0]["voix"]
        hs = house(3.4).move_to([0, ART_Y + 0.6, 0])
        warn = m.VGroup(m.Triangle(fill_color=RED, fill_opacity=1, stroke_color=m.WHITE, stroke_width=5).scale(0.75),
                        T("!", 70)).move_to(hs.get_corner(m.UR) + [0, 0.1, 0])
        warn[1].move_to(warn[0].get_center() + 0.1 * m.DOWN)
        cap = caption(B[0]["ecran"], accent="la plus chère", y=CAP_Y + 0.6)
        self.say(mark(v, "construire ta maison", "l'erreur la plus chère", "pas sur le chantier"),
                 m.DrawBorderThenFill(hs, run_time=1.4),
                 m.AnimationGroup(slam(cap[0]), m.GrowFromCenter(warn, rate_func=m.ease_out_back), m.Wiggle(hs)),
                 m.LaggedStart(rise(cap[1]), rise(cap[2]), lag_ratio=0.4))
        clear(self, hs, warn, cap)

        # 2. « Elle se fait avant » : un seul plan arrive trop vite, les autres cases restent vides
        v = B[1]["voix"]
        avant = T("AVANT", 150, ORANGE).move_to([0, ART_Y + 2.6, 0])
        one = card(1.2).move_to([0, ART_Y - 0.4, 0])
        slots = m.VGroup(*[m.DashedVMobject(m.RoundedRectangle(corner_radius=0.15, width=1.9, height=2.5, color=m.WHITE,
                                                               stroke_width=4), num_dashes=24).scale(0.9) for _ in range(2)])
        slots[0].move_to([-2.7, ART_Y - 0.4, 0])
        slots[1].move_to([2.7, ART_Y - 0.4, 0])
        qs = m.VGroup(*[T("?", 90, GOLD).move_to(s) for s in slots])
        ul = underline(avant)
        cap = caption(B[1]["ecran"][1:], y=CAP_Y)
        one.shift(9 * m.RIGHT)
        self.say(mark(v, "Elle se fait avant", "trop vite", "une seule proposition", "sans rien comparer"),
                 m.AnimationGroup(slam(avant), m.Create(ul, run_time=0.6)),
                 one.animate(rate_func=m.ease_out_expo, run_time=0.6).shift(9 * m.LEFT),
                 rise(cap),
                 m.AnimationGroup(m.Create(slots), m.LaggedStart(*[slam(q) for q in qs], lag_ratio=0.3)))
        clear(self, avant, ul, one, slots, qs, cap)

        # 3. Modifications en cours de chantier : mur fissuré, chambre ajoutée, toiture refaite, l'argent s'envole
        v = B[2]["voix"]
        hs = house(3.2).move_to([-0.6, ART_Y + 0.2, 0])
        crack = m.VMobject(stroke_color=RED, stroke_width=9)
        bx, by = hs.body.get_center()[:2]
        crack.set_points_as_corners([[bx - 0.9, by + 0.95, 0], [bx - 0.6, by + 0.45, 0], [bx - 0.95, by + 0.1, 0],
                                     [bx - 0.55, by - 0.35, 0], [bx - 0.8, by - 0.95, 0]])
        room = m.Rectangle(width=1.4, height=hs.body.height * 0.75, fill_color=GOLD, fill_opacity=1,
                           stroke_color=m.WHITE, stroke_width=4)
        room.next_to(hs.body, m.RIGHT, buff=0).align_to(hs.body, m.DOWN)
        new_roof = hs.roof.copy().set_fill(GREEN_LIGHT).shift(4 * m.UP)
        labels = [chip(t, size=36) for t in B[2]["ecran"]]
        for i, lab in enumerate(labels):
            lab.move_to([0, CAP_Y + 0.4 - i * 0.95, 0])
        coins = m.VGroup(*[coin(0.3).move_to(hs.get_center()) for _ in range(9)])
        rng = np.random.default_rng(3)
        flights = [m.FadeOut(c, shift=[rng.uniform(-3.5, 3.5), rng.uniform(1.5, 5), 0], run_time=1.2,
                             rate_func=m.ease_out_cubic) for c in coins]
        cost = T("coûte cher", 110, ORANGE).move_to([0, ART_Y + 3.9, 0])
        self.add(hs)
        self.say(mark(v, "Et ensuite ?", "casse un mur", "rajoute une chambre", "refait la toiture", "coûte cher"),
                 m.FadeIn(hs, scale=0.6, rate_func=m.ease_out_back),
                 m.AnimationGroup(m.Create(crack, run_time=0.5), m.Wiggle(hs, run_time=0.6), rise(labels[0])),
                 m.AnimationGroup(m.GrowFromEdge(room, m.LEFT, rate_func=m.ease_out_back), rise(labels[1])),
                 m.AnimationGroup(m.FadeOut(hs.roof, shift=3 * m.UP), new_roof.animate(rate_func=m.ease_out_bounce, run_time=0.9)
                                  .shift(4 * m.DOWN), rise(labels[2])),
                 m.AnimationGroup(m.LaggedStart(*flights, lag_ratio=0.08), slam(cost)))
        clear(self, hs, crack, room, new_roof, *labels, cost)

        # 4. Le regret : la petite maison triste face à celle du voisin
        v = B[3]["voix"]
        mine = house(2.2, roof=GREY_ROOF).move_to([-1.9, ART_Y - 0.2, 0])
        face = sad_face(0.45).next_to(mine, m.UP, buff=0.3)
        neigh = house(3.4, roof=ORANGE).move_to([1.6, ART_Y + 0.4, 0])
        stars = m.VGroup(*[m.Star(5, outer_radius=0.22, fill_color=GOLD, fill_opacity=1, stroke_width=0)
                           .move_to(neigh.get_center() + p) for p in ([-1.9, 2.0, 0], [1.9, 1.7, 0], [2.0, -0.6, 0])])
        cap = caption(B[3]["ecran"], accent="voisin", y=CAP_Y)
        self.say(mark(v, "regretter", "la maison du voisin"),
                 m.AnimationGroup(m.FadeIn(mine, shift=m.UP), slam(face)),
                 m.AnimationGroup(m.GrowFromEdge(neigh, m.DOWN, rate_func=m.ease_out_back),
                                  m.LaggedStart(*[m.SpinInFromNothing(s) for s in stars], lag_ratio=0.25), rise(cap)))
        self.play(m.Wiggle(face), run_time=0.6)
        clear(self, mine, face, neigh, stars, cap)

        # 5. La solution : le catalogue, l'éventail des modèles, le compteur 50+
        wipe(self)
        v = B[4]["voix"]
        cover = m.VGroup(m.RoundedRectangle(corner_radius=0.3, width=5.6, height=2.0, fill_color=m.WHITE, fill_opacity=1,
                                            stroke_color=GOLD, stroke_width=8),
                         T("CATALOGUE PREMIUM", 54, "#0F5B59", max_w=4.9)).move_to([0, ART_Y + 3.4, 0])
        cover[1].move_to(cover[0])
        cards, pivot = fan()
        num, upd = counter(50, "+", 150)
        num.move_to([0, CAP_Y + 0.1, 0])
        sub = T("villas et duplex", 60).next_to(num, m.DOWN, buff=0.3)
        africa = chip("Conçus pour l'Afrique", fill="#F08A2E").move_to([0, CAP_Y - 2.75, 0])
        self.say(mark(v, "Catalogue Premium WooPlans", "plus de cinquante modèles", "conçus pour l'Afrique"),
                 m.SpinInFromNothing(cover, angle=0.4, rate_func=m.ease_out_back, run_time=0.8),
                 m.AnimationGroup(m.LaggedStart(*[m.FadeIn(c, shift=2 * m.UP, scale=0.5, rate_func=m.ease_out_back) for c in cards],
                                                lag_ratio=0.12, run_time=1.4),
                                  m.UpdateFromAlphaFunc(num, upd, run_time=1.4, rate_func=m.ease_out_cubic), rise(sub)),
                 slam(africa))
        clear(self, cover, cards, num, sub, africa)

        # 6. Ce que contient chaque modèle : quatre tuiles qui s'allument une à une
        v = B[5]["voix"]
        tiles = m.VGroup(tile(icon_cube(), "Rendus 3D"), tile(icon_plan(), "Distribution cotée"),
                         tile(icon_ruler(), "Surfaces"), tile(icon_doc(), "Devis par lot"))
        tiles.arrange_in_grid(2, 2, buff=0.35).move_to([0, ART_Y - 1.6, 0])
        checks = [check(0.6).move_to(t.get_corner(m.UR) + [-0.1, -0.1, 0]) for t in tiles]
        head = T("Pour chaque modèle", 80, GOLD).move_to([0, ART_Y + 3.4, 0])
        self.say(mark(v, "Pour chaque modèle", "rendus 3D", "distribution cotée", "surfaces", "devis estimatif détaillé par lot"),
                 rise(head),
                 *[m.Succession(m.GrowFromCenter(t, rate_func=m.ease_out_back, run_time=0.5), slam(c, 0.3))
                   for t, c in zip(tiles, checks)])
        self.play(m.Circumscribe(tiles[3], color=ORANGE, run_time=0.8))
        clear(self, head, tiles, *checks)

        # 7. Comparer en famille et choisir sans regret
        v = B[6]["voix"]
        a = card(1.1).move_to([-2.0, ART_Y + 1.6, 0]).rotate(0.08)
        b = card(1.1, GOLD).move_to([2.0, ART_Y + 1.6, 0]).rotate(-0.08)
        vs = T("VS", 70, GOLD).move_to([0, ART_Y + 1.6, 0])
        fam = m.VGroup(person(ORANGE, 1.2), person(GOLD, 0.85), person(GREEN_LIGHT, 1.1)).arrange(m.RIGHT, buff=0.25)
        fam.move_to([0, ART_Y - 1.9, 0])
        glow = m.SurroundingRectangle(b, color=GOLD, buff=0.15, stroke_width=8)
        smile = sad_face(0.45, smile=True).next_to(b, m.UP, buff=0.2)
        cap = caption(B[6]["ecran"], accent="sans regret", y=CAP_Y - 0.2)
        self.say(mark(v, "Tu compares", "avec ta famille", "tu choisis une maison", "ne regretteras pas"),
                 m.AnimationGroup(m.FadeIn(a, shift=2 * m.RIGHT), m.FadeIn(b, shift=2 * m.LEFT), slam(vs)),
                 m.LaggedStart(*[m.FadeIn(p, shift=m.UP, rate_func=m.ease_out_back) for p in fam], lag_ratio=0.25),
                 m.AnimationGroup(m.FadeOut(a, scale=0.6), m.FadeOut(vs), b.animate.move_to([0, ART_Y + 1.6, 0]).scale(1.15),
                                  m.Create(glow.move_to([0, ART_Y + 1.6, 0]).scale(1.15))),
                 m.AnimationGroup(slam(smile), rise(cap)))
        clear(self, b, glow, smile, fam, cap)

        # 8. L'offre, puis 9. l'appel à l'action
        wipe(self)
        clear(self, *offer_beat(self, B[7]))
        cta_beat(self, B[8], "Mobile Money")


GREY_ROOF = "#8FA3A1"
