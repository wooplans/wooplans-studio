"""Maquette 3D interactive de la Villa V3-003 à partir de l'outil MIT wy51ai/floorplan-3d.

Source des cotes : jobs/V3-003/plan.png (plan amélioré validé) et meta.json (10,60 m × 11,60 m).
Les murs sont relevés en pixels sur plan.png puis convertis en mm. Les surfaces affichées
sont les étiquettes du plan (PDF), jamais un calcul. Aucun prix.
Usage : python build_v3_003.py <chemin/vers/floorplan-3d/index.html> <sortie.html>
"""
import json, sys

# Contour extérieur sur plan.png (px) = 10,60 m × 11,60 m (meta.json)
PX0, PX1, PY0, PY1 = 94, 918, 88, 979
FRONT, DEPTH = 10600, 11600
def X(p): return round((p - PX0) * FRONT / (PX1 - PX0) / 10) * 10
def Y(p): return round((p - PY0) * DEPTH / (PY1 - PY0) / 10) * 10
def rect(x0, y0, x1, y1): return [X(x0), Y(y0), X(x1), Y(y1)]

# Murs [x0,y0,x1,y1] en px, type e = extérieur, n = intérieur
WALLS_PX = [
    # façade arrière (haut)
    (94, 88, 184, 107, 'e'), (302, 88, 471, 107, 'e'), (590, 88, 678, 107, 'e'),
    (660, 107, 678, 412, 'e'), (745, 182, 918, 197, 'e'),
    # côté droit
    (900, 197, 918, 255, 'e'), (900, 379, 918, 612, 'e'), (900, 743, 918, 868, 'e'),
    # façade avant (séjour)
    (488, 849, 510, 868, 'e'), (634, 849, 717, 868, 'e'), (834, 849, 900, 868, 'e'),
    # côté gauche + chambre P.
    (94, 107, 113, 410, 'e'), (94, 467, 113, 538, 'e'), (94, 591, 113, 979, 'e'),
    (113, 959, 184, 979, 'e'), (305, 959, 398, 979, 'e'), (379, 868, 398, 959, 'e'),
    # intérieur
    (378, 107, 395, 372, 'n'), (113, 372, 309, 388, 'n'), (466, 374, 660, 389, 'n'),
    (379, 482, 398, 868, 'n'), (523, 483, 830, 499, 'n'), (660, 483, 678, 499, 'n'),
    (298, 483, 308, 499, 'n'), (283, 446, 298, 566, 'n'), (113, 494, 283, 511, 'n'),
    (113, 620, 298, 637, 'n'),
]
# Fenêtres [x0,y0,x1,y1, allège m]
WINS_PX = [
    (184, 88, 302, 107, .9), (471, 88, 590, 107, .9), (900, 255, 918, 379, .9),
    (900, 612, 918, 743, .9), (510, 849, 634, 868, .9), (717, 849, 834, 868, .9),
    (94, 410, 113, 467, 1.4), (94, 538, 113, 591, 1.4), (184, 959, 305, 979, .9),
]
# Portes : ouverture (px), charnière (px), sens fermé, sens ouvert, nom
DOORS_PX = [
    ((398, 849, 488, 868), (398, 868), (1, 0), (0, 1), 'Porte d\'entrée', True),
    ((309, 372, 378, 388), (378, 372), (-1, 0), (0, -1), 'Porte chambre 2', False),
    ((395, 374, 466, 389), (395, 374), (1, 0), (0, -1), 'Porte chambre 3', False),
    ((660, 412, 678, 483), (678, 483), (0, -1), (1, 0), 'Porte cuisine', False),
    ((830, 483, 900, 499), (900, 483), (-1, 0), (0, -1), 'Porte séjour-cuisine', False),
    ((678, 182, 745, 197), (745, 182), (-1, 0), (0, -1), 'Porte terrasse 2', False),
    ((283, 388, 298, 446), (283, 388), (0, 1), (-1, 0), 'Porte SDB 2', False),
    ((283, 566, 298, 620), (283, 620), (0, -1), (-1, 0), 'Porte SDB 1', False),
    ((308, 483, 379, 499), (379, 499), (-1, 0), (0, 1), 'Porte chambre P.', False),
]
def R(x0, y0, x1, y1): return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
# Pièces : id, nom, polygone px, sol, position étiquette px, cotes du plan (PDF)
ROOMS_PX = [
    ('sejour', 'Salon + Salle à manger', [[398, 483], [523, 483], [523, 499], [900, 499], [900, 849], [398, 849]], 'tile800', (740, 820), '6,15 m × 4,35 m'),
    ('cuisine', 'Cuisine', R(678, 197, 900, 483), 'tile600', (730, 300), '3,65 m × 2,73 m'),
    ('couloir', 'Couloir', R(298, 389, 660, 483), 'tile800', (510, 425), '4,50 m × 1,20 m'),
    ('ch2', 'Chambre 2', R(113, 107, 378, 372), 'wood', (330, 215), '3,50 m × 3,40 m'),
    ('ch3', 'Chambre 3', R(395, 107, 660, 374), 'wood', (445, 215), '3,50 m × 3,27 m'),
    ('sdb2', 'SDB 2', R(113, 388, 283, 494), 'antislip', (230, 412), '2,20 m × 1,38 m'),
    ('sdb1', 'SDB 1', R(113, 511, 283, 620), 'antislip', (230, 582), '2,20 m × 1,38 m'),
    ('chp', 'Chambre P.', [[113, 637], [298, 637], [298, 499], [379, 499], [379, 959], [113, 959]], 'wood', (215, 690), '4,00 m × 3,40 m'),
    ('t1', 'Terrasse 1', R(398, 868, 918, 979), 'terrazzo', (560, 930), '6,30 m × 1,35 m'),
    ('t2', 'Terrasse 2', R(678, 96, 918, 182), 'terrazzo', (735, 145), '2,88 m × 1,20 m'),
]
# Mobilier (centre px, dimensions mm, rotation) d'après plan.png
FURN_PX = [
    ('bed', 'Lit 1,50 m', 195, 224, 1500, 2000, 270, '#d8c7b0'), ('nightstand', '床头柜', 130, 147, 450, 400, 270, None),
    ('nightstand', '床头柜', 130, 300, 450, 400, 270, None), ('wardrobe', '衣柜', 197, 352, 2000, 450, 180, None),
    ('bed', 'Lit 1,50 m', 563, 224, 1500, 2000, 90, '#b9c9a8'), ('nightstand', '床头柜', 642, 147, 450, 400, 90, None),
    ('nightstand', '床头柜', 642, 300, 450, 400, 90, None), ('wardrobe', '衣柜', 576, 352, 2000, 450, 180, None),
    ('bed', 'Lit 1,60 m', 205, 812, 1600, 2000, 270, '#b9c9a8'), ('nightstand', '床头柜', 130, 735, 450, 400, 270, None),
    ('nightstand', '床头柜', 130, 893, 450, 400, 270, None), ('wardrobe', '衣柜', 197, 655, 2000, 450, 0, None),
    ('shower', '淋浴区', 143, 442, 700, 1250, 0, None), ('toilet', '马桶', 192, 466, 400, 650, 180, None),
    ('vanity', '浴室柜', 248, 477, 550, 420, 180, None),
    ('shower', '淋浴区', 143, 566, 700, 1250, 0, None), ('toilet', '马桶', 192, 538, 400, 650, 0, None),
    ('vanity', '浴室柜', 248, 530, 550, 420, 0, None),
    ('sofa', '三人沙发', 511, 675, 2300, 850, 270, '#e9e4da'), ('sofa', '双人沙发', 675, 675, 2000, 800, 90, '#e9e4da'),
    ('rug', '地毯', 599, 678, 1100, 1800, 0, None), ('coffeetable', '茶几', 599, 678, 600, 1200, 0, None),
    ('armchair', '单人沙发', 594, 800, 750, 750, 180, '#e9e4da'), ('tvstand', '电视柜', 606, 518, 1800, 400, 0, None),
    ('table', '六人餐桌', 812, 668, 900, 1900, 0, None),
    ('chair', '餐椅', 770, 625, 450, 480, 270, None), ('chair', '餐椅', 770, 668, 450, 480, 270, None), ('chair', '餐椅', 770, 712, 450, 480, 270, None),
    ('chair', '餐椅', 855, 625, 450, 480, 90, None), ('chair', '餐椅', 855, 668, 450, 480, 90, None), ('chair', '餐椅', 855, 712, 450, 480, 90, None),
    ('counter', '橱柜台面', 828, 222, 1800, 600, 0, None), ('stove', '燃气灶', 805, 222, 750, 450, 0, None),
    ('counter', '橱柜台面', 874, 300, 1400, 600, 90, None), ('ksink', '水槽', 874, 295, 800, 450, 90, None),
    ('fridge', '冰箱', 874, 392, 700, 650, 90, None), ('island', '岛台', 805, 340, 900, 1800, 0, None),
    ('roundtable', '圆桌', 810, 140, 600, 600, 0, None), ('armchair', '休闲椅', 772, 140, 650, 650, 270, '#e9e4da'),
    ('armchair', '休闲椅', 848, 140, 650, 650, 90, '#e9e4da'),
    ('roundtable', '圆桌', 732, 925, 600, 600, 0, None), ('armchair', '休闲椅', 692, 925, 650, 650, 270, '#e9e4da'),
    ('armchair', '休闲椅', 772, 925, 650, 650, 90, '#e9e4da'),
    ('plant', '绿植', 434, 932, 500, 500, 0, None), ('plant', '绿植', 880, 940, 500, 500, 0, None),
    ('plant', '绿植', 712, 116, 500, 500, 0, None),
]

