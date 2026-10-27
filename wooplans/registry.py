"""Registre anti-doublon : une vidéo = (format, plan, angle). Refuse de produire deux fois la même."""
import hashlib
import json
from pathlib import Path
from typing import Dict, Optional

from wooplans.settings import ROOT

REGISTRY = ROOT / "registry" / "videos.json"


def _load(path: Path) -> Dict[str, dict]:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def key(fmt: str, plan_id: str, angle: str = "") -> str:
    return f"{fmt}:{plan_id}:{hashlib.sha1(angle.strip().lower().encode()).hexdigest()[:8] if angle else '-'}"


def claim(fmt: str, plan_id: str, angle: str = "", path: Optional[Path] = None) -> bool:
    """True si la vidéo est nouvelle (et l'inscrit) ; False si elle existe déjà."""
    path = path or REGISTRY
    data = _load(path)
    k = key(fmt, plan_id, angle)
    if k in data:
        return False
    data[k] = {"format": fmt, "plan": plan_id, "angle": angle, "etat": "reserve"}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def set_state(fmt: str, plan_id: str, etat: str, angle: str = "", path: Optional[Path] = None, **extra) -> None:
    path = path or REGISTRY
    data = _load(path)
    k = key(fmt, plan_id, angle)
    if k not in data:
        raise KeyError(k)
    data[k].update(etat=etat, **extra)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
