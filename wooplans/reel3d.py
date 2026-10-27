"""Format « rendus 3D en vidéo » : Reel 9:16 de ~24 s fait des rendus du catalogue, musique de fond, sans voix off.

Logique pure (aucun réseau, ni ffmpeg) : calendrier calé sur les mesures de la musique, textes à l'écran
(`check_copy` appliqué), sous-titres ASS animés (pop, mot clé orange, prix qui s'incrémente), filigranes qui défilent.
Le rendu ffmpeg est dans tools/make_reel.py.

Règles du projet : chiffres uniquement ceux de data/plans.json (chambres, surface, terrain, estimation indicative),
prix actuel du catalogue 39 000 FCFA, jamais de formule d'urgence, lien wooplans.com dans la fin de vidéo.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from wooplans.guardrails import check_copy
from wooplans.settings import OFFER_PRICE_FCFA

W, H = 1080, 1920
FPS = 30
OVERLAP = 0.20                                 # durée du fondu entre deux plans (s)
BEATS_PER_BAR = 4
CAP_DY = 0                                   # textes décalés vers le bas pour laisser voir le plan
ORANGE, GREEN, WHITE = "&H2E8AF0&", "&H595B0F&", "&HFFFFFF&"      # ASS : BGR (orange #F08A2E, vert #0F5B59)


def fcfa(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def bar_length(tempo: float) -> float:
    return BEATS_PER_BAR * 60.0 / tempo


@dataclass
class Line:
    text: str                                  # texte brut (les mots entre * * sont en orange)
    size: int = 104
    y: int = 1060
    delay: float = 0.0                         # décalage dans la scène (s)


@dataclass
class Scene:
    bar: int                                   # mesure de départ
    bars: int = 1
    lines: List[Line] = field(default_factory=list)
    count_to: Optional[int] = None             # prix qui s'incrémente jusqu'à cette valeur (ligne marquée « {n} »)
    end_card: bool = False


def scenes(plan: dict) -> List[Scene]:
    """Scénario : accroche, type, surface, terrain (si connu), plan + devis, suspense, prix, catalogue, carte finale."""
    cat = plan["category"].upper()
    ch = plan["bedrooms"]
    lv = "DE PLAIN-PIED" if plan["levels"] == 1 else f"SUR {plan['levels']} NIVEAUX"
    Y1, Y2 = 1260, 1415                           # tout le texte dans la zone sous l'image : un seul fond
    out = [
        Scene(0, 1, [Line("CETTE MAISON", y=Y1, size=136), Line("COÛTE *COMBIEN* ?", y=Y2, size=136, delay=0.6)]),
        Scene(1, 1, [Line(cat, y=Y1, size=140), Line(f"*{ch}* CHAMBRES", y=Y2, size=136, delay=0.6)]),
        Scene(2, 1, [Line(f"*{plan['surface']} m²*", y=Y1, size=172), Line(lv, y=Y2, size=120, delay=0.6)]),
    ]
    if plan.get("land_area"):
        out.append(Scene(len(out), 1, [Line("TERRAIN PRÉVU", y=Y1, size=118), Line(f"*{plan['land_area']} m²*", y=Y2, size=168, delay=0.6)]))
    b = len(out)
    out += [
        Scene(b, 1, [Line("PLAN COMPLET", y=Y1, size=134), Line("+ *DEVIS* DÉTAILLÉ", y=Y2, size=124, delay=0.6)]),
        Scene(b + 1, 1, [Line("ET LE *BUDGET*", y=Y1, size=136), Line("POUR CONSTRUIRE ?", y=Y2, size=122, delay=0.6)]),
        Scene(b + 2, 2, [Line("ESTIMATION", y=1205, size=80), Line("{n}", y=1315, size=170, delay=0.0),
                         Line("FCFA", y=1420, size=96), Line("estimation indicative", y=1495, size=48, delay=1.3)],
              count_to=plan["estimate_total"]),
        Scene(b + 4, 1, [Line("TOUT EST DANS LE", y=Y1, size=108), Line("*CATALOGUE PREMIUM*", y=Y2, size=118, delay=0.6)]),
        Scene(b + 5, 1, [], end_card=True),
    ]
    return out


def n_bars(sc: List[Scene]) -> int:
    return max(s.bar + s.bars for s in sc)


def all_texts(sc: List[Scene], plan: dict) -> List[str]:
    return [l.text.replace("*", "").replace("{n}", fcfa(plan["estimate_total"])) + (" FCFA" if "{n}" in l.text else "")
            for s in sc for l in s.lines]


def check_scenes(sc: List[Scene], plan: dict) -> List[str]:
    """Garde-fous : texte à l'écran sans formule d'urgence ni montant non sourcé."""
    problems = []
    for t in all_texts(sc, plan):
        problems += check_copy(t, [plan["estimate_total"]])
    return problems


# ---------- images ----------

def image_mode(size: Tuple[int, int]) -> str:
    """« cover » : carré ou presque et assez grand pour remplir un écran vertical ; sinon « blurpad » (fond flou)."""
    w, h = size
    return "cover" if 0.8 <= w / h <= 1.25 and min(w, h) >= 1500 else "blurpad"


def assign_images(n_scenes: int, sizes: List[Tuple[int, int]]) -> List[Tuple[int, str]]:
    """Image (indice, mode) de chaque mesure. Les rendus plein écran (cover) d'abord, repris en boucle s'il y en a
    au moins 3 ; les images au format paysage (fond flou) ne servent que s'il n'y a pas assez de rendus carrés."""
    covers = [i for i, s in enumerate(sizes) if image_mode(s) == "cover"]
    others = [i for i, s in enumerate(sizes) if image_mode(s) != "cover"]
    order = covers if len(covers) >= 3 else covers + others
    if not order:
        raise ValueError("aucun rendu")
    return [(order[k % len(order)], image_mode(sizes[order[k % len(order)]])) for k in range(n_scenes)]


def pan(k: int) -> Tuple[float, float]:
    """Travelling horizontal : de gauche à droite, puis de droite à gauche (part de la zone visible, jamais hors image)."""
    return (0.15, 0.85) if k % 2 == 0 else (0.85, 0.15)


# ---------- sous-titres ASS ----------

def ts(t: float) -> str:
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def _runs(text: str, base: str) -> str:
    """Les mots entre * * passent en orange."""
    parts = text.split("*")
    return "".join((f"{{\\c{ORANGE}}}" if i % 2 else f"{{\\c{base}}}") + p for i, p in enumerate(parts) if p)


def _pop(dur_ms: int) -> str:
    return ("\\an5\\fscx55\\fscy55\\alpha&HFF&\\t(0,130,\\fscx112\\fscy112\\alpha&H00&)\\t(130,240,\\fscx100\\fscy100)"
            f"\\t({max(300, dur_ms - 140)},{dur_ms},\\alpha&HFF&)")


def count_steps(target: int, steps: int = 14) -> List[int]:
    """Valeurs successives du compteur (ralentit vers la fin), la dernière est exactement la cible."""
    vals = [int(round(target * (1 - (1 - (i + 1) / steps) ** 3), -3)) for i in range(steps)]
    vals[-1] = target
    return vals


def build_ass(sc: List[Scene], plan: dict, bar_s: float, total: float) -> str:
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Cap,Poppins,104,{WHITE},{WHITE},{GREEN},&H90000000&,-1,0,0,0,100,100,1,0,1,12,4,5,40,40,0,1
Style: WM,Poppins,58,&H80595B0F,&H80595B0F,&HA0FFFFFF,&HFF000000,-1,0,0,0,100,100,2,0,1,3,0,5,0,0,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    ev = []
    for s in sc:
        t0 = s.bar * bar_s + 0.05
        t1 = (s.bar + s.bars) * bar_s - 0.10
        for l in s.lines:
            a, dur_ms = t0 + l.delay, int((t1 - t0 - l.delay) * 1000)
            if dur_ms < 400:
                continue
            fs = f"\\fs{l.size}"
            if "{n}" in l.text:                                # prix qui s'incrémente puis se fige
                vals = count_steps(s.count_to)
                dt = 0.065
                for j, v in enumerate(vals[:-1]):
                    ev.append(f"Dialogue: 1,{ts(a + j * dt)},{ts(a + (j + 1) * dt)},Cap,,0,0,0,,"
                              f"{{\\an5\\pos({W // 2},{l.y + CAP_DY}){fs}\\c{ORANGE}}}{fcfa(v)}")
                a2 = a + (len(vals) - 1) * dt
                ev.append(f"Dialogue: 1,{ts(a2)},{ts(t1)},Cap,,0,0,0,,"
                          f"{{\\pos({W // 2},{l.y + CAP_DY}){fs}\\an5\\c{ORANGE}\\fscx118\\fscy118\\t(0,180,\\fscx100\\fscy100)"
                          f"\\t({max(300, int((t1 - a2) * 1000) - 140)},{int((t1 - a2) * 1000)},\\alpha&HFF&)}}{fcfa(vals[-1])}")
                continue
            ev.append(f"Dialogue: 1,{ts(a)},{ts(t1)},Cap,,0,0,0,,{{\\pos({W // 2},{l.y + CAP_DY}){fs}{_pop(dur_ms)}}}{_runs(l.text, WHITE)}")
    # filigrane anti-piratage : « wooplans.com » semi-transparent qui défile, du début à la fin
    k, a = 0, 0.3
    while a < total:
        y = (380, 1000, 700)[k % 3]
        ev.append(f"Dialogue: 0,{ts(a)},{ts(min(a + 7, total))},WM,,0,0,0,,{{\\move(1500,{y},-420,{y})}}wooplans.com")
        a += 4.5
        k += 1
    return head + "\n".join(ev) + "\n"
