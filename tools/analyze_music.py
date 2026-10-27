"""Analyse une musique de assets/music/ (une seule fois, hors rendu) et écrit assets/music/tracks.json :
tempo régulier (intervalle entre temps), position d'un temps fort, et fenêtre la plus énergique.
Le rendu des vidéos lit ce JSON : pas besoin de librosa au moment du rendu (GitHub Actions).

  pip install librosa
  python tools/analyze_music.py assets/music/C_Pop-Two_Grigoriy-Nuzhny_mixkit-697.mp3 [fenetre_s=26]
"""
import json
import sys
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parents[1] / "assets" / "music" / "tracks.json"


def analyze(path: Path, window: float = 26.0) -> dict:
    import librosa
    y, sr = librosa.load(str(path), sr=22050)
    _, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
    rms = librosa.feature.rms(y=y)[0]
    t = librosa.times_like(rms, sr=sr)
    best, best_t = -1.0, 0.0
    for st in np.arange(0, len(y) / sr - window, 1.0):                # fenêtre la plus énergique
        m = (t >= st) & (t < st + window)
        e = float(rms[m].mean())
        if e > best:
            best, best_t = e, float(st)
    # grille régulière ajustée (moindres carrés) sur les temps détectés DANS la fenêtre : le tempo global dérive
    w = beats[(beats >= best_t) & (beats <= best_t + window)]
    k = np.round((w - w[0]) / np.median(np.diff(w)))
    interval, first = np.polyfit(k, w, 1)
    drift = float(np.max(np.abs(w - (first + k * interval))))
    n = int(np.ceil((best_t - first) / interval))
    start = float(first + n * interval)
    beats = np.array([first])
    return {"file": path.name, "duration": round(len(y) / sr, 2), "beat_interval": round(float(interval), 4),
            "bpm": round(60 / interval, 1), "max_drift_s": round(drift, 3), "window_s": window,
            "best_start": round(start, 3)}


if __name__ == "__main__":
    f = Path(sys.argv[1])
    info = analyze(f, float(sys.argv[2]) if len(sys.argv) > 2 else 26.0)
    data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    data[f.name] = info
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(info, ensure_ascii=False))
