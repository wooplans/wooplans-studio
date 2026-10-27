"""Rendu local de la variante « visite sans 3D » : corps (segments) + hook + CTA + bande basse + filigranes.
Appelé par run_local.py quand le job contient nf.json. Ne touche pas au pipeline standard."""
import json, os, subprocess, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import bump_local as BL

ff, ENC = BL.ff, BL.ENC


def run(job: Path, VP: Path):
    B = json.loads((job / "bump.json").read_text(encoding="utf-8"))
    segs = json.loads((job / "segments.json").read_text(encoding="utf-8"))
    sync = json.loads((job / "sync.json").read_text(encoding="utf-8"))
    work = job / "_work"; segdir = work / "segs"; segdir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    def render_seg(k):
        out = segdir / f"seg{k}.mp4"
        if out.exists():
            return
        env = dict(os.environ, JOB=str(job), SEG=str(k))
        subprocess.run(["manimgx", "render", "scene_visite_nf.py", "VisitePlan", "-r", "1080x1920", "--fps", "30",
                        "--preset", "veryfast", "--crf", "18", "-o", str(out)], cwd=VP, env=env, check=True)
        print(f"segment {k} ok ({time.time()-t0:.0f}s)", flush=True)

    def render_part(part):
        out = work / f"{part}_raw.mp4"
        if out.exists():
            return
        env = dict(os.environ, JOB=str(job))
        subprocess.run(["manimgx", "render", "scene_bumpers_nf.py", {"hook": "HookNF", "cta": "CtaNF"}[part],
                        "-r", "1080x1920", "--fps", "30", "--preset", "veryfast", "--crf", "18", "-o", str(out)],
                       cwd=VP, env=env, check=True)
        print(f"{part} ok ({time.time()-t0:.0f}s)", flush=True)

    tasks = [lambda k=k: render_seg(k) for k in range(len(segs))] + [lambda p=p: render_part(p) for p in ("hook", "cta")]
    with ThreadPoolExecutor(2) as ex:           # 2 rendus simultanés maximum (7,7 Go de RAM)
        list(ex.map(lambda f: f(), tasks))

    # ---- corps muet : segments recalés à 30 fps puis concaténés
    tmp = work / "seg_cfr"; tmp.mkdir(exist_ok=True)
    lines = []
    for k, s in enumerate(segs):
        dst = tmp / f"c{k}.mp4"
        ff("-i", segdir / f"seg{k}.mp4", "-vf", "fps=30,tpad=stop_mode=clone:stop_duration=2", "-t", f"{s['t1'] - s['t0']:.3f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-an", dst)
        lines.append(f"file '{dst.resolve().as_posix()}'")
    (work / "concat_body.txt").write_text("\n".join(lines), encoding="utf-8")
    ff("-f", "concat", "-safe", "0", "-i", work / "concat_body.txt", "-c", "copy", job / "body_silent.mp4")
    print(f"corps muet ok ({time.time()-t0:.0f}s)", flush=True)

    parts = {}
    for part in ("hook", "cta"):
        dst = work / f"{part}.mp4"
        ff("-i", work / f"{part}_raw.mp4", "-i", job / f"{part}.m4a", "-vf", "fps=30,tpad=stop_mode=clone:stop_duration=3",
           "-af", "apad", "-t", f"{B[part]['total']:.3f}", *ENC, dst)
        parts[part] = dst
    parts["body"] = BL.build_body(job, B, work, VP)
    lst = work / "concat_final.txt"
    lst.write_text("\n".join(f"file '{parts[p].resolve().as_posix()}'" for p in ("hook", "body", "cta")), encoding="utf-8")
    mid = work / "mid.mp4"
    ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", mid)

    # ---- marque : filigrane mosaïque, logo mobile, adresse du site (zone sûre)
    hook_t = B["hook"]["total"]
    fin_start = next(i for i in sync["items"] if i["name"] == "Final")["start"]
    t_badge0 = B["hook"]["cues"]["dot"] + 0.2
    t_badge1 = hook_t + fin_start
    out = job / f"{job.name}.mp4"
    # filigrane : mosaïque très discrète + 2 logos semi-transparents qui se promènent sur tout l'écran, du début à la fin
    fc = ("[2:v]format=rgba,scale=390:-1,colorchannelmixer=aa=0.62[w1];"
          "[3:v]format=rgba,scale=390:-1,colorchannelmixer=aa=0.62[w2];"
          "[0:v][1:v]overlay=0:0[a];"
          "[a][w1]overlay=x='(W-w)*(0.5+0.5*sin(0.53*t))':y='(H-h)*(0.5+0.5*sin(0.37*t+1.1))'[b];"
          "[b][w2]overlay=x='(W-w)*(0.5+0.5*sin(0.41*t+2.6))':y='(H-h)*(0.5+0.5*sin(0.29*t+4.0))'[c];"
          f"[c][5:v]overlay=28:170:enable='between(t,{t_badge0:.3f},{t_badge1:.3f})'[v]")
    ff("-i", mid, "-i", job / "wm_tile.png", "-i", job / "wm_logo.png", "-i", job / "wm_logo.png",
       "-i", job / "wm_logo.png", "-i", job / "badge_url.png", "-filter_complex", fc, "-map", "[v]", "-map", "0:a",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "copy",
       "-metadata", "comment=© WooPlans - wooplans.com", "-metadata", "copyright=© WooPlans", out)
    print(f"TERMINE {out} en {time.time()-t0:.0f}s", flush=True)
