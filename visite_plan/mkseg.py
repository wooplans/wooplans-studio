"""Découpe la visite en segments rendus en parallèle (un job GitHub par segment).
usage: python mkseg.py jobs/<id> [pièces_par_segment]"""
import json, sys
from pathlib import Path
job = Path(sys.argv[1]); per = int(sys.argv[2]) if len(sys.argv) > 2 else 2
paths = json.loads((job / "paths.json").read_text(encoding="utf-8"))
sync = json.loads((job / "sync.json").read_text(encoding="utf-8"))
items = {i["name"]: i for i in sync["items"]}
rooms = [r for r in paths["rooms"]]
segs, pos, t0 = [], paths["start"], 0.0
for k in range(0, len(rooms), per):
    grp = rooms[k:k + per]
    last = items[grp[-1]["name"]]
    t1 = round(last["zout_start"] + (1.2 if last["zoom"] else 0.5), 3)
    segs.append({"rooms": [r["name"] for r in grp], "t0": t0, "t1": t1, "start_pos": pos, "final": False})
    pos, t0 = grp[-1]["path"][-1], t1
segs.append({"rooms": [], "t0": t0, "t1": sync["total"], "start_pos": pos, "final": True})
(job / "segments.json").write_text(json.dumps(segs, indent=1, ensure_ascii=False), encoding="utf-8")
print(len(segs), "segments:", [(s["t0"], s["t1"]) for s in segs])
