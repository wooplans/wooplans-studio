"""Assemble la vidéo : concat des chunks (ORDER) + jingle + segment catalogue (copie), muxe l'audio mixé, planche-contact.
  YT_JOB=<job> YT_OUT=<dossier chunks> python assemble.py <sortie.mp4>"""
import sys, os, subprocess, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import D, FPS, ORDER, OUTDIR, A
from PIL import Image, ImageDraw
out = os.path.abspath(sys.argv[1])
def sh(*c):
    subprocess.run(c, check=True)
lst = []
for k in ORDER:
    if k == 'jingle' or k == 'catalogue':
        src = A + ('jingle.mp4' if k == 'jingle' else 'catalogue_seg.mp4')
        dst = f'{OUTDIR}/{k}_video.mp4'
        sh('ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-an', '-c:v', 'copy', dst)
        lst.append(dst)
    else:
        n = int(round(D[k] * FPS)); fs = sorted(glob.glob(f'{OUTDIR}/{k}_[0-9]*.mp4'))
        fs = [f for f in fs if not f.endswith('.part.mp4')]
        assert len(fs) == -(-n // 240), (k, len(fs), n)
        lst += fs
open(f'{OUTDIR}/concat.txt', 'w').write(''.join(f"file '{os.path.abspath(f)}'\n" for f in lst))
sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{OUTDIR}/concat.txt', '-c', 'copy', f'{OUTDIR}/video_only.mp4')
sh('ffmpeg', '-y', '-loglevel', 'error', '-i', f'{OUTDIR}/video_only.mp4', '-i', f'{OUTDIR}/audio_mix.m4a', '-map', '0:v', '-map', '1:a', '-c', 'copy', '-movflags', '+faststart', '-shortest', out)
# planche-contact : 1 image / 8 s
fr = f'{OUTDIR}/sheet_frames'; os.makedirs(fr, exist_ok=True)
sh('ffmpeg', '-y', '-loglevel', 'error', '-i', out, '-vf', 'fps=1/8,scale=320:180', f'{fr}/f_%03d.png')
fs = sorted(glob.glob(fr + '/f_*.png')); cols = 6; rows = -(-len(fs) // cols)
sheet = Image.new('RGB', (cols * 320, rows * 200), (20, 20, 20)); d = ImageDraw.Draw(sheet)
for i, f in enumerate(fs):
    x, y = (i % cols) * 320, (i // cols) * 200
    sheet.paste(Image.open(f), (x, y)); t = i * 8
    d.text((x + 4, y + 182), f'{t // 60}:{t % 60:02d}', fill=(255, 255, 255))
sheet.save(os.path.splitext(out)[0] + '_planche.jpg', quality=82)
print('ok', out)
