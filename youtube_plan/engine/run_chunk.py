"""Rend les images [f0,f1) d'une séquence -> $YT_OUT/<seq>_<f0>.mp4.  Usage: YT_JOB=<job> python run_chunk.py <seq> <f0> <f1>"""
import sys, os, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from PIL import Image
seq, f0, f1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
m = importlib.import_module('seq_' + seq)
n = int(round(D[seq] * FPS))
f1 = min(f1, n)
OUT = f'{OUTDIR}/{seq}_{f0:05d}.mp4'
wr = Writer(OUT + '.part.mp4')
for i in range(f0, f1):
    t = i / FPS
    if seq == 'intro' and i < 5 and os.path.exists(A + 'thumb_1920.png'):
        im = Image.open(A + 'thumb_1920.png').convert('RGB')
    else:
        fr = m.frame(t)
        if seq == 'intro':
            a_ = clamp((t - 8.9) / 0.5)
            im = fr if a_ <= 0 else finish(fr, OFF[seq] + t, True, a_)
        else:
            im = finish(fr, OFF[seq] + t)
    wr.write(im)
wr.close()
os.rename(OUT + '.part.mp4', OUT)
print(seq, f0, f1, 'ok of', n)
