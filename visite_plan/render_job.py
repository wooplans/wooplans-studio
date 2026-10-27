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
