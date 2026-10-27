"""Rendu local hook / estimation / CTA + corps (sans intro ni phrase catalogue) + bande basse + filigranes.
Appelé par run_local.py quand le job contient bump.json."""
import json, os, shutil, subprocess, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

SCENES = {"hook": "HookScene", "estim": "EstimScene", "cta": "CtaScene"}
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30",
       "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2"]
BAND_H = 190


def ff(*a, cwd=None):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, a)], check=True, cwd=cwd)


def build_body(job: Path, B, work: Path, VP: Path) -> Path:
    """corps = silent_all (visite v4) + sous-titres remontés + bande basse + voix (+ musique), coupé entre cut et end."""
    cut, end = B["body_cut"], B["body_end"]; D = end - cut
    shutil.copy(job / "subs_body.ass", work / "subs.ass")
    shutil.copytree(VP / "fonts", work / "fonts", dirs_exist_ok=True)
    out = work / "body.mp4"
    music = job / "music.mp3"
    fc = (f"[0:v]fps=30,subtitles=subs.ass:fontsdir=fonts[s];[s][2:v]overlay=0:{1920 - BAND_H}[o];"
          f"[o]trim=start={cut}:end={end},setpts=PTS-STARTPTS[v];")
    inputs = ["-i", job / "body_silent.mp4", "-i", job / "voice_mix.m4a", "-i", job / "band_bottom.png"]
    if music.exists():       # musique de fond (Mixkit « Pop Two »), baisse automatique sous la voix
        inputs += ["-i", music]
        fc += (f"[1:a]atrim=start={cut}:end={end},asetpts=PTS-STARTPTS,asplit[v1][v2];"
               f"[3:a]atrim=0:{D:.3f},loudnorm=I=-24:TP=-2:LRA=7,afade=t=in:d=1.5,afade=t=out:st={D - 0.6:.3f}:d=0.6[m];"
               f"[m][v2]sidechaincompress=threshold=0.03:ratio=5:attack=30:release=500[md];"
               f"[v1][md]amix=inputs=2:normalize=0:weights='1 1',loudnorm=I=-17:TP=-1.5,afade=t=out:st={D - 0.1:.3f}:d=0.1[a]")
    else:
        fc += f"[1:a]atrim=start={cut}:end={end},asetpts=PTS-STARTPTS,afade=t=out:st={D - 0.1:.3f}:d=0.1[a]"
    ff(*inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", *ENC, out, cwd=work)
    return out


def run(job: Path, VP: Path):
    B = json.loads((job / "bump.json").read_text(encoding="utf-8"))
    work = job / "_work"; work.mkdir(exist_ok=True)
    t0 = time.time()

    def render(part):
        out = work / f"{part}_raw.mp4"
        if out.exists():
            return
        env = dict(os.environ, JOB=str(job))
        subprocess.run(["manimgx", "render", "scene_bumpers.py", SCENES[part], "-r", "1080x1920", "--fps", "30",
                        "--preset", "veryfast", "--crf", "18", "-o", str(out)], cwd=VP, env=env, check=True)
        print(f"{part} ok ({time.time()-t0:.0f}s)", flush=True)
    with ThreadPoolExecutor(2) as ex:
        list(ex.map(render, SCENES))
    parts = {}
    for part in SCENES:
        total = B[part]["total"]; dst = work / f"{part}.mp4"
        ff("-i", work / f"{part}_raw.mp4", "-i", job / f"{part}.m4a",
           "-vf", "fps=30,tpad=stop_mode=clone:stop_duration=3", "-af", "apad,loudnorm=I=-17:TP=-1.5:LRA=7" if part == "cta" else "anull",
           "-t", f"{total:.3f}", *ENC, dst)
        parts[part] = dst
    parts["body"] = build_body(job, B, work, VP)
    print(f"corps ok ({time.time()-t0:.0f}s)", flush=True)
    order = ["hook", "body", "estim", "cta"]
    lst = work / "concat_final.txt"
    lst.write_text("\n".join(f"file '{parts[p].resolve().as_posix()}'" for p in order), encoding="utf-8")
    mid = work / "mid.mp4"
    ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", mid)

    # ---- marque : filigrane mosaïque, logo mobile, adresse du site (zone sûre) ----
    hook_t = B["hook"]["total"]; body_t = B["body_end"] - B["body_cut"]
    t_badge0 = B["hook"]["cues"]["dot"] + 0.2
    t_badge1 = hook_t + body_t + B["estim"]["total"]
    out = job / f"{job.name}.mp4"
    # filigrane : mosaïque discrète + 2 logos semi-transparents qui se promènent en continu sur tout l'écran, du début à la fin
    fc = ("[2:v]format=rgba,scale=390:-1,colorchannelmixer=aa=0.62[w1];"
          "[3:v]format=rgba,scale=390:-1,colorchannelmixer=aa=0.62[w2];"
          "[0:v][1:v]overlay=0:0[a];"
          "[a][w1]overlay=x='(W-w)*(0.5+0.5*sin(0.53*t))':y='(H-h)*(0.5+0.5*sin(0.37*t+1.1))'[b];"
          "[b][w2]overlay=x='(W-w)*(0.5+0.5*sin(0.41*t+2.6))':y='(H-h)*(0.5+0.5*sin(0.29*t+4.0))'[c];"
          f"[c][5:v]overlay=28:524:enable='between(t,{t_badge0:.3f},{t_badge1:.3f})'[v]")
    ff("-i", mid, "-i", job / "wm_tile.png", "-i", job / "wm_logo.png", "-i", job / "wm_logo.png",
       "-i", job / "wm_logo.png", "-i", job / "badge_url.png", "-filter_complex", fc, "-map", "[v]", "-map", "0:a",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "copy",
       "-metadata", "comment=© WooPlans - wooplans.com", "-metadata", "copyright=© WooPlans", out)
    print(f"TERMINE {out} en {time.time()-t0:.0f}s", flush=True)
