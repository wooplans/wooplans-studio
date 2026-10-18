"""Redessin d'un plan 2D au style WooPlans (référence : jobs/V3-003/plan.png) à partir de la géométrie de ses pièces.

Chaque pièce est un polygone orthogonal (coordonnées du plan source). Les bords sont recalés sur les murs détectés
dans le plan source, puis :
  - sol par type de pièce (blanc, carrelage clair des pièces d'eau, pierre grise des extérieurs) ;
  - murs noirs d'épaisseur constante sur tous les bords ; un trou dans le mur source donne une ouverture
    (porte intérieure dessinée avec son battant, porte extérieure si déclarée) ou une fenêtre bleue sur la façade ;
  - mobilier : traits fins du plan source à l'intérieur des pièces, en gris ;
  - étiquettes au style WooPlans (« Chambre 2 »), sans surface faute de PDF.
Les polygones recalés servent au voile de la vidéo, et le trajet du point est le plus court chemin entre les pièces
en passant par les ouvertures (restyle.shortest_path).
"""
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from restyle import FLOORS, FONT, label as draw_label, shortest_path, tiles

WALL = (24, 24, 24)
GLASS = (174, 214, 236)
GLASS_EDGE = (120, 170, 200)
FURN = (128, 128, 126)


def edges(poly):
    return [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]


