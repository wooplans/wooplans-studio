"""Nettoie le fond d'un plan (herbe, feuilles, filigrane posé dessus) : remplissage depuis les bords
de tous les pixels non blancs, arrêté par la marge blanche ou les murs du plan."""
import numpy as np
from collections import deque


def flood_white(a, white=215):
    h, w = a.shape[:2]
    cand = ~(a.min(-1) > white)
    seen = np.zeros((h, w), bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if cand[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if cand[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and cand[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True; q.append((ny, nx))
    out = a.copy(); out[seen] = 255
    return out, seen
