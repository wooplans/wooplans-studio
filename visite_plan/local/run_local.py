"""Rendu local d'un job (PC de Tao, secours). Le rendu normal se fait sur GitHub Actions (workflow visite-render).
usage: python run_local.py <dossier_job>      -> <job>/<id>.mp4"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import render_job
job = Path(sys.argv[1]).resolve()
render_job.local(job, job / f"{job.name}.mp4")
print("TERMINE", job / f"{job.name}.mp4", flush=True)
