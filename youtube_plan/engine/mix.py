import sys, subprocess, math, wave, random, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from common import D, ORDER, FPS, A, V, OUTDIR
import seq_intro, seq_chiffres, seq_visite, seq_visite2, seq_invit, seq_rendus, seq_catalogue, seq_terrain, seq_devis, seq_fin
FR = {k: int(round(D[k] * FPS)) for k in ORDER}; FR['jingle'] = 120
OFF = {}; acc = 0
for k in ORDER: OFF[k] = acc / 30.0; acc += FR[k]
TOT = acc / 30.0
print('TOT', TOT, OFF)
SR = 48000
buf = np.zeros(int(TOT * SR) + SR)
rnd = np.random.RandomState(7)
def put(t, y, g):
    i = int(t * SR); n = min(len(y), len(buf) - i)
    if i >= 0 and n > 0: buf[i:i + n] += y[:n] * g
def pop(g=0.5):
    n = int(0.12 * SR); x = np.arange(n) / SR
    f = 900 - 5000 * x; ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-x * 38) * g
def click(g=0.6):
    n = int(0.09 * SR); x = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1400 * x) * np.exp(-x * 70) + rnd.randn(n) * np.exp(-x * 150) * 0.4) * g
def whoosh(d=0.7, g=0.10):
    n = int(d * SR); x = np.arange(n) / SR
    noise = rnd.randn(n); out = np.zeros(n); y = 0
    for i in range(n):
        a = 0.008 + 0.05 * (i / n); y += a * (noise[i] - y); out[i] = y
    env = np.sin(np.pi * x / d) ** 3
    return out * env * g * 3
P = pop(0.32); C = click(0.35); Wh = whoosh()
def at(seq, ts, y, g=1.0):
    for t in ts: put(OFF[seq] + t, y, g)
Ti = seq_intro
at('intro', [Ti.T['chamb1'], Ti.T['cine1'], Ti.T['gar1'], Ti.T['plan'], Ti.T['angles'], Ti.T['terrain'], Ti.T['budget']] + [c[2] - 0.1 for c in Ti.CHIPS], P, 0.45); at('intro', [Ti.T_SUB - 0.2], P, 0.5); at('intro', [Ti.T_SUB + 1.3], C, 0.6); at('intro', [D['intro'] - 1.9], Wh, 0.8)
at('chiffres', [seq_chiffres.T149 - 0.5, seq_chiffres.TNIV - 1.2, seq_chiffres.TSEIZE - 1.0], P, 0.4)
at('visite', seq_visite.ARR, P, 0.35); at('visite2', seq_visite2.ARR, P, 0.35)
at('invit', [seq_invit.TCOM - 0.3, seq_invit.TSHARE - 0.3, seq_invit.TAIDE - 0.2], P, 0.5); at('invit', [seq_invit.TAIDE + 1.3], C, 0.6)
at('rendus', seq_rendus.BOUNDS[1:-1], Wh, 0.55)
at('catalogue', [s[0] for s in seq_catalogue.STEPS], P, 0.45); at('catalogue', [5.6, 32.0], Wh, 0.7); at('catalogue', [32.3], P, 0.6)
at('terrain', [seq_terrain.T_SEIZE, seq_terrain.T_TREIZE, seq_terrain.T_150, seq_terrain.T_DIX, seq_terrain.T_VINGT, seq_terrain.T_C1 - 0.2, seq_terrain.T_ROUTE2], P, 0.45)
at('devis', [seq_devis.T_PAYS - 0.2, seq_devis.T_TERR - 0.2, seq_devis.T_TECH - 0.2, seq_devis.T_ENTRE] + [r[2] for r in seq_devis.GO_ROWS + seq_devis.FIN_ROWS], P, 0.45)
at('fin', [seq_fin.T_POUCE - 0.1, seq_fin.T_ABO - 0.2, seq_fin.T_AUTRE - 0.25], P, 0.5); at('fin', [seq_fin.T_ABO - 0.2 + 0.8], C, 0.6)
buf = np.clip(buf, -1, 1)
w = wave.open(OUTDIR + '/sfx.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((buf * 32767).astype('<i2').tobytes()); w.close()
md = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'music') + '/'
mu = {k: glob.glob(md + k + '_*.mp3')[0] for k in 'BCD'}
ins = []; fl = []; vlab = []
seqs = [k for k in ORDER if k != 'jingle']
for k in seqs: ins += ['-i', V + f'{k}.wav']
for i, k in enumerate(seqs):
    ms = int(OFF[k] * 1000); fl.append(f'[{i}:a]aformat=sample_rates=48000:channel_layouts=mono,adelay={ms}|{ms}[v{i}]'); vlab.append(f'[v{i}]')
n = len(vlab)
ins += ['-i', A + 'jingle.mp4']; ji = n; ms = int(OFF['jingle'] * 1000)
fl.append(f'[{ji}:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.8,adelay={ms}|{ms}[jg]'); vlab.append('[jg]')
ins += ['-i', mu['C'], '-i', mu['B'], '-i', mu['D'], '-i', mu['C'], '-i', OUTDIR + '/sfx.wav']
ci, bi, di, c2i, si = n + 1, n + 2, n + 3, n + 4, n + 5
fl.append(f'{"".join(vlab)}amix=inputs={len(vlab)}:normalize=0,aformat=channel_layouts=mono,asplit=2[vo][vsc]')
c2s = 433; c2d = TOT - c2s + 1
fl.append(f'[{ci}:a]aformat=sample_rates=48000:channel_layouts=mono,atrim=0:140,afade=out:st=134:d=6,asetpts=PTS-STARTPTS[mc]')
fl.append(f'[{bi}:a]aformat=sample_rates=48000:channel_layouts=mono,atrim=0:186,afade=in:st=0:d=6,afade=out:st=180:d=6,adelay=134000|134000[mb]')
fl.append(f'[{di}:a]aformat=sample_rates=48000:channel_layouts=mono,atrim=0:125.4,afade=in:st=0:d=6,afade=out:st=118:d=7,adelay=314000|314000[md]')
fl.append(f'[{c2i}:a]aformat=sample_rates=48000:channel_layouts=mono,atrim=40:{40 + c2d:.1f},asetpts=PTS-STARTPTS,afade=in:st=0:d=6,afade=out:st={c2d - 3:.1f}:d=3,adelay={c2s * 1000}|{c2s * 1000}[mc2]')
fl.append('[mc][mb][md][mc2]amix=inputs=4:normalize=0,highpass=f=200,lowpass=f=4200,equalizer=f=2500:t=q:w=1:g=-6,volume=0.15[mus]')
fl.append('[mus][vsc]sidechaincompress=threshold=0.015:ratio=12:attack=15:release=450:makeup=1[musd]')
fl.append(f'[{si}:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.7[sx]')
fl.append('[vo][musd][sx]amix=inputs=3:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=9,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[a]')
cmd = ['ffmpeg', '-y', '-loglevel', 'error'] + ins + ['-filter_complex', ';'.join(fl), '-map', '[a]', '-t', f'{TOT:.3f}', '-c:a', 'aac', '-b:a', '192k', OUTDIR + '/audio_mix.m4a']
subprocess.run(cmd, check=True)
print('audio ok')
