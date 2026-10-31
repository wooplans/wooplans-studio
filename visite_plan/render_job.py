"""Point d'entrée UNIQUE du rendu d'un job de visite (GitHub Actions ET PC de Tao).

  python visite_plan/render_job.py plan  visite_plan/jobs/<id>            -> JSON {"mode", "include":[...]} (matrice GitHub Actions)
  python visite_plan/render_job.py build visite_plan/jobs/<id> <parts> <sortie.mp4>
        <parts> = dossier contenant les morceaux déjà rendus : seg<k>.mp4, hook_raw.mp4, estim_raw.mp4, cta_raw.mp4
  python visite_plan/render_job.py local visite_plan/jobs/<id> <sortie.mp4>   (rend tout en local : 2 rendus simultanés)

Trois modes, détectés dans le dossier du job :
  - nf.json    : « visite sans 3D » avec hook + CTA  (scene_visite_nf.py + scene_bumpers_nf.py + bump_local_nf.py)
  - bump.json  : visite AVEC 3D : hook + estimation + CTA  (scene_visite.py + scene_bumpers.py + bump_local.py)
  - sinon      : visite simple / « sans 3D » format cloud (scene_visite.py, segment CTA éventuel, assemble.py)
Les fichiers de marque communs (assets/brand, musique) sont copiés dans le job s'ils n'y sont pas déjà.
"""
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

VP = Path(__file__).resolve().parent
ROOT = VP.parent
sys.path.insert(0, str(VP))

BRAND = ["logo_white.png", "band_bottom.png", "badge_url.png", "wm_logo.png", "wm_tile.png"]
MUSIC = ROOT / "assets" / "music" / "C_Pop-Two_Grigoriy-Nuzhny_mixkit-697.mp3"


def mode_of(job: Path) -> str:
    if (job / "nf.json").exists():
        return "nf"
    if (job / "bump.json").exists():
        return "bump"
    return "std"


def plan(job: Path) -> dict:
    segs = json.loads((job / "segments.json").read_text(encoding="utf-8"))
    mode = mode_of(job)
    seg_scene = "scene_visite_nf.py" if mode == "nf" else "scene_visite.py"
    inc = [{"part": f"seg{k}", "scene": seg_scene, "cls": "VisitePlan", "seg": str(k)} for k in range(len(segs))]
    if mode == "bump":
        inc += [{"part": f"{p}_raw", "scene": "scene_bumpers.py", "cls": c, "seg": ""}
                for p, c in (("hook", "HookScene"), ("estim", "EstimScene"), ("cta", "CtaScene"))]
    elif mode == "nf":
        inc += [{"part": f"{p}_raw", "scene": "scene_bumpers_nf.py", "cls": c, "seg": ""}
                for p, c in (("hook", "HookNF"), ("cta", "CtaNF"))]
    return {"mode": mode, "include": inc}


def prepare_assets(job: Path) -> None:
    for name in BRAND:
        if not (job / name).exists():
            shutil.copy(ROOT / "assets" / "brand" / name, job / name)
    if mode_of(job) != "std" and not (job / "music.mp3").exists() and MUSIC.exists():
        shutil.copy(MUSIC, job / "music.mp3")


def place_parts(job: Path, parts: Path) -> None:
    """Dépose les morceaux rendus là où bump_local* les attend (ils sautent un rendu déjà présent)."""
    work = job / "_work"; segdir = work / "segs"; segdir.mkdir(parents=True, exist_ok=True)
    for f in parts.glob("*.mp4"):
        dst = segdir / f.name if f.name.startswith("seg") else work / f.name
        shutil.copy(f, dst)


def build(job: Path, parts: Path | None, out: Path) -> None:
    mode = mode_of(job)
    prepare_assets(job)
    if parts is not None:
        place_parts(job, parts)
    if mode == "nf":
        import bump_local_nf
        bump_local_nf.run(job, VP)
    elif mode == "bump":
        import bump_local
        make_body_silent(job)
        bump_local.run(job, VP)
    else:
        segdir = parts if parts is not None else job / "_work" / "segs"
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:     # assemble.py écrit seg_cfr/, concat.txt, final/ dans son dossier courant
            subprocess.run([sys.executable, str(VP / "assemble.py"), str(job), str(segdir.resolve()), str(out.resolve())],
                           cwd=tmp, check=True)
        return
    shutil.copy(job / f"{job.name}.mp4", out)