def js(v): return json.dumps(v, ensure_ascii=False)

def data_block():
    walls = [rect(*w[:4]) + [w[4]] for w in WALLS_PX]
    wins = [rect(*w[:4]) + [w[4]] for w in WINS_PX]
    doors = []
    for r, h, c, o, name, entry in DOORS_PX:
        rr = rect(*r)
        length = max(rr[2] - rr[0], rr[3] - rr[1])
        d = {'name': name, 'rect': rr, 'h': [X(h[0]), Y(h[1])], 'c': list(c), 'o': list(o), 'len': length}
        if entry: d['entry'] = True
        doors.append(d)
    rooms = [{'id': i, 'name': n, 'poly': [[X(x), Y(y)] for x, y in p], 'mat': m, 'at': [X(a[0]), Y(a[1])], 'dims': dm}
             for i, n, p, m, a, dm in ROOMS_PX]
    furn = ',\n  '.join(f"F({js(t)},{js(n)},{X(cx)},{Y(cy)},{w},{d},{r}{',' + js(c) if c else ''})"
                        for t, n, cx, cy, w, d, r, c in FURN_PX)
    return (f"const WALLS = {js(walls)};\nconst WINS = {js(wins)};\nconst DOORS = {js(doors)};\nconst SLIDES = [];\n"
            f"const R = (x0,y0,x1,y1) => [[x0,y0],[x1,y0],[x1,y1],[x0,y1]];\nconst ROOMS = {js(rooms)};\n"), furn

