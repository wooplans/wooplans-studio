from common import *
FA = A + 'fontawesome-webfont.ttf'
@lru_cache(None)
def fa(sz): return ImageFont.truetype(FA, sz)

def icon(d, xy, ch, sz, fill, anchor='mm'):
    d.text(xy, ch, font=fa(sz), fill=fill, anchor=anchor)

def subscribe_btn(im, t, t0, t_out, cx, cy, click_at=1.5):
    """bouton rouge « S'abonner » -> « Abonné » ; cx,cy centre."""
    p = e_back((t - t0) / 0.35)
    if p <= 0.02: return
    out = clamp((t - t_out) / 0.3)
    if out >= 1: return
    clicked = t > t0 + click_at
    w, h = 420, 100
    s = clamp(p, 0, 1.12) * (1 - 0.3 * out)
    ov = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    col = (70, 70, 70, 255) if clicked else (230, 30, 30, 255)
    d.rounded_rectangle((10, 10, w + 10, h + 10), 50, fill=col)
    d.text((10 + 250, 10 + h // 2), 'Abonné' if clicked else "S'abonner", font=font(40), fill=WHITE, anchor='mm')
    d.ellipse((10 + 20, 10 + 20, 10 + 80, 10 + 80), fill=WHITE)
    icon(d, (10 + 50, 10 + 50), '', 34, col[:3])
    ov = ov.resize((max(1, int(ov.width * s)), max(1, int(ov.height * s))), Image.LANCZOS)
    pos = (int(cx - ov.width / 2), int(cy - ov.height / 2))
    im.alpha_composite(ov, pos)
    if t0 + 0.9 < t < t0 + click_at + 0.7:
        q = clamp((t - t0 - 0.9) / 0.6)
        x = int(pos[0] + ov.width * 0.6 + (1 - e_out(q)) * 140); y = int(pos[1] + ov.height * 0.62 + (1 - e_out(q)) * 100)
        d2 = ImageDraw.Draw(im)
        d2.polygon([(x, y), (x, y + 46), (x + 13, y + 35), (x + 30, y + 35)], fill=WHITE, outline=DARK)

def pill_icon(im, xy, ch, label, t, t0, color=ORANGE, t_out=1e9, size=40):
    """pastille arrondie icône + libellé qui « pop » à t0 ; xy = centre."""
    p = e_back((t - t0) / 0.35)
    if p <= 0.02: return
    out = clamp((t - t_out) / 0.3)
    if out >= 1: return
    wt = int(tw(label, size) + 150); h = 110
    ov = Image.new('RGBA', (wt + 20, h + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle((10, 10, wt + 10, h + 10), 55, fill=WHITE + (245,))
    d.ellipse((20, 20, 20 + h - 20, 20 + h - 20), fill=color)
    icon(d, (10 + h // 2, 10 + h // 2), ch, 44, WHITE)
    d.text((10 + h + 4, 10 + h // 2), label, font=font(size), fill=DARK, anchor='lm')
    s = clamp(p, 0, 1.1) * (1 - 0.3 * out)
    ov = ov.resize((max(1, int(ov.width * s)), max(1, int(ov.height * s))), Image.LANCZOS)
    im.alpha_composite(ov, (int(xy[0] - ov.width / 2), int(xy[1] - ov.height / 2)))