def snap_polys(polys, raw, rng=35, band=6):
    """Recale chaque bord (vertical ou horizontal) sur l'axe du mur source le plus proche (densité maximale)."""
    H, W = raw.shape
    xs, ys = {}, {}

    def best(axis_vals, prof):
        k = int(np.argmax(prof))
        return axis_vals[k] if prof[k] > 0.25 else None

    out = []
    for poly in polys:
        poly = [list(p) for p in poly]
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            if a[0] == b[0]:                          # bord vertical
                y0, y1 = sorted((a[1], b[1])); x = a[0]
                key = ("v", x, y0, y1)
                if key not in xs:
                    vals = list(range(max(0, x - rng), min(W - 1, x + rng) + 1))
                    prof = [raw[y0:y1, v - band // 2:v + band // 2 + 1].mean() if y1 > y0 else 0 for v in vals]
                    xs[key] = best(vals, prof)
                nx = xs[key]
                if nx is not None:
                    a[0] = b[0] = nx
            elif a[1] == b[1]:
                x0, x1 = sorted((a[0], b[0])); y = a[1]
                key = ("h", y, x0, x1)
                if key not in ys:
                    vals = list(range(max(0, y - rng), min(H - 1, y + rng) + 1))
                    prof = [raw[v - band // 2:v + band // 2 + 1, x0:x1].mean() if x1 > x0 else 0 for v in vals]
                    ys[key] = best(vals, prof)
                ny = ys[key]
                if ny is not None:
                    a[1] = b[1] = ny
        out.append([tuple(p) for p in poly])
    return out


def unify(polys, tol=10):
    """Fusionne les coordonnées voisines (< tol px) pour que deux pièces voisines partagent exactement leur mur."""
    for axis in (0, 1):
        vals = sorted({p[axis] for poly in polys for p in poly})
        groups, cur = [], [vals[0]]
        for v in vals[1:]:
            if v - cur[0] <= tol:                 # groupe d'au plus tol px (pas de fusion en chaîne)
                cur.append(v)
            else:
                groups.append(cur); cur = [v]
        groups.append(cur)
        m = {v: int(round(sum(g) / len(g))) for g in groups for v in g}
        polys = [[(m[p[0]], p[1]) if axis == 0 else (p[0], m[p[1]]) for p in poly] for poly in polys]
    return polys


def gaps_along(raw, a, b, band, min_gap):
    """Intervalles (en abscisse curviligne) du bord a-b où le mur source est absent sur au moins min_gap px."""
    if a[0] == b[0]:
        y0, y1 = sorted((a[1], b[1])); x = a[0]
        prof = raw[y0:y1, max(0, x - band):x + band + 1].any(1)
        off = y0
    else:
        x0, x1 = sorted((a[0], b[0])); y = a[1]
        prof = raw[max(0, y - band):y + band + 1, x0:x1].any(0)
        off = x0
    out, i, n = [], 0, len(prof)
    while i < n:
        if not prof[i]:
            j = i
            while j < n and not prof[j]:
                j += 1
            if j - i >= min_gap and i > 0 and j < n:
                out.append((off + i, off + j))
            i = j
        else:
            i += 1
    return out


def redraw(src, ink, raw_walls, rooms, T=18, min_gap=48, band=None, ext_doors=(), no_open=(), out=None,
           furn_alpha=1.0, keep_src=False, windows=True, portes=(), auto_gaps=True, furn_col=None):
    """rooms : [{name, poly, sol, label, label_xy?, size?}]. ext_doors : points (x, y) des portes extérieures.
    no_open : points où un trou du mur source n'est pas une ouverture (mur à fermer).
    Renvoie (image, polygones recalés {nom: poly}, masque des murs dessinés)."""
    band = band or T // 2 + 2
    H, W = raw_walls.shape
    snapped = snap_polys([r["poly"] for r in rooms], raw_walls)
    polys = unify([r["poly"] if r.get("ouvert") or r.get("fixe") else p for r, p in zip(rooms, snapped)])
    inside = np.zeros((H, W), np.uint8)
    for p in polys:
        cv2.fillPoly(inside, [np.array(p, np.int32)], 1)
    if keep_src:
        img = src.convert("RGB").copy()
    else:
        img = Image.new("RGB", (W, H), (255, 255, 255))
        for r, p in zip(rooms, polys):
            m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [np.array(p, np.int32)], 1)
            col, joint, step = FLOORS[r.get("sol", "sec")]
            img = tiles(img, m.astype(bool), col, joint, step)
        # mobilier : traits fins du plan source, dans les pièces, hors bande des murs
        wallband = cv2.dilate(raw_walls.astype(np.uint8), np.ones((5, 5), np.uint8))
        edgeband = np.zeros((H, W), np.uint8)               # traits du plan source collés aux murs : retirés
        for p in polys:
            cv2.polylines(edgeband, [np.array(p, np.int32)], True, 1, thickness=2 * T if not auto_gaps else 4)
        ink_in = ink & (inside > 0) & (wallband == 0) & (edgeband == 0)
        a = np.asarray(img).copy()
        a[ink_in] = furn_col or FURN
        img = Image.fromarray(a)
    d = ImageDraw.Draw(img)
    walls = np.zeros((H, W), np.uint8)
    t = T // 2
    lab0 = np.zeros((H, W), np.int32)
    for i, p in enumerate(polys, 1):
        cv2.fillPoly(lab0, [np.array(p, np.int32)], i)
    is_open = {i: bool(r.get("ouvert")) for i, r in enumerate(rooms, 1)}
    seen = set()
    doors = []
    for p in polys:
        for a, b in edges(p):
            key = tuple(sorted((a, b)))
            if key in seen or a == b:
                continue
            seen.add(key)
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            # extérieur si un seul côté du bord est dans une pièce
            nrm = (0, 1) if a[1] == b[1] else (1, 0)
            s1 = (int(mid[0] + nrm[0] * (t + 4)), int(mid[1] + nrm[1] * (t + 4)))
            s2 = (int(mid[0] - nrm[0] * (t + 4)), int(mid[1] - nrm[1] * (t + 4)))
            ins = [0 <= q[0] < W and 0 <= q[1] < H and inside[q[1], q[0]] for q in (s1, s2)]
            exterior = not all(ins)
            sides = [lab0[q[1], q[0]] if ok else 0 for q, ok in zip((s1, s2), ins)]
            opn = [is_open.get(k, False) for k in sides if k]
            if (exterior and opn and all(opn)) or (len(opn) == 2 and all(opn)):
                continue
            gaps = gaps_along(raw_walls, a, b, band, min_gap) if auto_gaps else []
            vertical = a[0] == b[0]
            for px, py, pw in portes:                 # portes imposées (trou du plan source mal détecté)
                on = (abs(px - a[0]) <= t + 6 and min(a[1], b[1]) < py < max(a[1], b[1])) if vertical else \
                     (abs(py - a[1]) <= t + 6 and min(a[0], b[0]) < px < max(a[0], b[0]))
                if on:
                    c = py if vertical else px
                    gaps = sorted([g for g in gaps if g[1] < c - pw // 2 or g[0] > c + pw // 2] + [(c - pw // 2, c + pw // 2)])
            lo, hi = (min(a[1], b[1]), max(a[1], b[1])) if vertical else (min(a[0], b[0]), max(a[0], b[0]))
            pieces, cur = [], lo - t
            for g0, g1 in gaps:
                c = (a[0], (g0 + g1) // 2) if vertical else ((g0 + g1) // 2, a[1])
                if any(abs(c[0] - q[0]) < 60 and abs(c[1] - q[1]) < 60 for q in no_open):
                    continue
                is_door = not exterior or any(abs(c[0] - q[0]) < 70 and abs(c[1] - q[1]) < 70 for q in ext_doors) \
                    or any(abs(c[0] - q[0]) < 20 and abs(c[1] - q[1]) < 20 for q in portes)
                pieces.append((cur, g0, "mur"))
                pieces.append((g0, g1, "porte" if is_door else "fenetre"))
                cur = g1
            pieces.append((cur, hi + t, "mur"))
            if exterior and windows:              # fenêtres décoratives au milieu des grands pans de façade
                fp = []
                for s0, s1_, kind in pieces:
                    L = s1_ - s0
                    if kind == "mur" and L >= 190:
                        wl = int(min(0.42 * L, 170)); m0 = (s0 + s1_) // 2 - wl // 2
                        fp += [(s0, m0, "mur"), (m0, m0 + wl, "fenetre"), (m0 + wl, s1_, "mur")]
                    else:
                        fp.append((s0, s1_, kind))
                pieces = fp
            for s0, s1_, kind in pieces:
                if vertical:
                    x = a[0]; box = (x - t, s0, x + t, s1_)
                else:
                    y = a[1]; box = (s0, y - t, s1_, y + t)
                if kind == "mur":
                    d.rectangle(box, fill=WALL); cv2.rectangle(walls, box[:2], box[2:], 1, -1)
                elif kind == "fenetre":
                    d.rectangle(box, fill=GLASS, outline=GLASS_EDGE, width=2)
                    cv2.rectangle(walls, box[:2], box[2:], 1, -1)
                    if vertical:
                        d.line([(a[0], s0), (a[0], s1_)], fill=GLASS_EDGE, width=1)
                    else:
                        d.line([(s0, a[1]), (s1_, a[1])], fill=GLASS_EDGE, width=1)
                else:
                    doors.append((vertical, a[0] if vertical else a[1], s0, s1_, s1, s2, ins))
    # battants des portes : quart de cercle dans la plus petite des deux pièces voisines
    area = {}
    lab = np.zeros((H, W), np.int32)
    for i, p in enumerate(polys, 1):
        cv2.fillPoly(lab, [np.array(p, np.int32)], i)
        area[i] = cv2.contourArea(np.array(p, np.int32))
    for vertical, c, s0, s1_, q1, q2, ins in doors:
        w = s1_ - s0
        if w > 130:                               # grande ouverture (passage, baie) : pas de battant
            continue
        side = []
        for q, ok in zip((q1, q2), ins):
            if ok:
                side.append((area.get(lab[q[1], q[0]], 1e9), q))
        if not side:
            continue
        _, q = min(side)
        sgn = 1 if (q[0] - c if vertical else q[1] - c) > 0 else -1
        if vertical:
            hinge = (c, s0); end = (c + sgn * w, s0)
            d.line([hinge, end], fill=(90, 90, 90), width=3)
            bb = (c - w, s0 - w, c + w, s0 + w)
            d.arc(bb, 0 if sgn > 0 else 90, 90 if sgn > 0 else 180, fill=(150, 150, 150), width=2)
        else:
            hinge = (s0, c); end = (s0, c + sgn * w)
            d.line([hinge, end], fill=(90, 90, 90), width=3)
            bb = (s0 - w, c - w, s0 + w, c + w)
            d.arc(bb, 0 if sgn > 0 else 270, 90 if sgn > 0 else 360, fill=(150, 150, 150), width=2)
    for r, p in zip(rooms, polys):
        if r.get("label"):
            xs = [q[0] for q in p]; ys = [q[1] for q in p]
            xy = r.get("label_xy", ((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2))
            draw_label(d, xy, r["label"], r.get("size", 24))
    if out:
        img.save(out)
    return img, {r["name"]: p for r, p in zip(rooms, polys)}, walls.astype(bool)


def paths_json(job, rooms, polys, walls, start, order, clear_px=7, crop=(0, 0), scale=1.0, footprint=None):
    """paths.json pour la scène (coordonnées de plan.png = (x - crop) * scale)."""
    by = {r["name"]: r for r in rooms}
    fp = np.zeros(walls.shape, np.uint8)
    for p in polys.values():
        cv2.fillPoly(fp, [np.array(p, np.int32)], 1)
    fp = cv2.dilate(fp, np.ones((3, 3), np.uint8))
    if footprint is not None:
        fp = fp | footprint.astype(np.uint8)
    out, pos = [], tuple(start)
    tr = lambda q: [round((q[0] - crop[0]) * scale, 1), round((q[1] - crop[1]) * scale, 1)]
    for name in order:
        r = by[name]
        stop = tuple(r["stop"])
        try:
            path = shortest_path(walls, pos, stop, clear_px, footprint=fp)
        except ValueError as e:                     # signalé : à corriger (porte non détectée)
            print("ATTENTION", name, e); path = [list(pos), list(stop)]
        out.append({"name": name, "path": [tr(q) for q in path], "poly": [tr(q) for q in polys[name]]})
        pos = stop
    Path(job, "paths.json").write_text(json.dumps({"start": tr(start), "rooms": out}, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    return out


def run_job(here, src, ink, rooms, order, start, crop, wall_px=13, label_boxes=(), T=20, check=True, keep_src=False,
            **kw):
    """Chaîne complète d'un job : plan.png (recadré), paths.json, paths_check.png, meta.json (plan_px).
    keep_src : le plan source est déjà au style WooPlans (rendu réaliste) ; on garde l'image, on remplace les
    étiquettes et on recale seulement les pièces et les trajets."""
    from restyle import split_ink, footprint_of
    from relabel import erase_text
    here = Path(here)
    ink = ink.copy()
    for cx, cy, w, h in label_boxes:                 # étiquettes du plan source (centre, largeur, hauteur)
        ink[max(0, cy - h // 2):cy + h // 2, max(0, cx - w // 2):cx + w // 2] = False
    raw, _ = split_ink(ink, wall_px)
    if keep_src:
        img = src.convert("RGB")
        for cx, cy, w, h in label_boxes:
            img = erase_text(img, cx, cy, w // 2, h // 2, dark=120, maxh=h + 4, grow=3)
        from restyle import room_region, polygon
        fp = footprint_of(raw, kw.get("fp_close", 120)).astype(bool)
        for r in rooms:                         # extérieurs déclarés (véranda…) : dans l'emprise
            if "poly" in r:
                m = np.zeros(raw.shape, np.uint8); cv2.fillPoly(m, [np.array(r["poly"], np.int32)], 1); fp |= m.astype(bool)
        wall_fill = raw | ~fp                   # fenêtres (trous dans les murs de façade) : on ne sort pas
        for x0, y0, x1, y1 in kw.get("closures", ()):   # passages à fermer pour le remplissage (pièce ouverte)
            wall_fill[y0:y1, x0:x1] = True
        polys = {}
        for r in rooms:
            if "seed" in r:                   # pièce fermée : remplissage exact entre les murs
                try:
                    m = room_region(wall_fill, r["seed"], kw.get("close_px", 28), r.get("box"))
                except ValueError:
                    if "poly_fallback" not in r:
                        raise
                    m = np.zeros(raw.shape, bool)
                if m.mean() > 0.15:              # fuite probable : la pièce déborde sur ses voisines
                    print("ATTENTION fuite", r["name"], round(float(m.mean()), 2))
                fb = r.get("poly_fallback")
                if fb is not None:                # remplissage trop petit (porte non fermée, mur manquant) : position reportée
                    fa = cv2.contourArea(np.array(fb, np.float32))
                    if m.sum() < 0.45 * fa or m.sum() > 1.6 * fa:
                        print("  repli", r["name"], int(m.sum()), int(fa))
                        polys[r["name"]] = [tuple(q) for q in fb]; continue
                polys[r["name"]] = [tuple(q) for q in polygon(m, 4)]
            else:
                polys[r["name"]] = [tuple(q) for q in r["poly"]]
        d = ImageDraw.Draw(img)
        for r in rooms:
            if r.get("label"):
                xs = [q[0] for q in polys[r["name"]]]; ys = [q[1] for q in polys[r["name"]]]
                c = r.get("label_xy") or r.get("seed") or ((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2)
                draw_label(d, c, r["label"], r.get("size", 24))
        walls = raw.copy()
        for x0, y0, x1, y1 in kw.get("closures", ()):   # murs non détectés : fermés aussi pour le trajet
            walls[y0:y1, x0:x1] = True
        for x0, y0, x1, y1 in kw.get("openings", ()):   # portes mal détectées : ouvertes pour le trajet du point
            walls[y0:y1, x0:x1] = False
    else:
        img, polys, walls = redraw(src, ink, raw, rooms, T=T, **kw)
        fp = None
    img.crop(crop).save(here / "plan.png")
    out = paths_json(here, rooms, polys, walls, start, order, crop=crop[:2], footprint=fp)
    meta = json.loads((here / "meta.json").read_text(encoding="utf-8"))
    meta["plan_px"] = [crop[2] - crop[0], crop[3] - crop[1]]
    (here / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    if check:
        im = Image.open(here / "plan.png").convert("RGB"); d = ImageDraw.Draw(im, "RGBA")
        cols = [(240, 138, 46), (200, 0, 0), (0, 160, 0), (160, 0, 200), (0, 160, 160), (200, 120, 0), (255, 0, 120),
                (90, 90, 90), (0, 0, 0), (0, 120, 255), (120, 60, 0), (0, 90, 60)]
        for i, r in enumerate(out):
            c = cols[i % len(cols)]
            d.polygon([tuple(p) for p in r["poly"]], fill=c + (40,), outline=c + (255,))
            d.line([tuple(p) for p in r["path"]], fill=c + (255,), width=5)
        im.save(here / "paths_check.png")
    return polys


def blue_ink(src):
    a = np.asarray(src.convert("RGB")).astype(int)
    return ((a[..., 2] - a[..., 0]) > 60) | (a.mean(-1) < 150)
