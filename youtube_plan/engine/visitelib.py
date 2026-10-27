import sys
from common import *

VX, VY, VW, VH = 60, 128, 1140, 855
PX, PY, PWD, PHT = 1236, 128, 644, 470
PW, PH = 1024, 768


def make(voice, durkey, plan_file, ROOMS, WAY, head, intro_title, intro_big, intro_sub, big_size=150, rb_start=0):
    PLAN = Image.open(A + plan_file).convert('RGB')
    words = words_of(voice)
    TOKS = caption_tokens(words)
    ARR = [find(words, r, n) for (_, _, _, _, _, r, n) in ROOMS]
    DUR = D[durkey]
    END_ZOOM = DUR - 1.7
    N = len(ROOMS)

    def _plan_len(pts):
        return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))

    def _along(pts, f):
        L = _plan_len(pts); target = L * clamp(f); acc = 0
        for i in range(len(pts) - 1):
            seg = math.dist(pts[i], pts[i + 1])
            if acc + seg >= target - 1e-9:
                u = (target - acc) / seg if seg else 0
                return (lerp(pts[i][0], pts[i + 1][0], u), lerp(pts[i][1], pts[i + 1][1], u))
            acc += seg
        return pts[-1]

    DEP = []
    for i in range(N - 1):
        gap = ARR[i + 1] - ARR[i]
        T = min(2.4, 0.8 * gap)
        DEP.append(max(ARR[i] + 0.35, ARR[i + 1] - T))
    DEP.append(1e9)

    def state(t):
        if t < ARR[0]:
            return ROOMS[0][3], -1, 0, 0
        for i in range(N):
            if t < DEP[i] or i == N - 1:
                return ROOMS[i][3], i, 0, i
            if t < ARR[i + 1]:
                f = e_io((t - DEP[i]) / (ARR[i + 1] - DEP[i]))
                pts = [ROOMS[i][3]] + WAY[i] + [ROOMS[i + 1][3]]
                return _along(pts, f), i, f, i + 1
        return ROOMS[-1][3], N - 1, 0, N - 1

    def camera(t):
        pos, i, f, j = state(t)
        if i == -1:
            return PW / 2, PH / 2, 1.0
        zi, ci = ROOMS[i][4], ROOMS[i][3]
        zj, cj = ROOMS[j][4], ROOMS[j][3]
        z = lerp(zi, zj, f); c = (lerp(ci[0], cj[0], f), lerp(ci[1], cj[1], f))
        if t > END_ZOOM:
            k = e_io((t - END_ZOOM) / 1.5)
            z = lerp(z, 1.0, k); c = (lerp(c[0], PW / 2, k), lerp(c[1], PH / 2, k))
        return c[0], c[1], z

    def hi_alpha(t, i):
        a = ARR[i] - 0.15
        b = DEP[i] + 0.1 if i < N - 1 else END_ZOOM
        if t < a or t > b + 0.3:
            return 0
        return clamp((t - a) / 0.25) * clamp((b + 0.3 - t) / 0.3)

    cache = {}

    def bg():
        if 'bg' not in cache:
            b = Image.new('RGBA', (W, H), LIGHT + (255,))
            lg = img('logo_green.png').copy(); lg.thumbnail((900, 600))
            paste_alpha(b, lg, (W // 2 - lg.width // 2, H // 2 - lg.height // 2 + 40), 0.06)
            header(b, head)
            shadow_card(b, (VX - 10, VY - 10, VX + VW + 10, VY + VH + 10), r=30)
            shadow_card(b, (PX, PY, PX + PWD, PY + PHT), r=30)
            cache['bg'] = b
            m = Image.new('L', (VW, VH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, VW - 1, VH - 1), 22, fill=255); cache['m'] = m
        return cache['bg']

    def frame(t):
        base = bg().copy(); _mask = cache['m']
        cx, cy, z = camera(t)
        cw, ch = PW / z, PH / z
        x0 = clamp(cx - cw / 2, 0, PW - cw); y0 = clamp(cy - ch / 2, 0, PH - ch)
        vp = PLAN.resize((VW, VH), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch)).convert('RGBA')
        sc = VW / cw
        tp = lambda p: ((p[0] - x0) * sc, (p[1] - y0) * sc)
        ov = Image.new('RGBA', (VW, VH), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        for i, r in enumerate(ROOMS):
            a = hi_alpha(t, i)
            if a > 0:
                pts = [tp(p) for p in r[2]]
                d.polygon(pts, fill=ORANGE + (int(105 * a),), outline=ORANGE + (int(255 * a),), width=4)
        pos, i, f, j = state(t)
        show = clamp((t - (ARR[0] - 0.7)) / 0.5)
        if show > 0:
            for k in range(14, 0, -1):
                pk = state(t - k * 0.045)[0]
                px, py = tp(pk); rr = 5 + 9 * (1 - k / 15)
                d.ellipse((px - rr, py - rr, px + rr, py + rr), fill=(34, 197, 94, int(90 * (1 - k / 15) * show)))
            px, py = tp(pos)
            pulse = 0.5 + 0.5 * math.sin(t * 6.0)
            R = (24 + 10 * pulse) * show
            d.ellipse((px - R, py - R, px + R, py + R), fill=(34, 197, 94, int(70 * show)))
            r2 = 15 * show
            d.ellipse((px - r2, py - r2, px + r2, py + r2), fill=(34, 197, 94, 255), outline=WHITE + (255,), width=4)
        vp.alpha_composite(ov)
        vpm = Image.new('RGBA', (VW, VH), (0, 0, 0, 0)); vpm.paste(vp, (0, 0), _mask)
        base.alpha_composite(vpm, (VX, VY))
        d = ImageDraw.Draw(base)
        shown = -1
        for k in range(N):
            if t >= ARR[k] - 0.05:
                shown = k
        text(d, (PX + 44, PY + 54), 'VISITE DU PLAN', 30, GREY, 'lm')
        if shown == -1:
            text(d, (PX + 44, PY + 170), intro_title, 52, DARK, 'lm')
            text(d, (PX + 44, PY + 290), intro_big, big_size, ORANGE, 'lm')
            text(d, (PX + 44, PY + 385), intro_sub, 32, GREY, 'lm')
        else:
            name, surf = ROOMS[shown][0], ROOMS[shown][1]
            p = e_back((t - ARR[shown]) / 0.35)
            off = int((1 - clamp(p, 0, 1.2)) * 40)
            text(d, (PX + 44, PY + 165 - off), name, 54 if len(name) < 17 else 46, DARK, 'lm')
            if surf is None:
                text(d, (PX + 44, PY + 290), "vers l'étage", int(80 * (0.7 + 0.3 * clamp(p, 0, 1.15))), ORANGE, 'lm')
            else:
                s = int(130 * (0.7 + 0.3 * clamp(p, 0, 1.15)))
                text(d, (PX + 44, PY + 290), f'{surf}', s, ORANGE, 'lm')
                wnum = tw(f'{surf}', s)
                text(d, (PX + 44 + wnum + 10, PY + 322), 'm²', int(s * 0.5), ORANGE, 'lm')
        done = max(shown + 1, 0)
        gap = (PWD - 88) / (N - 1)
        for k in range(N):
            cxk = PX + 44 + k * gap; cyk = PY + PHT - 100
            r = 11
            d.ellipse((cxk - r, cyk - r, cxk + r, cyk + r), fill=GREEN if k < done else (220, 225, 230))
        text(d, (PX + 44, PY + PHT - 52), f'Espace {max(done, 1)} sur {N}' if shown >= 0 else "Entrée du niveau", 28, GREY, 'lm')
        render_box(base, (PX, 618, PX + PWD, 983), t, start=rb_start)
        draw_caption(base, TOKS, t)
        return base.convert('RGB')

    return frame, ARR, DUR
