"""Rendu « style WooPlans » d'un plan 2D (référence : jobs/V3-003/plan.png) et repérage précis des pièces.

À partir d'un plan source (bleu, couleur, capture…) :
  - murs : détectés comme les traits épais, redessinés en noir plein ;
  - pièces : segmentées entre les murs (portes refermées le temps du remplissage), sol par type de pièce
    (blanc, carrelage clair des pièces d'eau, pierre grise des terrasses) ;
  - mobilier : traits fins du plan source, en gris ;
  - étiquettes : style WooPlans (Inter Bold noir, « Chambre 2 »), sans surface faute de PDF.
Les polygones des pièces et les trajets du point (plus court chemin dans les pièces, donc par les portes)
sont calculés sur la même géométrie, puis écrits dans paths.json.
"""
import heapq
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FLOORS = {                       # couleur de sol, couleur des joints, pas du carrelage (0 = uni)
    "sec": ((255, 255, 255), None, 0),
    "eau": ((226, 238, 246), (200, 218, 232), 26),
    "cuisine": ((240, 240, 238), (222, 222, 218), 30),
    "ext": ((228, 228, 226), (210, 210, 206), 0),
    "garage": ((236, 233, 228), None, 0),
}
INK_WALL = (22, 22, 22)
INK_FURN = (120, 120, 118)


def disk(r):
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


