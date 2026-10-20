"""Impose la vignette comme PREMIER FRAME d'une vidéo existante (3 images ≈ 0,12 s), audio inchangé :
les plateformes qui prennent le premier frame comme vignette (YouTube Shorts, TikTok) affichent la bonne image.
  python tools/add_cover_frame.py video.mp4 vignette.jpg sortie.mp4
"""
import subprocess
import sys

video, cover, out = sys.argv[1:4]
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-loop", "1", "-t", "1", "-i", cover,
                "-filter_complex", "[1:v]scale=1080:1920,setsar=1[c];[0:v][c]overlay=0:0:enable='lt(t,0.12)':shortest=0[v]",
                "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-c:a", "copy", "-movflags", "+faststart", out], check=True)
print("OK", out)
