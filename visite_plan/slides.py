"""Diaporama de façade (haut de l'écran) : images facade_1.jpg, facade_2.jpg... du job, fondu enchaîné + zoom / pan lents (Ken Burns).
Piloté par l'horloge absolue de la vidéo (t_start = début du segment) : chaque segment rendu est donc cohérent."""
from pathlib import Path

PATTERNS = [  # (zoom début, zoom fin, pan début (x,y), pan fin (x,y)) ; pan en fraction de la marge disponible [-1, 1]
    (1.00, 1.12, (-0.7, 0.0), (0.7, 0.0)),
    (1.14, 1.02, (0.6, 0.3), (-0.6, -0.3)),
    (1.02, 1.14, (0.0, 0.8), (0.0, -0.8)),
    (1.12, 1.00, (-0.5, -0.5), (0.5, 0.5)),
    (1.00, 1.13, (0.7, 0.0), (-0.7, 0.0)),
]


def find(job):
    return [p for p in (Path(job) / f"facade_{i}.jpg" for i in range(1, 12)) if p.exists()]


def make(m, job, frame_w, slot_y, slot_h, t_start=0.0, z0=11, period=4.5, fade=0.8, order=(1, 0, 2, 3, 4)):
    files = find(job)
    if not files:
        return None
    _o = Path(job) / 'order.json'
    if _o.exists():
        import json as _j
        order = tuple(_j.loads(_o.read_text(encoding='utf-8'))['order'])
    files = [files[i] for i in order if i < len(files)] or files
    N = len(files)
    clk = [float(t_start)]
    imgs = []
    for k, f in enumerate(files):
        im = m.ImageMobject(str(f))
        im.scale_to_fit_height(slot_h * 1.01).move_to([0, slot_y, 0]).set_z_index(z0 + k)
        imgs.append(im)
    base_w = imgs[0].width
    base_h = imgs[0].height

    def state(k, T):
        n = int(T // period)
        if n % N == k:
            return n, T - n * period
        if n >= 1 and (n - 1) % N == k and (T - n * period) < fade:
            return n - 1, T - (n - 1) * period
        return None

    def make_up(k):
        def up(mob, dt):
            if k == 0:
                clk[0] += dt
            T = clk[0]
            st = state(k, T)
            if st is None:
                mob.set_opacity(0)
                return
            mm, age = st
            n = int(T // period)
            sa, sb, pa, pb = PATTERNS[mm % len(PATTERNS)]
            u = min(1.0, age / (period + fade))
            s = sa + (sb - sa) * u
            fx = pa[0] + (pb[0] - pa[0]) * u
            fy = pa[1] + (pb[1] - pa[1]) * u
            dx = fx * (s - 1) * base_w / 2
            dy = fy * (s - 1) * base_h / 2
            mob.scale_to_fit_height(slot_h * 1.01 * s)
            mob.move_to([dx, slot_y + dy, 0])
            if mm == n:                                   # diapo courante
                if mm == 0:
                    op = 1.0
                else:
                    kp = (mm - 1) % N
                    op = min(1.0, age / fade) if k > kp else 1.0
            else:                                         # diapo sortante (pendant le fondu)
                k_new = n % N
                op = 1.0 - min(1.0, (T - n * period) / fade) if k > k_new else 1.0
            mob.set_opacity(max(0.0, min(1.0, op)))
        return up

    for k, im in enumerate(imgs):
        im.add_updater(make_up(k))
    return m.Group(*imgs)