def split_ink(ink, wall_px, min_area=12, close_px=4, min_len=45, min_wall=60, drop=(), rect_t=0):
    """ink (bool) -> (murs, mobilier). Murs = traits d'au moins wall_px d'épaisseur et min_len de long,
    horizontaux ou verticaux (les plans sont orthogonaux) ; le reste est du mobilier."""
    m = ink.astype(np.uint8)
    for x0, y0, x1, y1 in drop:
        m[y0:y1, x0:x1] = 0
    cl = cv2.morphologyEx(m, cv2.MORPH_CLOSE, disk(close_px)) if close_px else m
    rk = lambda w, h: cv2.getStructuringElement(cv2.MORPH_RECT, (w, h))
    wh = cv2.morphologyEx(cl, cv2.MORPH_OPEN, rk(min_len, wall_px))
    wv = cv2.morphologyEx(cl, cv2.MORPH_OPEN, rk(wall_px, min_len))
    if rect_t:                               # murs redressés : barres droites d'épaisseur constante rect_t
        out = np.zeros_like(m)
        for mask, horiz in ((wh, True), (wv, False)):
            n, lab, st, _ = cv2.connectedComponentsWithStats(mask, 8)
            for i in range(1, n):
                x, y, w, h, _ = st[i]
                thick = h if horiz else w
                if thick <= 2.4 * wall_px:
                    if horiz:
                        cy = y + h // 2; out[cy - rect_t // 2:cy + (rect_t + 1) // 2, x:x + w] = 1
                    else:
                        cx = x + w // 2; out[y:y + h, cx - rect_t // 2:cx + (rect_t + 1) // 2] = 1
                else:
                    out[lab == i] = 1
        walls = out
    else:
        walls = wh | wv
    n, lab, st, _ = cv2.connectedComponentsWithStats(walls, 8)
    keep = np.zeros_like(walls)
    for i in range(1, n):
        if max(st[i, 2], st[i, 3]) >= min_wall:
            keep[lab == i] = 1
    walls = cv2.morphologyEx(keep, cv2.MORPH_OPEN, rk(3, 3))
    furn = m & (1 - cv2.dilate(walls, disk(3)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(furn, 8)
    keepf = np.zeros_like(furn)
    for i in range(1, n):
        if st[i, 4] >= min_area:
            keepf[lab == i] = 1
    return walls.astype(bool), keepf.astype(bool)


def vector_walls(walls, T=18, min_len=30, gap=6, join=None):
    """Murs détectés -> segments horizontaux/verticaux (squelette + Hough), fusionnés, prolongés jusqu'aux murs
    perpendiculaires, puis redessinés en barres d'épaisseur T : murs nets comme sur le plan V3-003."""
    from skimage.morphology import skeletonize
    join = join or T
    sk = skeletonize(walls).astype(np.uint8) * 255
    lines = cv2.HoughLinesP(sk, 1, np.pi / 180, 18, minLineLength=min_len, maxLineGap=gap)
    H, V = [], []
    for x0, y0, x1, y1 in (lines.reshape(-1, 4).tolist() if lines is not None else []):
        if abs(y1 - y0) <= 0.18 * abs(x1 - x0):
            H.append([min(x0, x1), max(x0, x1), (y0 + y1) / 2])
        elif abs(x1 - x0) <= 0.18 * abs(y1 - y0):
            V.append([min(y0, y1), max(y0, y1), (x0 + x1) / 2])

    def merge(segs):
        segs.sort(key=lambda s: (round(s[2] / 8), s[0]))
        out = []
        for a0, a1, c in sorted(segs, key=lambda s: s[2]):
            for o in out:
                if abs(o[2] - c) <= 8 and a0 <= o[1] + gap and a1 >= o[0] - gap:
                    w0, w1 = o[1] - o[0], a1 - a0
                    o[2] = (o[2] * w0 + c * w1) / max(1, w0 + w1); o[0] = min(o[0], a0); o[1] = max(o[1], a1)
                    break
            else:
                out.append([a0, a1, c])
        return out
    for _ in range(2):
        H, V = merge(H), merge(V)
    for h in H:                               # prolonger jusqu'aux murs perpendiculaires (angles fermés)
        for v in V:
            if v[0] - join <= h[2] <= v[1] + join:
                if abs(h[0] - v[2]) <= join: h[0] = min(h[0], v[2])
                if abs(h[1] - v[2]) <= join: h[1] = max(h[1], v[2])
    for v in V:
        for h in H:
            if h[0] - join <= v[2] <= h[1] + join:
                if abs(v[0] - h[2]) <= join: v[0] = min(v[0], h[2])
                if abs(v[1] - h[2]) <= join: v[1] = max(v[1], h[2])
    out = np.zeros(walls.shape, np.uint8)
    t = T // 2
    for x0, x1, y in H:
        cv2.rectangle(out, (int(x0) - t, int(y) - t), (int(x1) + t, int(y) + t), 1, -1)
    for y0, y1, x in V:
        cv2.rectangle(out, (int(x) - t, int(y0) - t), (int(x) + t, int(y1) + t), 1, -1)
    return out.astype(bool)


def room_region(walls, seed, close_px, box=None):
    """Pièce contenant seed : remplissage entre les murs, portes refermées par une dilatation de close_px."""
    h, w = walls.shape
    sq = cv2.getStructuringElement(cv2.MORPH_RECT, (2 * close_px + 1, 2 * close_px + 1))
    blocked = cv2.dilate(walls.astype(np.uint8), sq)
    if box is not None:                       # pièce ouverte (terrasse, séjour/salle à manger) : bornée par un cadre
        lim = np.ones_like(blocked); x0, y0, x1, y1 = box; lim[y0:y1, x0:x1] = 0
        blocked = blocked | lim
    sx, sy = seed
    if blocked[sy, sx]:                       # graine trop près d'un mur : point libre le plus proche
        ys, xs = np.where(blocked[max(0, sy - 120):sy + 120, max(0, sx - 120):sx + 120] == 0)
        if not len(xs):
            raise ValueError(f"graine {seed} dans un mur")
        k = np.argmin((xs + max(0, sx - 120) - sx) ** 2 + (ys + max(0, sy - 120) - sy) ** 2)
        sx, sy = int(xs[k] + max(0, sx - 120)), int(ys[k] + max(0, sy - 120))
    ff = np.zeros((h + 2, w + 2), np.uint8)
    reg = (1 - blocked).copy()
    cv2.floodFill(reg, ff, (sx, sy), 2)
    r = (reg == 2).astype(np.uint8)
    r = cv2.dilate(r, sq) & (1 - walls.astype(np.uint8))
    if box is not None:
        lim = np.zeros_like(r); x0, y0, x1, y1 = box; lim[y0:y1, x0:x1] = 1; r &= lim
    return r.astype(bool)


def polygon(mask, eps=3.0):
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cs, key=cv2.contourArea)
    c = cv2.approxPolyDP(c, eps, True)
    return [[int(p[0][0]), int(p[0][1])] for p in c]


def tiles(img, mask, col, joint, step):
    a = np.asarray(img).copy()
    a[mask] = col
    if joint and step:
        yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        grid = ((yy % step) == 0) | ((xx % step) == 0)
        a[mask & grid] = joint
    return Image.fromarray(a)


def label(draw, xy, text, size=24):
    f = ImageFont.truetype(FONT, size)
    lines = text.split("\n")
    lh = int(size * 1.2)
    y0 = xy[1] - lh * (len(lines) - 1) / 2
    for i, t in enumerate(lines):
        draw.text((xy[0], y0 + i * lh), t, font=f, fill=(20, 20, 20), anchor="mm",
                  stroke_width=3, stroke_fill=(255, 255, 255))


def render(src, ink, wall_px, rooms, close_px, erase_boxes=(), wall_extra=(), out=None, T=18, vector=True, **kw):
    """rooms : liste de dicts {name, label, seed, sol, box?, label_xy?}. Renvoie (image, {nom: masque}, murs)."""
    walls, furn = split_ink(ink, wall_px, drop=erase_boxes, **kw)
    if vector:
        raw = walls
        walls = vector_walls(raw, T)
        furn &= ~cv2.dilate(raw.astype(np.uint8), disk(2)).astype(bool)
    for x0, y0, x1, y1 in wall_extra:         # murs à compléter à la main (rares)
        walls[y0:y1, x0:x1] = True
    h, w = walls.shape
    img = Image.new("RGB", (w, h), (255, 255, 255))
    masks = {}
    for r in rooms:
        m = room_region(walls, r["seed"], close_px, r.get("box"))
        masks[r["name"]] = m
        col, joint, step = FLOORS[r.get("sol", "sec")]
        img = tiles(img, m, col, joint, step)
    a = np.asarray(img).copy()
    a[furn] = INK_FURN
    a[walls] = INK_WALL
    img = Image.fromarray(a)
    d = ImageDraw.Draw(img)
    for r in rooms:
        if r.get("label"):
            label(d, r.get("label_xy", r["seed"]), r["label"], r.get("size", 24))
    if out:
        img.save(out)
    return img, masks, walls


def shortest_path(walls, a, b, clear_px=6, step=3, footprint=None):
    """Plus court chemin de a à b hors des murs (marge clear_px), sur une grille de pas step ; préfère le milieu des passages."""
    free = 1 - cv2.dilate(walls.astype(np.uint8), disk(clear_px))
    if footprint is not None:
        free &= footprint.astype(np.uint8)
    dist = cv2.distanceTransform(free, cv2.DIST_L2, 5)
    fs, ds = free[::step, ::step], dist[::step, ::step]
    H, W = fs.shape
    cost = 1.0 + 6.0 / (1.0 + ds)
    s = (a[1] // step, a[0] // step); g = (b[1] // step, b[0] // step)
    for p in (s, g):
        if not fs[p]:
            raise ValueError(f"point {p[1]*step, p[0]*step} hors de l'espace libre")
    best = np.full((H, W), np.inf); best[s] = 0; prev = {}
    q = [(0.0, s)]
    nb = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1), (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]
    while q:
        c, p = heapq.heappop(q)
        if p == g:
            break
        if c > best[p]:
            continue
        for dy, dx, k in nb:
            n = (p[0] + dy, p[1] + dx)
            if 0 <= n[0] < H and 0 <= n[1] < W and fs[n]:
                nc = c + k * cost[n]
                if nc < best[n]:
                    best[n] = nc; prev[n] = p; heapq.heappush(q, (nc, n))
    if g not in prev and g != s:
        raise ValueError(f"aucun passage entre {a} et {b}")
    pts = [g]
    while pts[-1] != s:
        pts.append(prev[pts[-1]])
    pts = [(p[1] * step, p[0] * step) for p in reversed(pts)]
    simp = [tuple(map(float, p[0])) for p in cv2.approxPolyDP(np.array(pts, np.int32).reshape(-1, 1, 2), 4, False)]
    for _ in range(2):                        # lissage (Chaikin) : le point tourne au lieu de pivoter
        if len(simp) < 3:
            break
        sm = [simp[0]]
        for p, q in zip(simp, simp[1:]):
            sm += [(0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]), (0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1])]
        sm.append(simp[-1]); simp = sm
    return [[round(x, 1), round(y, 1)] for x, y in simp]


