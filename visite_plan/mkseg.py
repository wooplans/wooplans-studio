"""Découpe la visite en segments rendus en parallèle (un job GitHub par segment).
usage: python mkseg.py jobs/<id> [pièces_par_segment]
Gère : visite sans 3D (segment CTA final), duplex (champ level, pièce « escalier » : switch_to / jump_to)."""
import json, sys
from pathlib import Path
job = Path(sys.argv[1]); per = int(sys.argv[2]) if len(sys.argv) > 2 else 2
paths = json.loads((job / "paths.json").read_text(encoding="utf-8"))
sync = json.loads((job / "sync.json").read_text(encoding="utf-8"))
items = {i["name"]: i for i in sync["items"]}
rooms = [r for r in paths["rooms"] if r["name"] in items]
segs, pos, t0, lvl = [], paths["start"], 0.0, 0
for k in range(0, len(rooms), per):
    grp = rooms[k:k + per]
    last = items[grp[-1]["name"]]
    t1 = round(last["zout_start"] + (0.9 if grp[-1].get("switch_to") is not None else (1.2 if last["zoom"] else 0.5)), 3)
    segs.append({"rooms": [r["name"] for r in grp], "t0": t0, "t1": t1, "start_pos": pos, "final": False, "level": lvl})
    for r in grp:                                   # duplex : une pièce « escalier » change de niveau
        if r.get("switch_to") is not None:
            lvl, pos = r["switch_to"], r["jump_to"]
    pos, t0 = (pos if grp[-1].get("switch_to") is not None else grp[-1]["path"][-1]), t1
segs.append({"rooms": [], "t0": t0, "t1": sync["total"], "start_pos": pos, "final": True, "level": lvl,
             "cta": "CTA" in items})
(job / "segments.json").write_text(json.dumps(segs, indent=1, ensure_ascii=False), encoding="utf-8")
print(len(segs), "segments:", [(s["t0"], s["t1"]) for s in segs])
