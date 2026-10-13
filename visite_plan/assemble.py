"""Assemble les segments rendus (CFR 30 fps, calés sur la timeline nominale) puis brûle sous-titres + voix.
usage: python assemble.py jobs/<id> dossier_segments sortie.mp4"""
import json, subprocess, sys
from pathlib import Path
job, segdir, out = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
segs = json.loads((job / "segments.json").read_text(encoding="utf-8"))
tmp = Path("seg_cfr"); tmp.mkdir(exist_ok=True)
lst = []
for k, s in enumerate(segs):
    src = segdir / f"seg{k}.mp4"; dst = tmp / f"c{k}.mp4"
    d = s["t1"] - s["t0"]
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(src),"-vf","fps=30,tpad=stop_mode=clone:stop_duration=2","-t",f"{d:.3f}",
                    "-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-an",str(dst)], check=True)
    lst.append(f"file '{dst.resolve()}'")
Path("concat.txt").write_text("\n".join(lst), encoding="utf-8")
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i","concat.txt","-c","copy","silent_all.mp4"], check=True)
subprocess.run([sys.executable, str(Path(__file__).parent / "build_final.py"), "burn", "silent_all.mp4", out, str(job)], check=True)