def footprint_of(walls, close_px=60):
    """Emprise du bâtiment : murs refermés (fenêtres, portes), puis tout ce qui n'est pas joignable depuis le bord."""
    pad = 2 * close_px + 10
    m = cv2.copyMakeBorder(walls.astype(np.uint8), pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (2 * close_px + 1, 2 * close_px + 1))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    ext = (1 - m).astype(np.uint8)
    ff = np.zeros((ext.shape[0] + 2, ext.shape[1] + 2), np.uint8)
    cv2.floodFill(ext, ff, (0, 0), 2)
    fp = (ext != 2).astype(np.uint8)
    return fp[pad:-pad, pad:-pad]


def write_paths(job, rooms, masks, walls, start, order=None, clear_px=6, extra_free=None, footprint=None):
    """paths.json : pour chaque pièce dans l'ordre de visite, son polygone et le trajet depuis la précédente."""
    if footprint is None:
        footprint = footprint_of(walls)
    if extra_free is not None:
        footprint = footprint | extra_free
    by = {r["name"]: r for r in rooms}
    order = order or [r["name"] for r in rooms]
    out, pos = [], tuple(start)
    for name in order:
        r = by[name]
        stop = tuple(r.get("stop", r["seed"]))
        path = shortest_path(walls, pos, stop, clear_px, footprint=footprint)
        out.append({"name": name, "path": path, "poly": polygon(masks[name])})
        pos = stop
    Path(job, "paths.json").write_text(json.dumps({"start": list(start), "rooms": out}, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    return out


def check_image(plan_img, rooms_out, out):
    img = plan_img.convert("RGB").copy(); d = ImageDraw.Draw(img, "RGBA")
    cols = [(240, 138, 46), (200, 0, 0), (0, 160, 0), (160, 0, 200), (0, 160, 160), (200, 120, 0), (255, 0, 120),
            (90, 90, 90), (0, 0, 0), (0, 120, 255), (120, 60, 0), (0, 90, 60)]
    for i, r in enumerate(rooms_out):
        c = cols[i % len(cols)]
        d.polygon([tuple(p) for p in r["poly"]], fill=c + (50,), outline=c + (255,))
        d.line([tuple(p) for p in r["path"]], fill=c + (255,), width=5)
    img.save(out)