def make_body_silent(job: Path) -> None:
    """Mode bump : corps muet = segments recalés à 30 fps puis concaténés (comme bump_local_nf)."""
    segs = json.loads((job / "segments.json").read_text(encoding="utf-8"))
    work = job / "_work"; segdir = work / "segs"; tmp = work / "seg_cfr"; tmp.mkdir(parents=True, exist_ok=True)
    lines = []
    for k, s in enumerate(segs):
        dst = tmp / f"c{k}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(segdir / f"seg{k}.mp4"), "-vf",
                        "fps=30,tpad=stop_mode=clone:stop_duration=2", "-t", f"{s['t1'] - s['t0']:.3f}", "-c:v", "libx264",
                        "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(dst)], check=True)
        lines.append(f"file '{dst.resolve().as_posix()}'")
    (work / "concat_body.txt").write_text("\n".join(lines), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(work / "concat_body.txt"),
                    "-c", "copy", str(job / "body_silent.mp4")], check=True)
    facade_slider(job, job / "body_silent.mp4", segs[-1]["t1"])


SLIDE_HOLD, SLIDE_X = 4.5, 0.7          # durée d'un rendu à l'écran, durée du glissement (s)


def facade_slider(job: Path, video: Path, total: float) -> None:
    """Rendus 3D qui défilent à la place de la façade fixe (jobs/<id>/facades/*.png|jpg, dans l'ordre des noms) :
    glissement vers la gauche toutes les SLIDE_HOLD s, léger zoom lent sur chaque image, en boucle jusqu'à la fin."""
    imgs = sorted(p for p in (job / "facades").glob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg")) \
        if (job / "facades").is_dir() else []
    if len(imgs) < 2:
        return
    meta = json.loads((job / "meta.json").read_text(encoding="utf-8"))
    h = int(round(1080 * meta.get("facade_ratio", 0.5625)))
    n = int(total // (SLIDE_HOLD - SLIDE_X)) + 2               # assez d'images pour couvrir le corps
    seq = [imgs[k % len(imgs)] for k in range(n)]
    d = SLIDE_HOLD + SLIDE_X
    inputs, fc = [], []
    for k, p in enumerate(seq):
        inputs += ["-loop", "1", "-framerate", "30", "-t", f"{d:.3f}", "-i", str(p)]
        fc.append(f"[{k}:v]scale=1188:{int(h * 1.1)}:force_original_aspect_ratio=increase,crop=1188:{int(h * 1.1)},"
                  f"zoompan=z='min(1+0.0009*on,1.1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x{h}:fps=30,"
                  f"setsar=1,format=yuv420p[i{k}]")
    last = "i0"
    for k in range(1, n):
        off = k * SLIDE_HOLD
        fc.append(f"[{last}][i{k}]xfade=transition=slideleft:duration={SLIDE_X}:offset={off:.3f}[x{k}]")
        last = f"x{k}"
    tmp = video.with_name("facades.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(fc), "-map", f"[{last}]",
                    "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                    str(tmp)], check=True)
    out = video.with_name("body_slider.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(tmp), "-filter_complex",
                    "[0:v][1:v]overlay=0:0:eof_action=pass[v]", "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(out)], check=True)
    out.replace(video)


def local(job: Path, out: Path) -> None:
    """Rendu complet sur une seule machine (PC de Tao ou secours)."""
    p = plan(job)
    parts = job / "_work" / "parts"; parts.mkdir(parents=True, exist_ok=True)

    def one(item):
        dst = parts / f"{item['part']}.mp4"
        if dst.exists():
            return
        env = dict(os.environ, JOB=str(job), SEG=item["seg"])
        subprocess.run(["manimgx", "render", item["scene"], item["cls"], "-r", "1080x1920", "--fps", "30", "--preset",
                        "veryfast", "--crf", "18", "-o", str(dst)], cwd=VP, env=env, check=True)
    with ThreadPoolExecutor(2) as ex:                 # 2 rendus simultanés maximum (RAM)
        list(ex.map(one, p["include"]))
    build(job, parts, out)


if __name__ == "__main__":
    cmd, job = sys.argv[1], Path(sys.argv[2]).resolve()
    if cmd == "plan":
        print(json.dumps(plan(job), ensure_ascii=False))
    elif cmd == "build":
        build(job, Path(sys.argv[3]).resolve(), Path(sys.argv[4]).resolve())
    elif cmd == "local":
        local(job, Path(sys.argv[3]).resolve())
    else:
        sys.exit(__doc__)