def sub(src, old, new, count=1):
    n = src.count(old)
    assert n == count, f'{n} occurrence(s) au lieu de {count} : {old[:70]!r}'
    return src.replace(old, new)

def cut(src, start, end, new):
    i = src.index(start); j = src.index(end, i)
    return src[:i] + new + src[j:]

def build(src):
    data, furn = data_block()
    src = cut(src, 'const WALLS = [', 'const MATS = {', data)
    src = cut(src, 'function defaultFurniture(){ return [', '\n];}', 'function defaultFurniture(){ return [\n  ' + furn)
    src = sub(src, "const STORE = 'huxing-design-v1';", "const STORE = 'wooplans-v3-003-v1';")
    src = sub(src, "LANGS.includes(l) ? l : 'zh'", "LANGS.includes(l) ? l : 'en'")
    src = sub(src, "const LANG_KEY = 'huxing-lang';", "const LANG_KEY = 'wooplans-lang';")
    src = sub(src, 'const BOUNDS = {x:-1850, y:-1750, w:15600, h:14100};', 'const BOUNDS = {x:-1700, y:-1600, w:14000, h:14900};')
    src = sub(src, 'const OX = 6000, OY = 5300,', f'const OX = {FRONT//2}, OY = {DEPTH//2},')
    # cotes : uniquement les deux cotes générales du PDF
    src = cut(src, '    chain(true,-750,0,[1580', "\n  g.setAttribute('display', ui.layers.dims",
              f'    chain(true,-750,0,[{FRONT}]) + chain(false,-800,0,[{DEPTH}]);')
    # entrée
    ex, ey = X(443), Y(979)
    src = cut(src, '  s += `<path d="M3350 8755H4350', "\n  $('#gOpen').innerHTML",
              f'  s += `<path d="M{ex} {ey+900}V{ey+50}M{ex-150} {ey+250}L{ex} {ey}L{ex+150} {ey+250}" fill="none" stroke="#b5653a" stroke-width="2" vector-effect="non-scaling-stroke"/>\n'
              f'        <text x="{ex+200}" y="{ey+700}" font-size="220" fill="#b5653a">${{tr(\'入户\',\'Entrée\')}}</text>`;')
    # 3D : allège par fenêtre, plus de baies
    src = sub(src, "const sill = i === 0 ? 1.4 : i >= 6 ? .45 : .9, head = 2.4;", "const sill = r[4] ?? .9, head = 2.4;")
    src = sub(src, ", [[10270,800,10510,2600], 2.4], [[10270,4260,10510,5740], 2.4]]", "]")
    # surfaces : étiquettes du plan (PDF), jamais calculées
    src = sub(src, '<text x="${x}" y="${y+260}" font-size="175" text-anchor="middle" fill="#7d7366" ${halo}>${fmt(area(r.poly))} m²</text>',
              '<text x="${x}" y="${y+260}" font-size="175" text-anchor="middle" fill="#7d7366" ${halo}>${r.dims}</text>')
    src = sub(src, '<td class="r">${fmt(area(r.poly))} m²</td></tr>`;', '<td class="r">${r.dims}</td></tr>`;')
    src = cut(src, '    <div class="total"><span>${tr(\'套内使用面积\'', '  <section><h3>${tr(\'方案统计\'',
              '    <div class="muted" style="font-size:11px;margin-top:4px">Cotes du plan Villa V3-003 (PDF WooPlans)</div></section>\n')
    src = sub(src, "<span>${nm(m.name)}<small>¥${m.price}/m²</small></span>", "<span>${nm(m.name)}</span>")
    src = cut(src, '      <div><small>${tr(\'使用面积\'', '    <div class="muted">${tr(`墙面面积',
              '      <div><small>Cotes (plan)</small><span class="big">${r.dims}</span></div></div>\n')
    src = cut(src, '    <div class="muted">${tr(`墙面面积', '  <section><h3>${tr(\'地面材料\'', '</section>\n')
    src = cut(src, '    <div class="total"><span>${tr(\'材料估价\'', '  <section><h3>${tr(\'房间内家具\'', '</section>\n')
    src = sub(src, '${esc(nm(state.rooms[r.id].name))}<small>${area(r.poly).toFixed(1)}m²</small>', '${esc(nm(state.rooms[r.id].name))}<small>${r.dims}</small>')
    src = sub(src, '<small>${area(r.poly).toFixed(2)} m²</small></button>`', '<small>${r.dims}</small></button>`')
    src = sub(src, "<small>${counted.reduce((a, r) => a + area(r.poly), 0).toFixed(2)} m²</small>", "<small>10,60 m × 11,60 m</small>")
    src = cut(src, "  $('#subtitle').textContent = tr(", "\n  $('#undo').disabled",
              "  $('#subtitle').textContent = 'Villa V3-003 · 3 chambres · 10,60 m × 11,60 m';")
    src = sub(src, "document.title = tr('户型装修设计', 'Floor Plan Designer');", "document.title = 'WooPlans · Villa V3-003 en 3D';")
    src = sub(src, '<html lang="zh-CN">', '<html lang="fr">')
    src = sub(src, '<title>户型装修设计</title>', '<title>Villa V3-003 en 3D</title>')
    src = sub(src, '<b data-en="3BR 2LR 2BA · Interior Design">三室两厅两卫 · 装修设计</b>', '<b data-en="WooPlans · Villa V3-003">WooPlans · Villa V3-003</b>')
    return src

if __name__ == '__main__':
    src = open(sys.argv[1], encoding='utf-8').read()
    out = build(src)
    open(sys.argv[2], 'w', encoding='utf-8').write(out)
    print('ok', sys.argv[2], len(out))
