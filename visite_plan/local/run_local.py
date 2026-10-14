"""Rendu local rapide d'un job : segments en parallèle puis assemblage.
usage: python run_local.py <dossier_job>   (contient plan.png, facade.png, segments.json, ...)"""
import json, os, subprocess, sys, shutil, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
HERE = Path(__file__).resolve().parent
VP = HERE / "visite_plan"
job = Path(sys.argv[1]).resolve()
if (job / "bump.json").exists():          # hook / estimation / CTA (+ corps)
    sys.path.insert(0, str(HERE)); import bump_local; bump_local.run(job, VP); sys.exit(0)

if (job / "DIAG").exists():
    rep = job / "diag.txt"; lines = []
    import platform
    lines.append(f"cpu_count={os.cpu_count()} machine={platform.machine()}")
    try:
        r = subprocess.run(["powershell","-NoProfile","-Command",
          "Get-CimInstance Win32_VideoController | Select Name,DriverVersion | Format-List; Get-CimInstance Win32_Processor | Select Name,NumberOfCores,NumberOfLogicalProcessors | Format-List; (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB"],capture_output=True,text=True)
        lines.append(r.stdout)
    except Exception as e: lines.append(str(e))
    for k in (4,):
        t1 = time.time()
        env = dict(os.environ, JOB=str(job), SEG=str(k))
        subprocess.run(["manimgx","render","scene_visite.py","VisitePlan","-r","1080x1920","--fps","30","--preset","veryfast","--crf","18","-o",str(job/"diag_seg.mp4")], cwd=VP, env=env)
        lines.append(f"segment {k} seul : {time.time()-t1:.0f}s")
    rep.write_text("\n".join(lines), encoding="utf-8")
    sys.exit(0)
segs = json.loads((job / "segments.json").read_text(encoding="utf-8"))
work = job / "_work"; segdir = work / "segs"; segdir.mkdir(parents=True, exist_ok=True)
t0 = time.time()
def render(k):
    env = dict(os.environ, JOB=str(job), SEG=str(k))
    subprocess.run(["manimgx","render","scene_visite.py","VisitePlan","-r","1080x1920","--fps","30","--preset","veryfast","--crf","18",
                    "-o",str(segdir / f"seg{k}.mp4")], cwd=VP, env=env, check=True)
    print(f"segment {k} ok ({time.time()-t0:.0f}s)", flush=True)
workers = max(1, min(len(segs), 2))
with ThreadPoolExecutor(workers) as ex:
    list(ex.map(render, range(len(segs))))
out = job / f"{job.name}.mp4"
subprocess.run([sys.executable, str(VP / "assemble.py"), str(job), str(segdir), str(out)], cwd=work, check=True)
print(f"TERMINE {out} en {time.time()-t0:.0f}s", flush=True)
