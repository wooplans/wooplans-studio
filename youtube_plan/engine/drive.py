"""Rendu des chunks (240 images) en parallèle.
  YT_JOB=<job> python drive.py list                      -> JSON [[seq,f0,f1],...]
  YT_JOB=<job> python drive.py run [--shard i --of N] [--workers 4]
"""
import sys, os, json, subprocess, argparse, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import D, FPS, ORDER, OUTDIR
CH = 240
HERE = os.path.dirname(os.path.abspath(__file__))
jobs = []
for k in ORDER:
    if k in ('jingle', 'catalogue'): continue
    n = int(round(D[k] * FPS))
    for f0 in range(0, n, CH): jobs.append((k, f0, min(f0 + CH, n)))
ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--shard', type=int, default=0); ap.add_argument('--of', type=int, default=1); ap.add_argument('--workers', type=int, default=2)
a = ap.parse_args()
if a.cmd == 'list':
    print(json.dumps(jobs)); sys.exit()
mine = [j for i, j in enumerate(jobs) if i % a.of == a.shard]
todo = [j for j in mine if not os.path.exists(f'{OUTDIR}/{j[0]}_{j[1]:05d}.mp4')]
print('todo', len(todo), 'of', len(mine), flush=True)
running = []; fail = 0
while todo or running:
    still = []
    for p, j in running:
        if p.poll() is None: still.append((p, j))
        elif p.returncode != 0: fail += 1; print('FAIL', j, p.stderr.read()[-400:], flush=True)
    running = still
    while todo and len(running) < a.workers:
        j = todo.pop(0)
        running.append((subprocess.Popen([sys.executable, HERE + '/run_chunk.py', j[0], str(j[1]), str(j[2])], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=os.environ), j))
    time.sleep(0.5)
sys.exit(1 if fail else 0)
