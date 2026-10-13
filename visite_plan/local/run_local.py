"""Rendu local rapide d'un job : segments en parallèle puis assemblage.
usage: python run_local.py <dossier_job>   (contient plan.png, facade.png, segments.json, ...)"""
import json, os, subprocess, sys, shutil, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
HERE = Path(__file__).resolve().parent
VP = HERE / "visite_plan"
job = Path(sys.argv[1]).resolve()
segs = json.loads((job / "segments.json").read_text(encoding="utf-8"))
work = job / "_work"; segdir = work / "segs"; segdir.mkdir(parents=True, exist_ok=True)
t0 = time.time()
def render(k):
    env = dict(os.environ, JOB=str(job), SEG=str(k))
    subprocess.run(["manimgx","render","scene_visite.py","VisitePlan","-r","1080x1920","--fps","30","--preset","veryfast","--crf","18",
                    "-o",str(segdir / f"seg{k}.mp4")], cwd=VP, env=env, check=True)
    print(f"segment {k} ok ({time.time()-t0:.0f}s)", flush=True)
workers = max(1, min(len(segs), (os.cpu_count() or 4) // 2))
with ThreadPoolExecutor(workers) as ex:
    list(ex.map(render, range(len(segs))))
out = job / f"{job.name}.mp4"
subprocess.run([sys.executable, str(VP / "assemble.py"), str(job), str(segdir), str(out)], cwd=work, check=True)
print(f"TERMINE {out} en {time.time()-t0:.0f}s", flush=True)
