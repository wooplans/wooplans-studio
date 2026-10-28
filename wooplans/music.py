"""Musiques des vidéos : base Mixkit (assets/music/library.json), téléchargement à la demande, rotation.

Une musique se désigne par « mixkit:<id> » (titre de la base) ou par un chemin assets/music/<fichier>.mp3.
Le tempo de chaque fichier est dans assets/music/tracks.json (tools/analyze_music.py, librosa, hors rendu).
Rotation : pick() prend, parmi les titres sélectionnés (use=true) déjà analysés, le moins utilisé par les shorts
déjà rendus (shorts/out/*.json) ; à égalité, un tirage stable propre au job. Ainsi deux shorts d'affilée n'ont
jamais la même musique tant que la base n'est pas épuisée.
"""
import hashlib
import json
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Optional

from wooplans.settings import ROOT

MUSIC = ROOT / "assets" / "music"
LIB = MUSIC / "library.json"
TRACKS = MUSIC / "tracks.json"
SHORTS_OUT = ROOT / "shorts" / "out"


def library() -> list:
    return json.loads(LIB.read_text(encoding="utf-8"))["tracks"] if LIB.exists() else []


def tracks() -> dict:
    return json.loads(TRACKS.read_text(encoding="utf-8")) if TRACKS.exists() else {}


def file_name(mid: int) -> str:
    """Nom du fichier local d'un titre Mixkit (les anciens fichiers nommés « ..._mixkit-<id>.mp3 » sont repris)."""
    for f in sorted(MUSIC.glob(f"*mixkit-{mid}.mp3")):
        return f.name
    return f"mixkit-{mid}.mp3"


def ensure_file(mid: int) -> Path:
    """Fichier mp3 du titre, téléchargé depuis assets.mixkit.co s'il manque."""
    path = MUSIC / file_name(mid)
    if not path.exists():
        req = urllib.request.Request(f"https://assets.mixkit.co/music/{mid}/{mid}.mp3", headers={"User-Agent": "Mozilla/5.0"})
        path.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    return path


def resolve(spec: str) -> Path:
    """« mixkit:<id> » ou chemin relatif au dépôt → fichier mp3 local."""
    if spec.startswith("mixkit:"):
        return ensure_file(int(spec.split(":", 1)[1]))
    return ROOT / spec


def usage() -> Counter:
    """Nombre de shorts déjà rendus par musique (journal shorts/out/<job>.json écrit par tools/make_short.py)."""
    used = Counter()
    for f in SHORTS_OUT.glob("*.json"):
        try:
            used[json.loads(f.read_text(encoding="utf-8"))["music"]] += 1
        except (ValueError, KeyError):
            continue
    return used


def pick(job: str, used: Optional[Counter] = None) -> str:
    """Musique d'un nouveau short : le titre sélectionné le moins utilisé (tirage stable à égalité)."""
    analysed = tracks()
    pool = [f"mixkit:{t['id']}" for t in library() if t.get("use") and file_name(t["id"]) in analysed]
    if not pool:
        raise RuntimeError("aucune musique sélectionnée et analysée (assets/music/library.json + tracks.json)")
    used = usage() if used is None else used
    return min(pool, key=lambda s: (used[s], hashlib.sha1(f"{job}|{s}".encode()).hexdigest()))


def describe(spec: str) -> dict:
    """Titre et artiste (pour le journal et la description des publications)."""
    if spec.startswith("mixkit:"):
        mid = int(spec.split(":", 1)[1])
        t = next((t for t in library() if t["id"] == mid), {})
        return {"music": spec, "title": t.get("title", ""), "artist": t.get("artist", ""),
                "source": f"https://mixkit.co/free-stock-music/ (id {mid})"}
    return {"music": spec, "title": Path(spec).stem, "artist": "", "source": "assets/music"}
